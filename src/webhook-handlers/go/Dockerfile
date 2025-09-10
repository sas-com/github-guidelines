# GitHub Webhook Security Server - Go/Gin
# エス・エー・エス株式会社

# ===========================
# Multi-stage build for security and efficiency
# ===========================

# Stage 1: Build stage
FROM golang:1.21-alpine AS builder

# セキュリティ: CA証明書を更新
RUN apk --no-cache add ca-certificates git tzdata

# 非rootユーザー作成
RUN addgroup -g 1001 -S webhook && adduser -u 1001 -S webhook -G webhook

# 作業ディレクトリ設定
WORKDIR /build

# Go modules設定
ENV GO111MODULE=on
ENV CGO_ENABLED=0
ENV GOOS=linux
ENV GOARCH=amd64

# go.modとgo.sumをコピー（依存関係キャッシュ最適化）
COPY go.mod go.sum ./

# 依存関係ダウンロード
RUN go mod download && go mod verify

# ソースコードコピー
COPY cmd/ ./cmd/
COPY internal/ ./internal/ 2>/dev/null || true
COPY pkg/ ./pkg/ 2>/dev/null || true

# ビルド実行（静的リンク）
RUN go build \
    -a \
    -installsuffix cgo \
    -ldflags='-w -s -extldflags "-static"' \
    -tags netgo,osusergo \
    -o webhook-server \
    ./cmd/main.go

# バイナリの実行権限確認
RUN chmod +x webhook-server

# ===========================
# Stage 2: Runtime stage
# ===========================

FROM scratch AS runtime

# CA証明書とタイムゾーンデータをコピー
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo
COPY --from=builder /etc/passwd /etc/passwd
COPY --from=builder /etc/group /etc/group

# バイナリをコピー
COPY --from=builder --chown=webhook:webhook /build/webhook-server /webhook-server

# 非rootユーザーに切り替え
USER webhook:webhook

# 環境変数設定
ENV TZ=Asia/Tokyo \
    HOST=0.0.0.0 \
    PORT=8080 \
    ENVIRONMENT=production \
    LOG_LEVEL=info \
    LOG_FORMAT=json \
    LOG_OUTPUT=stdout \
    \
    # 機能フラグ
    ENABLE_CORS=false \
    ENABLE_COMPRESSION=true \
    ENABLE_HEALTH_CHECK=true \
    ENABLE_METRICS=true \
    \
    # セキュリティ設定
    RATE_LIMIT_GLOBAL=1000 \
    RATE_LIMIT_PER_IP=60 \
    RATE_LIMIT_PER_HOOK=120 \
    RATE_LIMIT_PER_REPO=100 \
    MAX_PAYLOAD_SIZE_MB=10 \
    IP_VALIDATION_STRICT=true \
    GEO_RESTRICTIONS="JP,US" \
    ENABLE_SIGNATURE_VERIFY=true \
    \
    # サーバー設定
    READ_TIMEOUT=30s \
    WRITE_TIMEOUT=30s \
    IDLE_TIMEOUT=60s \
    SHUTDOWN_TIMEOUT=30s \
    MAX_HEADER_SIZE=1048576 \
    \
    # メトリクス設定
    METRICS_ENABLED=true \
    METRICS_NAMESPACE=github_webhook \
    METRICS_SUBSYSTEM=security_server

# ヘルスチェック設定
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD ["/webhook-server", "--health-check"] || exit 1

# ポート公開
EXPOSE 8080

# アプリケーション実行
ENTRYPOINT ["/webhook-server"]

# ===========================
# Development stage (optional)
# ===========================

FROM golang:1.21-alpine AS development

# 開発用パッケージインストール
RUN apk --no-cache add \
    git \
    make \
    curl \
    vim \
    bash

# 非rootユーザー作成
RUN addgroup -g 1001 -S webhook && adduser -u 1001 -S webhook -G webhook

# 作業ディレクトリ設定
WORKDIR /app

