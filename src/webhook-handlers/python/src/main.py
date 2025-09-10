"""
GitHub Webhook Security Server - Python FastAPI Implementation
エス・エー・エス株式会社 GitHub Webhook セキュリティサーバー
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
import re
import signal
import sys
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import httpx
import orjson
import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.security import HTTPBearer
from netaddr import IPAddress, IPNetwork
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field, ValidationError, validator
from pydantic_settings import BaseSettings
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware


# ===========================
# Configuration & Settings
# ===========================

class SecuritySettings(BaseSettings):
    """セキュリティ設定"""
    webhook_secret: str = Field(..., env="WEBHOOK_SECRET")
    allowed_ips: List[str] = Field(
        default_factory=lambda: [
            "140.82.112.0/20", "143.55.64.0/20", "185.199.108.0/22",
            "192.30.252.0/22", "20.201.28.151/32", "20.205.243.166/32"
        ],
        env="ALLOWED_IPS"
    )
    rate_limit_global: int = Field(default=1000, env="RATE_LIMIT_GLOBAL")
    rate_limit_per_ip: int = Field(default=60, env="RATE_LIMIT_PER_IP")
    rate_limit_per_hook: int = Field(default=120, env="RATE_LIMIT_PER_HOOK")
    rate_limit_per_repo: int = Field(default=100, env="RATE_LIMIT_PER_REPO")
    max_payload_size_mb: int = Field(default=10, env="MAX_PAYLOAD_SIZE_MB")
    ip_validation_strict: bool = Field(default=True, env="IP_VALIDATION_STRICT")
    geo_restrictions: List[str] = Field(default=["JP", "US"], env="GEO_RESTRICTIONS")

    class Config:
        env_file = ".env"
        env_prefix = "WEBHOOK_SECURITY_"


class AppSettings(BaseSettings):
    """アプリケーション設定"""
    app_name: str = "GitHub Webhook Security Server"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    log_level: str = Field(default="info", env="LOG_LEVEL")
    
    # Feature flags
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    enable_cors: bool = Field(default=False, env="ENABLE_CORS")
    enable_docs: bool = Field(default=False, env="ENABLE_DOCS")
    enable_compression: bool = Field(default=True, env="ENABLE_COMPRESSION")
    
    # External services
    elasticsearch_url: Optional[str] = Field(default=None, env="ELASTICSEARCH_URL")
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")

    class Config:
        env_file = ".env"


# ===========================
# Pydantic Models
# ===========================

class GitHubRepository(BaseModel):
    """GitHub リポジトリ"""
    id: int
    name: str
    full_name: str
    private: bool
    html_url: str
    description: Optional[str] = None
    default_branch: str


class GitHubUser(BaseModel):
    """GitHub ユーザー"""
    id: int
    login: str
    avatar_url: str
    html_url: str
    type: str = "User"


class GitHubCommit(BaseModel):
    """GitHub コミット"""
    id: str = Field(..., regex=r'^[a-f0-9]{40}$')
    message: str
    timestamp: datetime
    author: Dict[str, str]
    added: List[str] = Field(default_factory=list)
    removed: List[str] = Field(default_factory=list)
    modified: List[str] = Field(default_factory=list)


class PushEventPayload(BaseModel):
    """Push イベント ペイロード"""
    ref: str
    before: str = Field(..., regex=r'^[a-f0-9]{40}$')
    after: str = Field(..., regex=r'^[a-f0-9]{40}$')
    commits: List[GitHubCommit]
    repository: GitHubRepository
    pusher: Dict[str, str]
    sender: GitHubUser

    @validator('ref')
    def validate_ref(cls, v):
        if not v.startswith('refs/'):
            raise ValueError('Invalid ref format')
        return v


class PullRequestPayload(BaseModel):
    """Pull Request イベント ペイロード"""
    action: str
    number: int
    pull_request: Dict[str, Any]
    repository: GitHubRepository
    sender: GitHubUser

    @validator('action')
    def validate_action(cls, v):
        valid_actions = [
            'opened', 'closed', 'reopened', 'edited', 'synchronize',
            'assigned', 'unassigned', 'labeled', 'unlabeled'
        ]
        if v not in valid_actions:
            raise ValueError(f'Invalid action: {v}')
        return v


class WebhookResponse(BaseModel):
    """Webhook レスポンス"""
    status: str = "success"
    delivery_id: str
    event_type: Optional[str] = None
    processing_time_ms: Optional[int] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """エラー レスポンス"""
    error: str
    message: str
    details: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    request_id: str
    delivery_id: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """ヘルスチェック レスポンス"""
    status: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    version: str
    service: str
    uptime_seconds: int
    dependencies: Optional[Dict[str, str]] = None


# ===========================
# Security Validator
# ===========================

class WebhookSecurityValidator:
    """Webhook セキュリティ検証クラス"""
    
    def __init__(self, security_settings: SecuritySettings):
        self.settings = security_settings
        self.allowed_networks = [
            IPNetwork(ip) for ip in security_settings.allowed_ips
        ]
        self.logger = structlog.get_logger(__name__)
        
        # 機密データ検出パターン
        self.sensitive_patterns = [
            re.compile(r'password\s*[=:]\s*["\']([^"\']+)["\']', re.IGNORECASE),
            re.compile(r'api[_-]?key\s*[=:]\s*["\']([^"\']+)["\']', re.IGNORECASE),
            re.compile(r'secret\s*[=:]\s*["\']([^"\']+)["\']', re.IGNORECASE),
            re.compile(r'token\s*[=:]\s*["\']([^"\']+)["\']', re.IGNORECASE),
            re.compile(r'-----BEGIN [A-Z ]+PRIVATE KEY-----', re.IGNORECASE),
            re.compile(r'akia[0-9a-z]{16}', re.IGNORECASE),  # AWS Access Key
            re.compile(r'\d{3}-?\d{4}-?\d{4}'),  # Phone numbers
        ]

    async def verify_signature(self, payload: bytes, signature: str) -> bool:
        """GitHub Webhook 署名検証"""
        try:
            if not signature or not signature.startswith('sha256='):
                return False
            
            expected_signature = hmac.new(
                self.settings.webhook_secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            expected = f"sha256={expected_signature}"
            
            # タイミング攻撃防止のための定数時間比較
            return hmac.compare_digest(signature, expected)
            
        except Exception as e:
            self.logger.error("signature_verification_failed", error=str(e))
            return False

    async def verify_ip_address(self, client_ip: str) -> bool:
        """IP アドレス検証"""
        try:
            # 開発環境での特別処理
            if not self.settings.ip_validation_strict and client_ip in ['127.0.0.1', '::1']:
                return True
            
            ip_addr = IPAddress(client_ip)
            
            for network in self.allowed_networks:
                if ip_addr in network:
                    return True
                    
            return False
            
        except Exception as e:
            self.logger.error("ip_verification_failed", error=str(e), ip=client_ip)
            return False

    async def validate_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """必須ヘッダー検証"""
        required_headers = [
            'x-github-delivery',
            'x-github-event',
            'x-hub-signature-256',
            'user-agent'
        ]
        
        errors = []
        for header in required_headers:
            if header not in headers:
                errors.append(f"Missing required header: {header}")
        
        # ヘッダー形式検証
        if 'x-github-delivery' in headers:
            delivery_id = headers['x-github-delivery']
            if not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', delivery_id):
                errors.append("Invalid x-github-delivery format")
        
        if 'x-hub-signature-256' in headers:
            signature = headers['x-hub-signature-256']
            if not re.match(r'^sha256=[a-f0-9]{64}$', signature):
                errors.append("Invalid x-hub-signature-256 format")
        
        if 'user-agent' in headers:
            user_agent = headers['user-agent']
            if not re.match(r'^GitHub-Hookshot/[a-f0-9]+$', user_agent):
                errors.append("Invalid user-agent format")
        
        if errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"errors": errors}
            )
        
        return headers

    async def detect_sensitive_data(self, content: str) -> List[str]:
        """機密データ検出"""
        detected_patterns = []
        
        for i, pattern in enumerate(self.sensitive_patterns):
            if pattern.search(content):
                detected_patterns.append(f"pattern_{i+1}")
        
        return detected_patterns

    async def sanitize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """ペイロード サニタイゼーション"""
        def sanitize_string(text: str) -> str:
            if not isinstance(text, str):
                return text
            
            # 基本的なサニタイゼーション
            sanitized = text
            sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
            sanitized = re.sub(r'<[^>]*>', '', sanitized)
            sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
            sanitized = re.sub(r'on\w+\s*=', '', sanitized, flags=re.IGNORECASE)
            sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)
            
            return sanitized.strip()
        
        def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
            sanitized = {}
            for key, value in data.items():
                if isinstance(value, str):
                    sanitized[key] = sanitize_string(value)
                elif isinstance(value, dict):
                    sanitized[key] = sanitize_dict(value)
                elif isinstance(value, list):
                    sanitized[key] = [
                        sanitize_dict(item) if isinstance(item, dict) else
                        sanitize_string(item) if isinstance(item, str) else item
                        for item in value
                    ]
                else:
                    sanitized[key] = value
            return sanitized
        
        return sanitize_dict(payload)


# ===========================
# Logging Setup
# ===========================

def setup_logging(log_level: str = "info"):
    """構造化ログ設定"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(serializer=orjson.dumps)
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )


