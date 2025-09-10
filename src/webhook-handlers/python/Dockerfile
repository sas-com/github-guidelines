# GitHub Webhook Security Server - Python FastAPI
# エス・エー・エス株式会社

# ===========================
# Multi-stage build for security and efficiency
# ===========================

# Stage 1: Build stage
FROM python:3.11-slim AS builder

# セキュリティ: 非rootユーザー作成
RUN groupadd -r webhook && useradd --no-log-init -r -g webhook webhook

# システム依存関係のインストール
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ設定
WORKDIR /app

# Python依存関係管理ツールの更新
RUN pip install --upgrade pip setuptools wheel

# requirements.txtをコピー（キャッシュ最適化）
COPY requirements.txt .

# Python依存関係インストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードコピー
COPY src/ ./src/
COPY config/ ./config/ 2>/dev/null || true

# ===========================
# Stage 2: Runtime stage
# ===========================

FROM python:3.11-slim AS runtime

# セキュリティ: 非rootユーザー作成
RUN groupadd -r webhook && useradd --no-log-init -r -g webhook webhook

# システム依存関係のインストール（ランタイムのみ）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    tzdata \
    tini \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# タイムゾーン設定
ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 作業ディレクトリ設定
WORKDIR /app

# 必要なディレクトリ作成と権限設定
RUN mkdir -p /app/logs /app/tmp && \
    chown -R webhook:webhook /app

# ビルドステージから必要ファイルをコピー
COPY --from=builder --chown=webhook:webhook /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder --chown=webhook:webhook /usr/local/bin/ /usr/local/bin/
COPY --from=builder --chown=webhook:webhook /app/src/ ./src/
COPY --from=builder --chown=webhook:webhook /app/config/ ./config/ 2>/dev/null || true

# requirements.txtもコピー（参照用）
COPY --from=builder --chown=webhook:webhook /app/requirements.txt ./

# 環境変数設定
ENV PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    \
    # アプリケーション設定
    HOST=0.0.0.0 \
    PORT=8000 \
    ENVIRONMENT=production \
    LOG_LEVEL=info \
    \
    # 機能フラグ
    ENABLE_METRICS=true \
    ENABLE_CORS=false \
    ENABLE_DOCS=false \
    ENABLE_COMPRESSION=true \
    \
    # セキュリティ設定
    WEBHOOK_SECURITY_RATE_LIMIT_GLOBAL=1000 \
    WEBHOOK_SECURITY_RATE_LIMIT_PER_IP=60 \
    WEBHOOK_SECURITY_RATE_LIMIT_PER_HOOK=120 \
    WEBHOOK_SECURITY_RATE_LIMIT_PER_REPO=100 \
    WEBHOOK_SECURITY_MAX_PAYLOAD_SIZE_MB=10 \
    WEBHOOK_SECURITY_IP_VALIDATION_STRICT=true \
    WEBHOOK_SECURITY_GEO_RESTRICTIONS="JP,US" \
    \
    # パフォーマンス設定
    UVICORN_WORKERS=4 \
    UVICORN_WORKER_CLASS=uvicorn.workers.UvicornWorker \
    UVICORN_MAX_REQUESTS=1000 \
    UVICORN_MAX_REQUESTS_JITTER=100 \
    UVICORN_KEEPALIVE=2 \
    UVICORN_TIMEOUT_KEEP_ALIVE=5

# 非rootユーザーに切り替え
USER webhook

# ヘルスチェック設定
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# ポート公開
EXPOSE 8000

# シグナルハンドリング用にtiniを使用
ENTRYPOINT ["/usr/bin/tini", "--"]

# アプリケーション開始
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# ===========================
# Development stage (optional)
# ===========================

FROM builder AS development

# 開発用の追加パッケージ
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# 開発用依存関係
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    pytest-cov \
    black \
    isort \
    mypy \
    pre-commit \
    watchdog

# 開発用ユーザー設定
USER webhook

# 開発用環境変数
ENV ENVIRONMENT=development \
    LOG_LEVEL=debug \
    ENABLE_DOCS=true \
    ENABLE_CORS=true

# 開発用ポート
EXPOSE 8000 5678

# 開発用エントリーポイント（リロード機能付き）
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug"]

# ===========================
# Testing stage (optional)
# ===========================

FROM builder AS testing

# テスト用依存関係
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    pytest-cov \
    pytest-mock \
    httpx \
    respx \
    coverage

# テスト用ユーザー設定
USER webhook

# テスト用環境変数
ENV ENVIRONMENT=test \
    WEBHOOK_SECRET=test_secret_for_testing_only \
    WEBHOOK_SECURITY_IP_VALIDATION_STRICT=false

# テストコードコピー
COPY --chown=webhook:webhook tests/ ./tests/

# テスト実行
CMD ["python", "-m", "pytest", "tests/", "-v", "--cov=src", "--cov-report=html", "--cov-report=term"]

# ===========================
# Metadata and Labels
# ===========================

LABEL \
    org.opencontainers.image.title="GitHub Webhook Security Server (Python)" \
    org.opencontainers.image.description="エンタープライズ級GitHub Webhookセキュリティサーバー (Python/FastAPI)" \
    org.opencontainers.image.version="1.0.0" \
    org.opencontainers.image.vendor="エス・エー・エス株式会社" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.source="https://github.com/sas-com/github-guidelines" \
    org.opencontainers.image.documentation="https://github.com/sas-com/github-guidelines/blob/main/WEBHOOK_API_SPECIFICATION.md" \
    org.opencontainers.image.created="2025-09-10T21:00:00Z" \
    \
    io.sas-com.service.name="github-webhook-security" \
    io.sas-com.service.version="1.0.0" \
    io.sas-com.service.component="webhook-handler" \
    io.sas-com.service.language="python" \
    io.sas-com.service.framework="fastapi" \
    \
    security.scan.enabled="true" \
    security.non-root="true" \
    security.signature-verification="hmac-sha256" \
    security.rate-limiting="true" \
    security.ip-restrictions="true" \
    \
    monitoring.metrics.enabled="true" \
    monitoring.metrics.format="prometheus" \
    monitoring.health-check="/health" \
    monitoring.metrics-endpoint="/metrics" \
    \
    compliance.gdpr="true" \
    compliance.logging="structured" \
    compliance.encryption="true"

# ===========================
# Security hardening
# ===========================

# 最終セキュリティ強化
USER root
RUN echo "webhook:x:1001:1001:Webhook User:/app:/sbin/nologin" >> /etc/passwd && \
    echo "webhook:x:1001:" >> /etc/group && \
    # Remove unnecessary packages
    apt-get remove --purge -y \
    curl \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# 最終的に非rootユーザーに切り替え
USER webhook