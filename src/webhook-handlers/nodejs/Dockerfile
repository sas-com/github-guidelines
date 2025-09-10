# GitHub Webhook Security Server - Node.js/TypeScript
# エス・エー・エス株式会社

# ===========================
# Multi-stage build for security and efficiency
# ===========================

# Stage 1: Build stage
FROM node:20-alpine AS builder

# セキュリティ: 非rootユーザーを使用
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# 作業ディレクトリ設定
WORKDIR /app

# システムパッケージ更新とビルドツールインストール
RUN apk update && \
    apk add --no-cache \
    python3 \
    make \
    g++ \
    curl \
    && rm -rf /var/cache/apk/*

# package.jsonとpackage-lock.jsonをコピー（依存関係キャッシュ最適化）
COPY package*.json ./
COPY tsconfig.json ./

# 依存関係インストール（開発依存関係も含む）
RUN npm ci --only=production && npm ci --only=development

# ソースコードコピー
COPY src/ ./src/
COPY config/ ./config/ 2>/dev/null || true

# TypeScriptコンパイル
RUN npm run build

# プロダクション依存関係のみ再インストール
RUN npm ci --only=production && npm cache clean --force

# ===========================
# Stage 2: Runtime stage
# ===========================

FROM node:20-alpine AS runtime

# セキュリティ: 非rootユーザー作成
RUN addgroup -g 1001 -S nodejs && \
    adduser -S webhook -u 1001 -G nodejs

# システムパッケージ更新とランタイム依存関係インストール
RUN apk update && \
    apk add --no-cache \
    curl \
    ca-certificates \
    tzdata \
    tini \
    && rm -rf /var/cache/apk/*

# タイムゾーン設定
ENV TZ=Asia/Tokyo
RUN cp /usr/share/zoneinfo/${TZ} /etc/localtime && \
    echo ${TZ} > /etc/timezone

# 作業ディレクトリ設定
WORKDIR /app

# 必要なディレクトリ作成と権限設定
RUN mkdir -p /app/logs /app/tmp && \
    chown -R webhook:nodejs /app

# ビルドステージから必要ファイルをコピー
COPY --from=builder --chown=webhook:nodejs /app/dist ./dist
COPY --from=builder --chown=webhook:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=webhook:nodejs /app/package.json ./package.json

# 設定ファイルコピー（存在する場合のみ）
COPY --chown=webhook:nodejs config/ ./config/ 2>/dev/null || true

# 非rootユーザーに切り替え
USER webhook

# 環境変数設定
ENV NODE_ENV=production \
    HOST=0.0.0.0 \
    PORT=3000 \
    LOG_LEVEL=info \
    ENABLE_METRICS=true \
    ENABLE_HEALTH_CHECK=true \
    COMPRESSION_ENABLED=true \
    TRUST_PROXY=true \
    REQUEST_TIMEOUT_MS=30000 \
    BODY_LIMIT=10mb \
    RATE_LIMIT_GLOBAL=1000 \
    RATE_LIMIT_PER_IP=60 \
    RATE_LIMIT_PER_HOOK=120 \
    RATE_LIMIT_PER_REPO=100 \
    RATE_LIMIT_BURST=20 \
    MAX_PAYLOAD_SIZE=10485760 \
    IP_VALIDATION_STRICT=true

# ヘルスチェック設定
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# ポート公開
EXPOSE 3000

# シグナルハンドリング用にtiniを使用
ENTRYPOINT ["/sbin/tini", "--"]

# アプリケーション開始
CMD ["node", "dist/server.js"]

# ===========================
# Development stage (optional)
# ===========================

FROM builder AS development

# 開発用の追加パッケージ
RUN apk add --no-cache \
    git \
    openssh-client

# 開発用ユーザー設定
USER nextjs

# 開発用環境変数
ENV NODE_ENV=development \
    LOG_LEVEL=debug \
    ENABLE_SWAGGER=true

# 開発用ポート
EXPOSE 3000 9229

# 開発用エントリーポイント（デバッグモード付き）
CMD ["npm", "run", "dev"]

# ===========================
# Metadata and Labels
# ===========================

LABEL \
    org.opencontainers.image.title="GitHub Webhook Security Server" \
    org.opencontainers.image.description="エンタープライズ級GitHub Webhookセキュリティサーバー (Node.js/TypeScript)" \
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
    io.sas-com.service.language="nodejs" \
    io.sas-com.service.framework="express" \
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
    compliance.logging="audit" \
    compliance.encryption="true"

# セキュリティ強化のための最終設定
RUN echo "webhook:x:1001:1001:Webhook User:/app:/sbin/nologin" >> /etc/passwd && \
    echo "nodejs:x:1001:" >> /etc/group