# Go開発ツールインストール
RUN go install github.com/cosmtrek/air@latest && \
    go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest && \
    go install github.com/securecodewarrior/sast-scan/cmd/gosec@latest

# ソースコードコピー
COPY --chown=webhook:webhook . .

# 依存関係インストール
RUN go mod tidy && go mod download

# 非rootユーザーに切り替え
USER webhook:webhook

# 開発用環境変数
ENV ENVIRONMENT=development \
    LOG_LEVEL=debug \
    ENABLE_CORS=true \
    IP_VALIDATION_STRICT=false \
    WEBHOOK_SECRET=development_secret_only

# 開発用ポート
EXPOSE 8080 2345

# ホットリロード付きで起動
CMD ["air", "-c", ".air.toml"]

# ===========================
# Testing stage (optional)
# ===========================

FROM golang:1.21-alpine AS testing

# テスト用パッケージ
RUN apk --no-cache add \
    git \
    make \
    curl

# 作業ディレクトリ設定
WORKDIR /app

# ソースコードコピー
COPY . .

# 依存関係インストール
RUN go mod tidy && go mod download

# テスト用ツールインストール
RUN go install github.com/securecodewarrior/sast-scan/cmd/gosec@latest && \
    go install honnef.co/go/tools/cmd/staticcheck@latest

# テスト環境変数
ENV ENVIRONMENT=test \
    WEBHOOK_SECRET=test_secret_for_testing_only \
    IP_VALIDATION_STRICT=false \
    ENABLE_SIGNATURE_VERIFY=false

# テスト実行
CMD ["go", "test", "-v", "-race", "-coverprofile=coverage.out", "./..."]

# ===========================
# Production-optimized stage
# ===========================

FROM alpine:3.18 AS production

# セキュリティアップデート
RUN apk --no-cache add --update ca-certificates tzdata && \
    apk --no-cache del apk-tools && \
    rm -rf /var/cache/apk/* /tmp/* /var/tmp/*

# 非rootユーザー作成
RUN addgroup -g 1001 -S webhook && \
    adduser -u 1001 -S webhook -G webhook -D -h /app

# 必要なディレクトリ作成
RUN mkdir -p /app && \
    chown webhook:webhook /app

# バイナリをコピー
COPY --from=builder --chown=webhook:webhook /build/webhook-server /app/webhook-server

# 実行権限設定
RUN chmod +x /app/webhook-server

# 非rootユーザーに切り替え
USER webhook:webhook

# 作業ディレクトリ設定
WORKDIR /app

# 環境変数設定
ENV TZ=Asia/Tokyo \
    HOST=0.0.0.0 \
    PORT=8080 \
    ENVIRONMENT=production \
    LOG_LEVEL=info \
    LOG_FORMAT=json

# ヘルスチェック設定
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD ["./webhook-server", "--health-check"] || exit 1

# ポート公開
EXPOSE 8080

# アプリケーション実行
ENTRYPOINT ["./webhook-server"]

# ===========================
# Metadata and Labels
# ===========================

LABEL \
    org.opencontainers.image.title="GitHub Webhook Security Server (Go)" \
    org.opencontainers.image.description="エンタープライズ級GitHub Webhookセキュリティサーバー (Go/Gin)" \
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
    io.sas-com.service.language="go" \
    io.sas-com.service.framework="gin" \
    \
    security.scan.enabled="true" \
    security.non-root="true" \
    security.signature-verification="hmac-sha256" \
    security.rate-limiting="true" \
    security.ip-restrictions="true" \
    security.static-binary="true" \
    security.minimal-image="true" \
    \
    monitoring.metrics.enabled="true" \
    monitoring.metrics.format="prometheus" \
    monitoring.health-check="/health" \
    monitoring.metrics-endpoint="/metrics" \
    \
    compliance.gdpr="true" \
    compliance.logging="structured" \
    compliance.encryption="true" \
    \
    performance.optimized="true" \
    performance.static-linking="true" \
    performance.minimal-runtime="true"