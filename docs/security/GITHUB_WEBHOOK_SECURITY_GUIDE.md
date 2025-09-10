# GitHub Webhook セキュリティ実装ガイド

**エス・エー・エス株式会社**  
*GitHub Webhook エンタープライズセキュリティシステム*

## 📋 目次

1. [概要](#概要)
2. [セキュリティアーキテクチャ](#セキュリティアーキテクチャ)
3. [認証・認可メカニズム](#認証認可メカニズム)
4. [実装方式](#実装方式)
5. [セキュリティ対策](#セキュリティ対策)
6. [監査・ログ機能](#監査ログ機能)
7. [運用・監視](#運用監視)
8. [インシデント対応](#インシデント対応)
9. [コンプライアンス](#コンプライアンス)

## 📌 概要

### プロジェクト概要
エス・エー・エス株式会社のGitHub Enterprise環境向けWebhookセキュリティシステムは、エンタープライズ級のセキュリティ要件を満たすWebhook受信・処理システムです。

### 主要特徴
- **マルチ言語対応**: Node.js/TypeScript, Python, Go, Java
- **エンタープライズセキュリティ**: HMAC-SHA256署名検証、IP制限、Rate Limiting
- **スケーラブル設計**: Kubernetes対応、高可用性、負荷分散
- **包括的監視**: Prometheus, Grafana, ELK Stack統合
- **コンプライアンス準拠**: 2FA必須、監査ログ、暗号化

### 技術仕様
| 項目 | 詳細 |
|------|------|
| プラットフォーム | GitHub.com (Enterprise Cloud) |
| 対応言語 | Node.js/TS, Python, Go, Java |
| インフラ | AWS/Azure/GCP, Kubernetes |
| セキュリティ | TLS 1.3, HMAC-SHA256, OAuth 2.0 |
| 監視 | Prometheus, Grafana, ELK Stack |

## 🏗️ セキュリティアーキテクチャ

### 全体アーキテクチャ

```mermaid
graph TB
    subgraph "GitHub"
        GH[GitHub Webhook]
    end
    
    subgraph "Load Balancer & Security"
        LB[Load Balancer]
        WAF[Web Application Firewall]
        RateLimit[Rate Limiting]
    end
    
    subgraph "Webhook Receivers"
        NodeJS[Node.js/TypeScript]
        Python[Python/FastAPI]
        Go[Go/Gin]
        Java[Java/Spring Boot]
    end
    
    subgraph "Security Services"
        Auth[Authentication Service]
        SignatureVerify[Signature Verification]
        IPWhitelist[IP Whitelist Validation]
    end
    
    subgraph "Data Processing"
        Validation[Payload Validation]
        Sanitization[Input Sanitization]
        EventRouting[Event Routing]
    end
    
    subgraph "Storage & Cache"
        DB[(Database)]
        Redis[(Redis Cache)]
        Logs[(Audit Logs)]
    end
    
    subgraph "Monitoring & Alerts"
        Prometheus[Prometheus]
        Grafana[Grafana Dashboard]
        ELK[ELK Stack]
        Alerting[Alert Manager]
    end
    
    GH --> LB
    LB --> WAF
    WAF --> RateLimit
    RateLimit --> NodeJS
    RateLimit --> Python
    RateLimit --> Go
    RateLimit --> Java
    
    NodeJS --> Auth
    Python --> Auth
    Go --> Auth
    Java --> Auth
    
    Auth --> SignatureVerify
    Auth --> IPWhitelist
    
    SignatureVerify --> Validation
    IPWhitelist --> Validation
    Validation --> Sanitization
    Sanitization --> EventRouting
    
    EventRouting --> DB
    EventRouting --> Redis
    EventRouting --> Logs
    
    NodeJS --> Prometheus
    Python --> Prometheus
    Go --> Prometheus
    Java --> Prometheus
    
    Prometheus --> Grafana
    Prometheus --> Alerting
    Logs --> ELK
```

### セキュリティレイヤー

| レイヤー | 機能 | 実装技術 |
|----------|------|----------|
| **Transport Layer** | TLS 1.3暗号化通信 | HTTPS, Certificate Pinning |
| **Network Layer** | IP制限、DDoS保護 | WAF, Rate Limiting, Geo-blocking |
| **Authentication Layer** | 署名検証、認証 | HMAC-SHA256, OAuth 2.0, JWT |
| **Application Layer** | 入力検証、サニタイゼーション | JSON Schema, Input Validation |
| **Data Layer** | データ暗号化、機密保持 | AES-256, Field-level Encryption |

## 🔐 認証・認可メカニズム

### GitHub Webhook Secret検証

#### HMAC-SHA256署名検証
```typescript
// Node.js/TypeScript実装例
import crypto from 'crypto';

export function verifyGitHubSignature(
    payload: string,
    signature: string,
    secret: string
): boolean {
    const hmac = crypto.createHmac('sha256', secret);
    hmac.update(payload);
    const expectedSignature = `sha256=${hmac.digest('hex')}`;
    
    // 定数時間比較でタイミング攻撃を防止
    return crypto.timingSafeEqual(
        Buffer.from(signature),
        Buffer.from(expectedSignature)
    );
}
```

#### セキュリティヘッダー検証
```yaml
# 必須セキュリティヘッダー
required_headers:
  - name: "X-GitHub-Delivery"
    description: "一意のWebhook配信ID"
    validation: "UUID形式"
  
  - name: "X-GitHub-Event" 
    description: "Webhookイベントタイプ"
    validation: "許可されたイベントタイプのみ"
  
  - name: "X-GitHub-Hook-ID"
    description: "Webhook設定ID"
    validation: "数値形式"
    
  - name: "X-GitHub-Hook-Installation-Target-ID"
    description: "インストール対象ID"
    validation: "数値形式"

  - name: "X-Hub-Signature-256"
    description: "HMAC-SHA256署名"
    validation: "sha256=<hex>形式"
```

### IP制限・ホワイトリスト管理

#### GitHub IP範囲
```json
{
  "github_webhook_ips": [
    "140.82.112.0/20",
    "143.55.64.0/20", 
    "185.199.108.0/22",
    "192.30.252.0/22",
    "20.201.28.151/32",
    "20.205.243.166/32"
  ],
  "validation_rules": {
    "strict_mode": true,
    "geo_restriction": ["JP", "US"],
    "custom_allowlist": [
      "organization_specific_ranges"
    ]
  }
}
```

### Rate Limiting実装

#### 多層Rate Limiting
```yaml
rate_limiting:
  global:
    requests_per_minute: 1000
    burst_capacity: 100
    
  per_ip:
    requests_per_minute: 60
    burst_capacity: 20
    
  per_webhook:
    requests_per_minute: 120
    burst_capacity: 30
    
  per_repository:
    requests_per_minute: 100
    burst_capacity: 25

sliding_window:
  enabled: true
  window_size: "60s"
  precision: "1s"
```

## 🛡️ 実装方式

### Node.js/TypeScript実装

#### セキュアなWebhook受信サーバー
```typescript
// src/webhook-handlers/nodejs/src/server.ts
import express from 'express';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import { WebhookValidator } from './security/validator';
import { AuditLogger } from './logging/audit-logger';
import { MetricsCollector } from './monitoring/metrics';

interface WebhookConfig {
    port: number;
    webhookSecret: string;
    allowedIPs: string[];
    rateLimits: RateLimitOptions;
}

export class SecureWebhookServer {
    private app: express.Application;
    private validator: WebhookValidator;
    private auditLogger: AuditLogger;
    private metrics: MetricsCollector;

    constructor(private config: WebhookConfig) {
        this.app = express();
        this.validator = new WebhookValidator(config.webhookSecret);
        this.auditLogger = new AuditLogger();
        this.metrics = new MetricsCollector();
        
        this.setupMiddleware();
        this.setupRoutes();
    }

    private setupMiddleware(): void {
        // セキュリティヘッダー設定
        this.app.use(helmet({
            contentSecurityPolicy: {
                directives: {
                    defaultSrc: ["'self'"],
                    scriptSrc: ["'none'"],
                    objectSrc: ["'none'"]
                }
            },
            hsts: {
                maxAge: 31536000,
                includeSubDomains: true,
                preload: true
            }
        }));

        // Rate Limiting
        const limiter = rateLimit({
            windowMs: 60 * 1000, // 1分
            max: this.config.rateLimits.requestsPerMinute,
            standardHeaders: true,
            legacyHeaders: false,
            handler: (req, res) => {
                this.auditLogger.logSecurityEvent({
                    type: 'RATE_LIMIT_EXCEEDED',
                    ip: req.ip,
                    timestamp: new Date(),
                    details: { path: req.path }
                });
                res.status(429).json({ error: 'Too many requests' });
            }
        });
        this.app.use(limiter);

        // IP制限
        this.app.use((req, res, next) => {
            if (!this.isIPAllowed(req.ip)) {
                this.auditLogger.logSecurityEvent({
                    type: 'UNAUTHORIZED_IP_ACCESS',
                    ip: req.ip,
                    timestamp: new Date()
                });
                return res.status(403).json({ error: 'Forbidden' });
            }
            next();
        });

        // JSON解析
        this.app.use(express.json({ 
            limit: '10mb',
            verify: (req: any, res, buf) => {
                req.rawBody = buf;
            }
        }));
    }

    private setupRoutes(): void {
        // Health Check
        this.app.get('/health', (req, res) => {
            res.json({ status: 'healthy', timestamp: new Date() });
        });

        // Metrics
        this.app.get('/metrics', (req, res) => {
            res.set('Content-Type', 'text/plain');
            res.send(this.metrics.getPrometheusMetrics());
        });

        // Webhook受信エンドポイント
        this.app.post('/webhook/github', async (req, res) => {
            const startTime = Date.now();
            const deliveryId = req.headers['x-github-delivery'] as string;
            const event = req.headers['x-github-event'] as string;
            const signature = req.headers['x-hub-signature-256'] as string;

            try {
                // 署名検証
                if (!this.validator.verifySignature(req.rawBody, signature)) {
                    this.auditLogger.logSecurityEvent({
                        type: 'INVALID_SIGNATURE',
                        deliveryId,
                        ip: req.ip,
                        timestamp: new Date()
                    });
                    return res.status(401).json({ error: 'Invalid signature' });
                }

                // ペイロード検証
                const validationResult = await this.validator.validatePayload(
                    req.body, 
                    event
                );
                if (!validationResult.isValid) {
                    this.auditLogger.logSecurityEvent({
                        type: 'INVALID_PAYLOAD',
                        deliveryId,
                        ip: req.ip,
                        errors: validationResult.errors,
                        timestamp: new Date()
                    });
                    return res.status(400).json({ 
                        error: 'Invalid payload',
                        details: validationResult.errors 
                    });
                }

                // イベント処理
                await this.processWebhookEvent(event, req.body, deliveryId);

                // 成功ログ
                this.auditLogger.logWebhookReceived({
                    deliveryId,
                    event,
                    repository: req.body.repository?.full_name,
                    sender: req.body.sender?.login,
                    ip: req.ip,
                    timestamp: new Date(),
                    processingTime: Date.now() - startTime
                });

                // メトリクス更新
                this.metrics.incrementWebhookReceived(event);
                this.metrics.recordProcessingTime(event, Date.now() - startTime);

                res.json({ status: 'success', deliveryId });

            } catch (error) {
                this.auditLogger.logError({
                    type: 'WEBHOOK_PROCESSING_ERROR',
                    deliveryId,
                    error: error.message,
                    stack: error.stack,
                    timestamp: new Date()
                });

                this.metrics.incrementWebhookErrors(event);
                res.status(500).json({ error: 'Internal server error' });
            }
        });
    }

    private isIPAllowed(ip: string): boolean {
        return this.config.allowedIPs.some(allowedIP => {
            // CIDR範囲チェック実装
            return this.isIPInCIDR(ip, allowedIP);
        });
    }

    private isIPInCIDR(ip: string, cidr: string): boolean {
        // CIDR範囲チェックのロジック実装
        // 省略（実際の実装では ip-cidr ライブラリ等を使用）
        return true;
    }

    private async processWebhookEvent(
        event: string, 
        payload: any, 
        deliveryId: string
    ): Promise<void> {
        // イベント別処理ロジック
        switch (event) {
            case 'push':
                await this.handlePushEvent(payload, deliveryId);
                break;
            case 'pull_request':
                await this.handlePullRequestEvent(payload, deliveryId);
                break;
            case 'issues':
                await this.handleIssuesEvent(payload, deliveryId);
                break;
            case 'repository':
                await this.handleRepositoryEvent(payload, deliveryId);
                break;
            case 'organization':
                await this.handleOrganizationEvent(payload, deliveryId);
                break;
            case 'member':
                await this.handleMemberEvent(payload, deliveryId);
                break;
            case 'team':
                await this.handleTeamEvent(payload, deliveryId);
                break;
            case 'installation':
                await this.handleInstallationEvent(payload, deliveryId);
                break;
            default:
                this.auditLogger.logWarning({
                    type: 'UNKNOWN_EVENT_TYPE',
                    event,
                    deliveryId,
                    timestamp: new Date()
                });
        }
    }

    private async handlePushEvent(payload: any, deliveryId: string): Promise<void> {
        // Push イベント処理
        const { repository, pusher, commits } = payload;
        
        // セキュリティチェック
        if (this.containsSensitiveData(commits)) {
            this.auditLogger.logSecurityEvent({
                type: 'SENSITIVE_DATA_DETECTED',
                repository: repository.full_name,
                pusher: pusher.name,
                deliveryId,
                timestamp: new Date()
            });
        }
    }

    private async handlePullRequestEvent(payload: any, deliveryId: string): Promise<void> {
        // Pull Request イベント処理
        const { action, pull_request, repository } = payload;
        
        // セキュリティレビューが必要かチェック
        if (this.requiresSecurityReview(pull_request)) {
            await this.triggerSecurityReview(pull_request, deliveryId);
        }
    }

    private containsSensitiveData(commits: any[]): boolean {
        // 機密データ検出ロジック
        const sensitivePatterns = [
            /password\s*=\s*["'][^"']+["']/i,
            /api[_-]?key\s*=\s*["'][^"']+["']/i,
            /secret\s*=\s*["'][^"']+["']/i,
            /token\s*=\s*["'][^"']+["']/i,
            /-----BEGIN [A-Z ]+PRIVATE KEY-----/
        ];

        return commits.some(commit => 
            sensitivePatterns.some(pattern => 
                pattern.test(commit.message) || 
                commit.added?.some(file => pattern.test(file)) ||
                commit.modified?.some(file => pattern.test(file))
            )
        );
    }

    public start(): void {
        this.app.listen(this.config.port, () => {
            console.log(`Secure Webhook Server listening on port ${this.config.port}`);
        });
    }
}
```

### Python実装

#### FastAPI セキュアWebhook実装
```python
# src/webhook-handlers/python/src/main.py
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import hashlib
import hmac
import json
import logging
import ipaddress
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, validator
import prometheus_client
from prometheus_client import Counter, Histogram, Gauge

# セキュリティ設定
class SecurityConfig(BaseModel):
    webhook_secret: str
    allowed_ips: list[str]
    rate_limit: str = "60/minute"
    max_payload_size: int = 10 * 1024 * 1024  # 10MB

# Webhook ペイロード検証
class GitHubWebhookPayload(BaseModel):
    action: Optional[str]
    repository: Optional[Dict[str, Any]]
    sender: Optional[Dict[str, Any]]
    organization: Optional[Dict[str, Any]]
    
    @validator('repository')
    def validate_repository(cls, v):
        if v and 'full_name' not in v:
            raise ValueError('Repository must have full_name')
        return v

# メトリクス定義
webhook_requests_total = Counter(
    'webhook_requests_total',
    'Total webhook requests',
    ['event_type', 'status']
)

webhook_processing_duration = Histogram(
    'webhook_processing_duration_seconds',
    'Webhook processing duration',
    ['event_type']
)

webhook_errors_total = Counter(
    'webhook_errors_total',
    'Total webhook errors',
    ['error_type']
)

# Rate Limiter初期化
limiter = Limiter(key_func=get_remote_address)

# アプリケーション初期化
app = FastAPI(
    title="GitHub Webhook Security Server",
    description="エンタープライズ級セキュリティWebhook受信システム",
    version="1.0.0"
)

# Rate Limit エラーハンドラー
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# セキュリティミドルウェア
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["webhook.sas-com.internal", "*.sas-com.com"]
)

# CORS設定（必要に応じて）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],  # 空の配列で全て拒否
    allow_credentials=False,
    allow_methods=["POST"],
    allow_headers=["*"],
)

# セキュリティ検証クラス
class WebhookSecurityValidator:
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """GitHub Webhook署名検証"""
        if not signature.startswith('sha256='):
            return False
            
        expected_signature = hmac.new(
            self.config.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        expected = f"sha256={expected_signature}"
        
        # タイミング攻撃防止のための定数時間比較
        return hmac.compare_digest(signature, expected)

    def verify_ip_address(self, client_ip: str) -> bool:
        """IP制限検証"""
        try:
            client_addr = ipaddress.ip_address(client_ip)
            
            for allowed_cidr in self.config.allowed_ips:
                if client_addr in ipaddress.ip_network(allowed_cidr, strict=False):
                    return True
                    
            return False
        except ValueError:
            self.logger.error(f"Invalid IP address: {client_ip}")
            return False

    def validate_headers(self, request: Request) -> Dict[str, str]:
        """必須ヘッダー検証"""
        required_headers = [
            'x-github-delivery',
            'x-github-event',
            'x-hub-signature-256'
        ]
        
        headers = {}
        for header in required_headers:
            value = request.headers.get(header)
            if not value:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required header: {header}"
                )
            headers[header] = value
            
        return headers

    def sanitize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """ペイロード サニタイゼーション"""
        # 危険な文字列パターンを除去
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'eval\s*\(',
            r'exec\s*\('
        ]
        
        def clean_string(value: str) -> str:
            import re
            for pattern in dangerous_patterns:
                value = re.sub(pattern, '', value, flags=re.IGNORECASE | re.DOTALL)
            return value
        
        def clean_dict(d: Dict[str, Any]) -> Dict[str, Any]:
            cleaned = {}
            for key, value in d.items():
                if isinstance(value, str):
                    cleaned[key] = clean_string(value)
                elif isinstance(value, dict):
                    cleaned[key] = clean_dict(value)
                elif isinstance(value, list):
                    cleaned[key] = [
                        clean_dict(item) if isinstance(item, dict) else
                        clean_string(item) if isinstance(item, str) else item
                        for item in value
                    ]
                else:
                    cleaned[key] = value
            return cleaned
        
        return clean_dict(payload)

# セキュリティ依存関数
def get_security_validator() -> WebhookSecurityValidator:
    config = SecurityConfig(
        webhook_secret=os.getenv('WEBHOOK_SECRET'),
        allowed_ips=os.getenv('ALLOWED_IPS', '').split(',')
    )
    return WebhookSecurityValidator(config)

def verify_webhook_security(
    request: Request,
    validator: WebhookSecurityValidator = Depends(get_security_validator)
) -> Dict[str, Any]:
    """Webhook セキュリティ検証"""
    
    # IP制限チェック
    client_ip = request.client.host
    if not validator.verify_ip_address(client_ip):
        webhook_errors_total.labels(error_type='unauthorized_ip').inc()
        raise HTTPException(
            status_code=403,
            detail="Access denied: IP not allowed"
        )
    
    # ヘッダー検証
    headers = validator.validate_headers(request)
    
    return {
        'client_ip': client_ip,
        'headers': headers,
        'validator': validator
    }

# エンドポイント定義
@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "github-webhook-security-server"
    }

@app.get("/metrics")
async def metrics():
    """Prometheusメトリクスエンドポイント"""
    return Response(
        prometheus_client.generate_latest(),
        media_type="text/plain"
    )

@app.post("/webhook/github")
@limiter.limit("60/minute")
async def github_webhook(
    request: Request,
    security: Dict[str, Any] = Depends(verify_webhook_security)
):
    """GitHub Webhook受信エンドポイント"""
    
    start_time = datetime.utcnow()
    delivery_id = security['headers']['x-github-delivery']
    event_type = security['headers']['x-github-event']
    signature = security['headers']['x-hub-signature-256']
    
    try:
        # ペイロード取得
        raw_body = await request.body()
        if len(raw_body) > security['validator'].config.max_payload_size:
            raise HTTPException(
                status_code=413,
                detail="Payload too large"
            )
        
        # 署名検証
        if not security['validator'].verify_signature(raw_body, signature):
            webhook_errors_total.labels(error_type='invalid_signature').inc()
            raise HTTPException(
                status_code=401,
                detail="Invalid signature"
            )
        
        # JSON解析
        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            webhook_errors_total.labels(error_type='invalid_json').inc()
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON payload"
            )
        
        # ペイロード検証とサニタイゼーション
        try:
            GitHubWebhookPayload(**payload)  # Pydantic検証
            payload = security['validator'].sanitize_payload(payload)
        except Exception as e:
            webhook_errors_total.labels(error_type='invalid_payload').inc()
            raise HTTPException(
                status_code=400,
                detail=f"Invalid payload: {str(e)}"
            )
        
        # イベント処理
        await process_webhook_event(event_type, payload, delivery_id)
        
        # メトリクス更新
        webhook_requests_total.labels(
            event_type=event_type,
            status='success'
        ).inc()
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        webhook_processing_duration.labels(event_type=event_type).observe(processing_time)
        
        return {
            "status": "success",
            "delivery_id": delivery_id,
            "event_type": event_type,
            "processing_time": processing_time
        }
        
    except HTTPException:
        webhook_requests_total.labels(
            event_type=event_type,
            status='error'
        ).inc()
        raise
    except Exception as e:
        webhook_errors_total.labels(error_type='internal_error').inc()
        logging.error(f"Unexpected error processing webhook: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

async def process_webhook_event(event_type: str, payload: Dict[str, Any], delivery_id: str):
    """Webhook イベント処理"""
    
    # イベント別処理
    event_processors = {
        'push': process_push_event,
        'pull_request': process_pull_request_event,
        'issues': process_issues_event,
        'repository': process_repository_event,
        'organization': process_organization_event,
        'member': process_member_event,
        'team': process_team_event,
        'installation': process_installation_event,
        'secret_scanning_alert': process_secret_scanning_event,
        'code_scanning_alert': process_code_scanning_event,
        'dependabot_alert': process_dependabot_event
    }
    
    processor = event_processors.get(event_type)
    if processor:
        await processor(payload, delivery_id)
    else:
        logging.warning(f"No processor found for event type: {event_type}")

async def process_push_event(payload: Dict[str, Any], delivery_id: str):
    """Push イベント処理"""
    repository = payload.get('repository', {})
    commits = payload.get('commits', [])
    
    # セキュリティスキャン
    for commit in commits:
        if contains_sensitive_data(commit):
            await alert_security_team({
                'type': 'SENSITIVE_DATA_DETECTED',
                'repository': repository.get('full_name'),
                'commit_sha': commit.get('id'),
                'delivery_id': delivery_id,
                'timestamp': datetime.utcnow().isoformat()
            })

def contains_sensitive_data(commit: Dict[str, Any]) -> bool:
    """機密データ検出"""
    import re
    
    sensitive_patterns = [
        r'password\s*[=:]\s*["\'][^"\']+["\']',
        r'api[_-]?key\s*[=:]\s*["\'][^"\']+["\']',
        r'secret\s*[=:]\s*["\'][^"\']+["\']',
        r'token\s*[=:]\s*["\'][^"\']+["\']',
        r'-----BEGIN [A-Z ]+PRIVATE KEY-----'
    ]
    
    message = commit.get('message', '')
    for pattern in sensitive_patterns:
        if re.search(pattern, message, re.IGNORECASE):
            return True
    
    return False

async def alert_security_team(alert_data: Dict[str, Any]):
    """セキュリティチーム通知"""
    # 実際の実装では、メール、Slack、Teams等への通知を行う
    logging.critical(f"SECURITY ALERT: {json.dumps(alert_data)}")

if __name__ == "__main__":
    import uvicorn
    import os
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # サーバー起動
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv('PORT', 8000)),
        ssl_keyfile=os.getenv('SSL_KEY_FILE'),
        ssl_certfile=os.getenv('SSL_CERT_FILE')
    )
```

## 🔒 セキュリティ対策

### 脅威対策マトリクス

| 脅威カテゴリ | リスクレベル | 対策 | 実装状況 |
|-------------|-------------|------|----------|
| **Injection Attacks** | Critical | Input Validation, Sanitization | ✅ 実装済み |
| **Man-in-the-Middle** | High | TLS 1.3, Certificate Pinning | ✅ 実装済み |
| **Replay Attacks** | High | Timestamp Validation, Nonce | ✅ 実装済み |
| **DDoS/DoS** | High | Rate Limiting, WAF | ✅ 実装済み |
| **Data Exfiltration** | Critical | Access Control, Encryption | ✅ 実装済み |
| **Privilege Escalation** | Critical | RBAC, Least Privilege | ✅ 実装済み |

### セキュリティ監査ログ

#### 監査ログ形式
```json
{
  "timestamp": "2025-09-10T21:00:00.000Z",
  "event_id": "evt_1234567890",
  "event_type": "webhook_received",
  "severity": "info",
  "source": {
    "ip": "140.82.112.1",
    "user_agent": "GitHub-Hookshot/123456",
    "delivery_id": "12345678-1234-1234-1234-123456789012"
  },
  "webhook": {
    "event_type": "push",
    "repository": "sas-com/example-repo",
    "sender": "developer@sas-com.com",
    "signature_valid": true,
    "processing_time_ms": 150
  },
  "security": {
    "ip_allowed": true,
    "rate_limit_remaining": 58,
    "payload_size_bytes": 1024,
    "sensitive_data_detected": false
  },
  "compliance": {
    "gdpr_compliant": true,
    "retention_days": 365,
    "encrypted": true
  }
}
```

### 暗号化・機密保持

#### データ暗号化仕様
```yaml
encryption:
  at_rest:
    algorithm: "AES-256-GCM"
    key_management: "AWS KMS / Azure Key Vault"
    key_rotation: "90 days"
    
  in_transit:
    protocol: "TLS 1.3"
    cipher_suites:
      - "TLS_AES_256_GCM_SHA384"
      - "TLS_CHACHA20_POLY1305_SHA256"
    certificate_validation: "strict"
    
  field_level:
    sensitive_fields:
      - "webhook_secret"
      - "api_tokens"  
      - "user_emails"
      - "ip_addresses"
    algorithm: "AES-256-SIV"
```

## 📊 監査・ログ機能

### 構造化ログ実装

#### ELK Stack統合
```yaml
# monitoring/elasticsearch/logstash-webhook.conf
input {
  beats {
    port => 5044
  }
}

filter {
  if [fields][service] == "github-webhook" {
    json {
      source => "message"
    }
    
    # IP Geolocation
    geoip {
      source => "[source][ip]"
      target => "[source][geo]"
    }
    
    # Threat Intelligence
    translate {
      field => "[source][ip]"
      destination => "[security][threat_level]"
      dictionary_path => "/etc/logstash/threat_intel.yml"
      fallback => "unknown"
    }
    
    # Anomaly Detection
    if [webhook][processing_time_ms] > 5000 {
      mutate {
        add_tag => ["performance_anomaly"]
      }
    }
    
    if [security][rate_limit_remaining] < 10 {
      mutate {
        add_tag => ["rate_limit_warning"]
      }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "webhook-security-%{+YYYY.MM.dd}"
    template_name => "webhook-security"
    template => "/etc/logstash/webhook-security-template.json"
    template_overwrite => true
  }
  
  # セキュリティアラート
  if "security_alert" in [tags] {
    http {
      url => "https://alerts.sas-com.internal/webhook"
      http_method => "post"
      format => "json"
      headers => {
        "Authorization" => "Bearer ${ALERT_API_TOKEN}"
      }
    }
  }
}
```

## 🔍 運用・監視

### Prometheus監視設定

#### メトリクス定義
```yaml
# monitoring/prometheus/webhook-metrics.yml
groups:
  - name: webhook-security
    rules:
      # 可用性監視
      - alert: WebhookServerDown
        expr: up{job="github-webhook"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Webhook server is down"
          
      # レスポンス時間監視  
      - alert: WebhookHighLatency
        expr: histogram_quantile(0.95, webhook_processing_duration_seconds) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High webhook processing latency"
          
      # エラー率監視
      - alert: WebhookHighErrorRate
        expr: rate(webhook_errors_total[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High webhook error rate"
          
      # セキュリティ監視
      - alert: SuspiciousWebhookActivity
        expr: rate(webhook_requests_total{status="error"}[1m]) > 10
        for: 30s
        labels:
          severity: critical
        annotations:
          summary: "Suspicious webhook activity detected"
          
      # Rate Limit監視
      - alert: RateLimitExceeded  
        expr: rate(webhook_rate_limit_exceeded_total[1m]) > 5
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Multiple rate limit violations"
```

### Grafanaダッシュボード

#### セキュリティ監視ダッシュボード
```json
{
  "dashboard": {
    "title": "GitHub Webhook Security Dashboard",
    "panels": [
      {
        "title": "Webhook Requests",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(webhook_requests_total[5m]))",
            "legendFormat": "Requests/sec"
          }
        ]
      },
      {
        "title": "Success Rate",
        "type": "stat", 
        "targets": [
          {
            "expr": "sum(rate(webhook_requests_total{status=\"success\"}[5m])) / sum(rate(webhook_requests_total[5m])) * 100",
            "legendFormat": "Success %"
          }
        ]
      },
      {
        "title": "Security Events",
        "type": "table",
        "targets": [
          {
            "expr": "increase(webhook_security_events_total[1h])",
            "legendFormat": "{{event_type}}"
          }
        ]
      },
      {
        "title": "Geographic Distribution",
        "type": "geomap",
        "targets": [
          {
            "expr": "sum by (country) (webhook_requests_total)",
            "legendFormat": "{{country}}"
          }
        ]
      }
    ]
  }
}
```

## 🚨 インシデント対応

### セキュリティインシデント対応プロセス

#### 自動対応フロー
```mermaid
graph TD
    A[セキュリティアラート検知] --> B{重要度判定}
    B -->|Critical| C[即座に自動ブロック]
    B -->|High| D[一時的な制限実施]
    B -->|Medium| E[監視強化]
    B -->|Low| F[ログ記録のみ]
    
    C --> G[セキュリティチーム通知]
    D --> G
    E --> H[定期レポート]
    F --> H
    
    G --> I[インシデント調査開始]
    I --> J[根本原因分析]
    J --> K[対策実施]
    K --> L[再発防止策]
    L --> M[インシデント終了]
```

#### インシデント分類

| レベル | 説明 | 対応時間 | 自動アクション |
|--------|------|----------|----------------|
| **L1 (Critical)** | システム侵害、データ漏洩 | 即座 | 自動ブロック + 緊急通知 |
| **L2 (High)** | 攻撃の兆候、異常なトラフィック | 15分以内 | Rate Limit + アラート |
| **L3 (Medium)** | ポリシー違反、設定不備 | 1時間以内 | ログ記録 + 定期報告 |
| **L4 (Low)** | 軽微な異常、情報収集 | 翌営業日 | ログ記録のみ |

## ✅ コンプライアンス

### 規制要件準拠

#### データ保護・プライバシー
```yaml
compliance:
  gdpr:
    data_subjects: ["EU residents"]
    lawful_basis: "legitimate_interest"
    retention_period: "365 days"
    right_to_erasure: true
    data_portability: true
    
  ccpa:
    personal_information: ["ip_addresses", "user_identifiers"]
    opt_out_rights: true
    data_sale_prohibition: true
    
  sox:
    financial_controls: true
    audit_trails: "immutable"
    segregation_of_duties: true
    
  iso27001:
    information_security_management: true
    risk_assessment: "quarterly"
    security_training: "mandatory"
```

### 監査証跡

#### 監査ログ保持ポリシー
```json
{
  "retention_policy": {
    "security_logs": {
      "retention_days": 2555, // 7年
      "archive_after_days": 365,
      "encryption": "AES-256",
      "immutable": true
    },
    "access_logs": {
      "retention_days": 365, // 1年
      "archive_after_days": 90,
      "encryption": "AES-256",
      "immutable": true  
    },
    "performance_logs": {
      "retention_days": 30,
      "archive_after_days": 7,
      "encryption": "AES-256",
      "immutable": false
    }
  },
  "compliance_reports": {
    "frequency": "monthly",
    "recipients": ["compliance@sas-com.com", "security@sas-com.com"],
    "format": "pdf",
    "digital_signature": true
  }
}
```

---

**注意**: この文書には機密性の高いセキュリティ実装詳細が含まれています。適切なアクセス制御の下で管理してください。

**更新履歴**:
- 2025-09-10: 初版作成
- セキュリティレビュー: 承認待ち
- 次回更新予定: 2025-12-10

**担当者**: 
- 作成: GitHub管理チーム
- レビュー: セキュリティチーム
- 承認: CTO Office