# ===========================
# Metrics & Monitoring
# ===========================

class MetricsCollector:
    """メトリクス収集クラス"""
    
    def __init__(self):
        self.instrumentator = Instrumentator()
        
    def setup_metrics(self, app: FastAPI):
        """メトリクス設定"""
        self.instrumentator.instrument(app).expose(app, endpoint="/metrics")


# ===========================
# Middleware
# ===========================

class SecurityMiddleware(BaseHTTPMiddleware):
    """セキュリティ ミドルウェア"""
    
    def __init__(self, app, validator: WebhookSecurityValidator):
        super().__init__(app)
        self.validator = validator
        self.logger = structlog.get_logger(__name__)

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        # リクエストID追加
        request.state.request_id = request_id
        
        try:
            response = await call_next(request)
            
            # セキュリティヘッダー追加
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            
            # 処理時間ログ
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            self.logger.error("middleware_error", error=str(e), request_id=request_id)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )


# ===========================
# Application Lifecycle
# ===========================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーション ライフサイクル管理"""
    logger = structlog.get_logger(__name__)
    
    # Startup
    logger.info("application_starting", version=app_settings.app_version)
    
    # Initialize services
    if app_settings.redis_url:
        logger.info("connecting_to_redis", url=app_settings.redis_url)
    
    if app_settings.elasticsearch_url:
        logger.info("connecting_to_elasticsearch", url=app_settings.elasticsearch_url)
    
    logger.info("application_started")
    
    yield
    
    # Shutdown
    logger.info("application_shutting_down")
    
    # Cleanup resources
    logger.info("application_shutdown_complete")


# ===========================
# Application Setup
# ===========================

# 設定読み込み
app_settings = AppSettings()
security_settings = SecuritySettings()

# ログ設定
setup_logging(app_settings.log_level)
logger = structlog.get_logger(__name__)

# セキュリティ検証
validator = WebhookSecurityValidator(security_settings)

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)

# FastAPI アプリケーション作成
app = FastAPI(
    title=app_settings.app_name,
    version=app_settings.app_version,
    description="エンタープライズ級GitHub Webhookセキュリティサーバー",
    docs_url="/docs" if app_settings.enable_docs else None,
    redoc_url="/redoc" if app_settings.enable_docs else None,
    lifespan=lifespan
)

# Rate Limiter設定
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ミドルウェア設定
app.add_middleware(SecurityMiddleware, validator=validator)

# Trusted Hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if app_settings.environment == "development" else [
        "webhook.sas-com.internal",
        "*.sas-com.com"
    ]
)

# CORS設定
if app_settings.enable_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://*.sas-com.com"] if app_settings.environment == "production" else ["*"],
        allow_credentials=False,
        allow_methods=["POST", "GET"],
        allow_headers=["*"],
    )

# メトリクス設定
if app_settings.enable_metrics:
    metrics_collector = MetricsCollector()
    metrics_collector.setup_metrics(app)

# 起動時刻記録
startup_time = datetime.utcnow()


# ===========================
# API Endpoints
# ===========================

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """ヘルスチェック エンドポイント"""
    uptime = int((datetime.utcnow() - startup_time).total_seconds())
    
    return HealthCheckResponse(
        status="healthy",
        version=app_settings.app_version,
        service=app_settings.app_name,
        uptime_seconds=uptime,
        dependencies={
            "redis": "healthy" if app_settings.redis_url else "not_configured",
            "elasticsearch": "healthy" if app_settings.elasticsearch_url else "not_configured",
            "database": "healthy" if app_settings.database_url else "not_configured"
        }
    )


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Prometheus メトリクス エンドポイント"""
    if not app_settings.enable_metrics:
        raise HTTPException(status_code=404, detail="Metrics not enabled")
    
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/config")
async def get_config():
    """設定情報取得 (非機密情報のみ)"""
    return {
        "version": app_settings.app_version,
        "environment": app_settings.environment,
        "features": {
            "metrics_enabled": app_settings.enable_metrics,
            "cors_enabled": app_settings.enable_cors,
            "docs_enabled": app_settings.enable_docs
        },
        "rate_limits": {
            "global": security_settings.rate_limit_global,
            "per_ip": security_settings.rate_limit_per_ip,
            "per_hook": security_settings.rate_limit_per_hook,
            "per_repository": security_settings.rate_limit_per_repo
        },
        "security": {
            "max_payload_size_mb": security_settings.max_payload_size_mb,
            "ip_validation_strict": security_settings.ip_validation_strict,
            "supported_events": [
                "push", "pull_request", "issues", "repository",
                "organization", "member", "team", "installation",
                "secret_scanning_alert", "code_scanning_alert", "dependabot_alert"
            ]
        }
    }


@app.post("/webhook/github")
@limiter.limit(f"{security_settings.rate_limit_per_ip}/minute")
async def github_webhook(request: Request):
    """GitHub Webhook 受信エンドポイント"""
    start_time = time.time()
    request_id = request.state.request_id
    
    # ヘッダー取得
    headers = dict(request.headers)
    delivery_id = headers.get('x-github-delivery')
    event_type = headers.get('x-github-event')
    signature = headers.get('x-hub-signature-256')
    user_agent = headers.get('user-agent')
    client_ip = request.client.host
    
    try:
        # 基本検証
        if not all([delivery_id, event_type, signature]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    error="MISSING_HEADERS",
                    message="Required headers are missing",
                    details="Missing one or more: X-GitHub-Delivery, X-GitHub-Event, X-Hub-Signature-256",
                    request_id=request_id,
                    delivery_id=delivery_id
                ).dict()
            )
        
        # ペイロード取得
        raw_body = await request.body()
        
        # ペイロードサイズチェック
        max_size = security_settings.max_payload_size_mb * 1024 * 1024
        if len(raw_body) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=ErrorResponse(
                    error="PAYLOAD_TOO_LARGE",
                    message="Request payload too large",
                    details=f"Maximum payload size is {security_settings.max_payload_size_mb}MB",
                    request_id=request_id,
                    delivery_id=delivery_id
                ).dict()
            )
        
        # ヘッダー検証
        await validator.validate_headers(headers)
        
        # 署名検証
        if not await validator.verify_signature(raw_body, signature):
            logger.error(
                "signature_verification_failed",
                delivery_id=delivery_id,
                client_ip=client_ip,
                event_type=event_type
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorResponse(
                    error="INVALID_SIGNATURE",
                    message="Invalid webhook signature",
                    details="HMAC-SHA256 signature verification failed",
                    request_id=request_id,
                    delivery_id=delivery_id
                ).dict()
            )
        
        # IP制限チェック
        if not await validator.verify_ip_address(client_ip):
            logger.error(
                "unauthorized_ip_access",
                delivery_id=delivery_id,
                client_ip=client_ip,
                event_type=event_type
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorResponse(
                    error="FORBIDDEN_IP",
                    message="Access denied: IP not allowed",
                    details="Request from unauthorized IP address",
                    request_id=request_id,
                    delivery_id=delivery_id
                ).dict()
            )
        
        # JSON解析
        try:
            payload = orjson.loads(raw_body)
        except orjson.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    error="INVALID_PAYLOAD",
                    message="Invalid JSON payload",
                    details=f"JSON decode error: {str(e)}",
                    request_id=request_id,
                    delivery_id=delivery_id
                ).dict()
            )
        
        # ペイロード検証（イベント別）
        try:
            if event_type == 'push':
                validated_payload = PushEventPayload(**payload)
            elif event_type == 'pull_request':
                validated_payload = PullRequestPayload(**payload)
            else:
                # 基本的な構造のみ検証
                validated_payload = payload
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    error="INVALID_PAYLOAD",
                    message="Payload validation failed",
                    details=str(e),
                    request_id=request_id,
                    delivery_id=delivery_id
                ).dict()
            )
        
        # 機密データ検出
        payload_str = raw_body.decode('utf-8')
        sensitive_patterns = await validator.detect_sensitive_data(payload_str)
        
        if sensitive_patterns:
            logger.warning(
                "sensitive_data_detected",
                delivery_id=delivery_id,
                client_ip=client_ip,
                event_type=event_type,
                patterns=sensitive_patterns
            )
        
        # ペイロードサニタイゼーション
        sanitized_payload = await validator.sanitize_payload(payload)
        
        # イベント処理
        await process_webhook_event(event_type, sanitized_payload, delivery_id, client_ip)
        
        # 成功ログ
        processing_time = int((time.time() - start_time) * 1000)
        logger.info(
            "webhook_processed_successfully",
            delivery_id=delivery_id,
            event_type=event_type,
            client_ip=client_ip,
            processing_time_ms=processing_time,
            payload_size=len(raw_body),
            sensitive_data_detected=bool(sensitive_patterns)
        )
        
        # レスポンス
        return WebhookResponse(
            delivery_id=delivery_id,
            event_type=event_type,
            processing_time_ms=processing_time,
            metadata={
                "repository": sanitized_payload.get("repository", {}).get("full_name"),
                "sender": sanitized_payload.get("sender", {}).get("login"),
                "action": sanitized_payload.get("action"),
                "security_checks_passed": True,
                "sensitive_data_detected": bool(sensitive_patterns)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(
            "webhook_processing_error",
            delivery_id=delivery_id,
            event_type=event_type,
            client_ip=client_ip,
            processing_time_ms=processing_time,
            error=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred",
                details=str(e),
                request_id=request_id,
                delivery_id=delivery_id
            ).dict()
        )


# ===========================
# Event Processing
# ===========================

async def process_webhook_event(
    event_type: str,
    payload: Dict[str, Any],
    delivery_id: str,
    client_ip: str
) -> None:
    """Webhook イベント処理"""
    
    logger.debug(
        "processing_webhook_event",
        event_type=event_type,
        delivery_id=delivery_id,
        repository=payload.get("repository", {}).get("full_name")
    )
    
    # イベント別処理
    if event_type == 'push':
        await handle_push_event(payload, delivery_id, client_ip)
    elif event_type == 'pull_request':
        await handle_pull_request_event(payload, delivery_id, client_ip)
    elif event_type == 'secret_scanning_alert':
        await handle_secret_scanning_event(payload, delivery_id, client_ip)
    elif event_type == 'code_scanning_alert':
        await handle_code_scanning_event(payload, delivery_id, client_ip)
    elif event_type == 'dependabot_alert':
        await handle_dependabot_event(payload, delivery_id, client_ip)
    else:
        logger.info(
            "unhandled_event_type",
            event_type=event_type,
            delivery_id=delivery_id
        )


async def handle_push_event(payload: Dict[str, Any], delivery_id: str, client_ip: str) -> None:
    """Push イベント処理"""
    repository = payload.get("repository", {})
    commits = payload.get("commits", [])
    
    logger.info(
        "processing_push_event",
        delivery_id=delivery_id,
        repository=repository.get("full_name"),
        commit_count=len(commits)
    )
    
    # セキュリティスキャン
    for commit in commits:
        if contains_sensitive_data(commit):
            logger.critical(
                "sensitive_data_in_commit",
                delivery_id=delivery_id,
                repository=repository.get("full_name"),
                commit_sha=commit.get("id"),
                commit_message=commit.get("message", "")[:100]
            )


async def handle_pull_request_event(payload: Dict[str, Any], delivery_id: str, client_ip: str) -> None:
    """Pull Request イベント処理"""
    action = payload.get("action")
    pull_request = payload.get("pull_request", {})
    repository = payload.get("repository", {})
    
    logger.info(
        "processing_pull_request_event",
        delivery_id=delivery_id,
        action=action,
        repository=repository.get("full_name"),
        pr_number=pull_request.get("number")
    )


async def handle_secret_scanning_event(payload: Dict[str, Any], delivery_id: str, client_ip: str) -> None:
    """Secret Scanning イベント処理"""
    alert = payload.get("alert", {})
    repository = payload.get("repository", {})
    
    logger.critical(
        "secret_scanning_alert",
        delivery_id=delivery_id,
        repository=repository.get("full_name"),
        secret_type=alert.get("secret_type"),
        alert_number=alert.get("number")
    )


async def handle_code_scanning_event(payload: Dict[str, Any], delivery_id: str, client_ip: str) -> None:
    """Code Scanning イベント処理"""
    alert = payload.get("alert", {})
    repository = payload.get("repository", {})
    
    logger.warning(
        "code_scanning_alert",
        delivery_id=delivery_id,
        repository=repository.get("full_name"),
        rule_id=alert.get("rule", {}).get("id"),
        severity=alert.get("rule", {}).get("severity")
    )


async def handle_dependabot_event(payload: Dict[str, Any], delivery_id: str, client_ip: str) -> None:
    """Dependabot イベント処理"""
    alert = payload.get("alert", {})
    repository = payload.get("repository", {})
    
    logger.warning(
        "dependabot_alert",
        delivery_id=delivery_id,
        repository=repository.get("full_name"),
        vulnerability=alert.get("security_advisory", {}).get("ghsa_id"),
        severity=alert.get("security_advisory", {}).get("severity")
    )


def contains_sensitive_data(commit: Dict[str, Any]) -> bool:
    """コミット内の機密データ検出"""
    sensitive_keywords = [
        'password', 'secret', 'key', 'token', 'credential',
        'aws_access_key', 'api_key', 'private_key'
    ]
    
    message = commit.get("message", "").lower()
    added_files = commit.get("added", [])
    modified_files = commit.get("modified", [])
    
    # コミットメッセージチェック
    if any(keyword in message for keyword in sensitive_keywords):
        return True
    
    # ファイル名チェック
    all_files = added_files + modified_files
    sensitive_files = ['.env', 'credentials', 'secrets', 'private_key']
    
    if any(any(sensitive in file.lower() for sensitive in sensitive_files) for file in all_files):
        return True
    
    return False


# ===========================
# Exception Handlers
# ===========================

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """カスタム HTTP 例外ハンドラー"""
    logger.error(
        "http_exception",
        status_code=exc.status_code,
        detail=exc.detail,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    return await http_exception_handler(request, exc)


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Validation エラーハンドラー"""
    logger.error(
        "validation_error",
        errors=exc.errors(),
        request_id=getattr(request.state, 'request_id', None)
    )
    
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="VALIDATION_ERROR",
            message="Request validation failed",
            details=str(exc),
            request_id=getattr(request.state, 'request_id', str(uuid.uuid4()))
        ).dict()
    )


# ===========================
# Graceful Shutdown
# ===========================

async def graceful_shutdown():
    """グレースフル シャットダウン"""
    logger.info("initiating_graceful_shutdown")
    
    # リソースクリーンアップ
    # (データベース接続、Redis接続等をクローズ)
    
    logger.info("graceful_shutdown_complete")


def setup_signal_handlers():
    """シグナル ハンドラー設定"""
    def signal_handler(signum, frame):
        logger.info("received_shutdown_signal", signal=signum)
        asyncio.create_task(graceful_shutdown())
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)


# ===========================
# Application Entry Point
# ===========================

if __name__ == "__main__":
    setup_signal_handlers()
    
    logger.info(
        "starting_github_webhook_security_server",
        version=app_settings.app_version,
        environment=app_settings.environment,
        host=app_settings.host,
        port=app_settings.port
    )
    
    uvicorn.run(
        "main:app",
        host=app_settings.host,
        port=app_settings.port,
        log_level=app_settings.log_level.lower(),
        reload=app_settings.environment == "development",
        workers=1 if app_settings.environment == "development" else 4,
        access_log=True,
        server_header=False,
        date_header=False,
    )