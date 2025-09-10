# GitHub Webhook API 仕様・設計ドキュメント

**エス・エー・エス株式会社**  
*GitHub Webhook API エンタープライズ仕様*

## 📋 目次

1. [API概要](#api概要)
2. [OpenAPI 3.1仕様](#openapi-31仕様)
3. [エンドポイント仕様](#エンドポイント仕様)
4. [認証・認可](#認証認可)
5. [リクエスト・レスポンス形式](#リクエストレスポンス形式)
6. [エラーハンドリング](#エラーハンドリング)
7. [レート制限](#レート制限)
8. [セキュリティ仕様](#セキュリティ仕様)
9. [監視・メトリクス](#監視メトリクス)
10. [SDK・クライアントライブラリ](#sdkクライアントライブラリ)

## 📌 API概要

### 基本情報
- **API名**: GitHub Webhook Security API
- **バージョン**: v1.0.0
- **ベースURL**: `https://webhook.sas-com.internal/api/v1`
- **プロトコル**: HTTPS（TLS 1.3）
- **認証方式**: HMAC-SHA256 + Bearer Token
- **データ形式**: JSON
- **文字エンコーディング**: UTF-8

### サポート言語・フレームワーク
| 言語 | フレームワーク | ポート | ヘルスチェック |
|------|---------------|--------|---------------|
| Node.js/TypeScript | Express.js | 3000 | `/health` |
| Python | FastAPI | 8000 | `/health` |
| Go | Gin | 8080 | `/health` |
| Java | Spring Boot | 8090 | `/health` |

## 📝 OpenAPI 3.1仕様

### 完全仕様定義

```yaml
openapi: 3.1.0
info:
  title: GitHub Webhook Security API
  description: |
    エス・エー・エス株式会社のGitHub Webhook セキュリティ処理API
    
    ## 主要機能
    - セキュアなWebhook受信・検証
    - マルチ言語対応（Node.js, Python, Go, Java）
    - エンタープライズ級セキュリティ
    - リアルタイム監視・アラート
    - 包括的な監査ログ
    
    ## セキュリティ
    - HMAC-SHA256署名検証
    - IP制限・ジオブロッキング
    - Rate Limiting
    - TLS 1.3暗号化
    - 入力検証・サニタイゼーション
    
  version: 1.0.0
  contact:
    name: SAS GitHub管理チーム
    email: github@sas-com.com
    url: https://github.sas-com.internal
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT
  termsOfService: https://sas-com.com/terms

servers:
  - url: https://webhook.sas-com.internal/api/v1
    description: 本番環境
  - url: https://webhook-staging.sas-com.internal/api/v1
    description: ステージング環境
  - url: https://webhook-dev.sas-com.internal/api/v1
    description: 開発環境

# セキュリティスキーム
security:
  - GitHubWebhookSignature: []
  - BearerAuth: []

components:
  securitySchemes:
    GitHubWebhookSignature:
      type: apiKey
      in: header
      name: X-Hub-Signature-256
      description: GitHub Webhook HMAC-SHA256署名
      
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: JWT Bearer Token

  # 共通スキーマ定義
  schemas:
    # Webhook共通スキーマ
    WebhookHeaders:
      type: object
      required:
        - x-github-delivery
        - x-github-event
        - x-hub-signature-256
        - user-agent
      properties:
        x-github-delivery:
          type: string
          format: uuid
          description: 一意のWebhook配信ID
          example: "12345678-1234-1234-1234-123456789012"
        x-github-event:
          type: string
          enum:
            - push
            - pull_request
            - issues
            - repository
            - organization
            - member
            - team
            - installation
            - secret_scanning_alert
            - code_scanning_alert
            - dependabot_alert
          description: GitHubイベントタイプ
          example: "push"
        x-github-hook-id:
          type: integer
          description: Webhook設定ID
          example: 12345
        x-github-hook-installation-target-id:
          type: integer
          description: インストール対象ID
          example: 67890
        x-hub-signature-256:
          type: string
          pattern: '^sha256=[a-f0-9]{64}$'
          description: HMAC-SHA256署名
          example: "sha256=1234567890abcdef..."
        user-agent:
          type: string
          pattern: '^GitHub-Hookshot/[a-f0-9]+$'
          description: GitHub User-Agent
          example: "GitHub-Hookshot/044aadd"

    # 基本レスポンス
    SuccessResponse:
      type: object
      required:
        - status
        - delivery_id
        - timestamp
      properties:
        status:
          type: string
          enum: [success]
          description: 処理ステータス
        delivery_id:
          type: string
          format: uuid
          description: Webhook配信ID
        event_type:
          type: string
          description: 処理されたイベントタイプ
        processing_time_ms:
          type: number
          minimum: 0
          description: 処理時間（ミリ秒）
        timestamp:
          type: string
          format: date-time
          description: 処理完了時刻（ISO 8601）
        metadata:
          type: object
          description: 追加メタデータ
          properties:
            repository:
              type: string
              description: リポジトリ名
            sender:
              type: string
              description: 送信者
            action:
              type: string
              description: アクション

    # エラーレスポンス
    ErrorResponse:
      type: object
      required:
        - error
        - message
        - timestamp
        - request_id
      properties:
        error:
          type: string
          description: エラーコード
          example: "INVALID_SIGNATURE"
        message:
          type: string
          description: エラーメッセージ
          example: "Invalid webhook signature"
        details:
          type: string
          description: 詳細情報
          example: "Signature verification failed"
        timestamp:
          type: string
          format: date-time
          description: エラー発生時刻
        request_id:
          type: string
          format: uuid
          description: リクエストID
        validation_errors:
          type: array
          description: 入力検証エラー
          items:
            type: object
            properties:
              field:
                type: string
                description: エラーフィールド
              message:
                type: string
                description: エラーメッセージ
              value:
                type: string
                description: 不正な値

    # GitHub Event Payloads
    GitHubRepository:
      type: object
      required:
        - id
        - name
        - full_name
        - private
      properties:
        id:
          type: integer
          description: リポジトリID
        name:
          type: string
          description: リポジトリ名
        full_name:
          type: string
          description: 完全名（owner/repo）
        private:
          type: boolean
          description: プライベートリポジトリかどうか
        html_url:
          type: string
          format: uri
          description: リポジトリURL
        description:
          type: string
          nullable: true
          description: リポジトリ説明
        default_branch:
          type: string
          description: デフォルトブランチ名

    GitHubUser:
      type: object
      required:
        - id
        - login
      properties:
        id:
          type: integer
          description: ユーザーID
        login:
          type: string
          description: ユーザー名
        avatar_url:
          type: string
          format: uri
          description: アバターURL
        html_url:
          type: string
          format: uri
          description: ユーザープロファイルURL

    # Push Event
    PushEventPayload:
      type: object
      required:
        - ref
        - commits
        - repository
        - pusher
        - sender
      properties:
        ref:
          type: string
          description: Git参照（refs/heads/main等）
          example: "refs/heads/main"
        before:
          type: string
          pattern: '^[a-f0-9]{40}$'
          description: プッシュ前のコミットSHA
        after:
          type: string
          pattern: '^[a-f0-9]{40}$'
          description: プッシュ後のコミットSHA
        commits:
          type: array
          description: コミット一覧
          items:
            $ref: '#/components/schemas/GitHubCommit'
        repository:
          $ref: '#/components/schemas/GitHubRepository'
        pusher:
          type: object
          properties:
            name:
              type: string
            email:
              type: string
              format: email
        sender:
          $ref: '#/components/schemas/GitHubUser'

    GitHubCommit:
      type: object
      properties:
        id:
          type: string
          pattern: '^[a-f0-9]{40}$'
          description: コミットSHA
        message:
          type: string
          description: コミットメッセージ
        timestamp:
          type: string
          format: date-time
          description: コミット時刻
        url:
          type: string
          format: uri
          description: コミットURL
        author:
          type: object
          properties:
            name:
              type: string
            email:
              type: string
              format: email
        committer:
          type: object
          properties:
            name:
              type: string
            email:
              type: string
              format: email
        added:
          type: array
          items:
            type: string
          description: 追加されたファイル
        removed:
          type: array
          items:
            type: string
          description: 削除されたファイル
        modified:
          type: array
          items:
            type: string
          description: 変更されたファイル

    # Pull Request Event
    PullRequestEventPayload:
      type: object
      required:
        - action
        - number
        - pull_request
        - repository
        - sender
      properties:
        action:
          type: string
          enum:
            - opened
            - closed
            - reopened
            - edited
            - assigned
            - unassigned
            - labeled
            - unlabeled
            - synchronize
          description: プルリクエストのアクション
        number:
          type: integer
          description: プルリクエスト番号
        pull_request:
          $ref: '#/components/schemas/GitHubPullRequest'
        repository:
          $ref: '#/components/schemas/GitHubRepository'
        sender:
          $ref: '#/components/schemas/GitHubUser'

    GitHubPullRequest:
      type: object
      properties:
        id:
          type: integer
        number:
          type: integer
        state:
          type: string
          enum: [open, closed]
        title:
          type: string
        body:
          type: string
          nullable: true
        html_url:
          type: string
          format: uri
        user:
          $ref: '#/components/schemas/GitHubUser'
        head:
          type: object
          properties:
            ref:
              type: string
            sha:
              type: string
              pattern: '^[a-f0-9]{40}$'
            repo:
              $ref: '#/components/schemas/GitHubRepository'
        base:
          type: object
          properties:
            ref:
              type: string
            sha:
              type: string
              pattern: '^[a-f0-9]{40}$'
            repo:
              $ref: '#/components/schemas/GitHubRepository'

    # ヘルスチェック
    HealthCheckResponse:
      type: object
      required:
        - status
        - timestamp
        - version
      properties:
        status:
          type: string
          enum: [healthy, unhealthy, degraded]
          description: サービス状態
        timestamp:
          type: string
          format: date-time
          description: チェック実行時刻
        version:
          type: string
          description: APIバージョン
        service:
          type: string
          description: サービス名
        uptime_seconds:
          type: number
          description: 稼働時間（秒）
        dependencies:
          type: object
          description: 依存サービス状態
          properties:
            database:
              type: string
              enum: [healthy, unhealthy]
            redis:
              type: string
              enum: [healthy, unhealthy]
            elasticsearch:
              type: string
              enum: [healthy, unhealthy]

    # メトリクス
    MetricsResponse:
      type: string
      description: Prometheus形式のメトリクス
      example: |
        # HELP webhook_requests_total Total number of webhook requests
        # TYPE webhook_requests_total counter
        webhook_requests_total{event_type="push",status="success"} 1234
        
        # HELP webhook_processing_duration_seconds Webhook processing duration
        # TYPE webhook_processing_duration_seconds histogram
        webhook_processing_duration_seconds_bucket{event_type="push",le="0.1"} 100
        webhook_processing_duration_seconds_bucket{event_type="push",le="0.5"} 120

# エンドポイント定義
paths:
  # Webhook受信エンドポイント
  /webhook/github:
    post:
      summary: GitHub Webhook受信
      description: |
        GitHubからのWebhookイベントを受信・処理します。
        
        ## セキュリティ
        - HMAC-SHA256署名検証必須
        - IP制限あり（GitHub IP範囲のみ）
        - Rate Limiting適用
        - ペイロードサイズ制限（10MB）
        
        ## サポートイベント
        - push: リポジトリへのプッシュ
        - pull_request: プルリクエスト操作
        - issues: イシュー操作
        - repository: リポジトリ操作
        - organization: 組織操作
        - member: メンバー操作
        - team: チーム操作
        - installation: GitHub App操作
        - security alerts: セキュリティアラート
        
      operationId: receiveGitHubWebhook
      tags:
        - Webhook
      parameters:
        - name: X-GitHub-Delivery
          in: header
          required: true
          schema:
            type: string
            format: uuid
          description: 一意のWebhook配信ID
        - name: X-GitHub-Event
          in: header
          required: true
          schema:
            type: string
          description: GitHubイベントタイプ
        - name: X-GitHub-Hook-ID
          in: header
          schema:
            type: integer
          description: Webhook設定ID
        - name: X-GitHub-Hook-Installation-Target-ID
          in: header
          schema:
            type: integer
          description: インストール対象ID
        - name: X-Hub-Signature-256
          in: header
          required: true
          schema:
            type: string
            pattern: '^sha256=[a-f0-9]{64}$'
          description: HMAC-SHA256署名
        - name: User-Agent
          in: header
          required: true
          schema:
            type: string
            pattern: '^GitHub-Hookshot/[a-f0-9]+$'
          description: GitHub User-Agent
        - name: Content-Type
          in: header
          required: true
          schema:
            type: string
            enum: ['application/json']
          description: コンテンツタイプ
      
      requestBody:
        description: GitHub Webhookペイロード
        required: true
        content:
          application/json:
            schema:
              oneOf:
                - $ref: '#/components/schemas/PushEventPayload'
                - $ref: '#/components/schemas/PullRequestEventPayload'
                # 他のイベントタイプも追加可能
            examples:
              push_event:
                summary: Push Event
                value:
                  ref: "refs/heads/main"
                  before: "0000000000000000000000000000000000000000"
                  after: "1234567890abcdef1234567890abcdef12345678"
                  repository:
                    id: 123456
                    name: "example-repo"
                    full_name: "sas-com/example-repo"
                    private: true
                  commits:
                    - id: "1234567890abcdef1234567890abcdef12345678"
                      message: "feat: 新機能追加"
                      timestamp: "2025-09-10T21:00:00Z"
                  pusher:
                    name: "developer"
                    email: "developer@sas-com.com"
                  sender:
                    id: 12345
                    login: "developer"
              
              pull_request_event:
                summary: Pull Request Event
                value:
                  action: "opened"
                  number: 42
                  pull_request:
                    id: 123456789
                    number: 42
                    state: "open"
                    title: "新機能の追加"
                    body: "詳細な説明"
                  repository:
                    id: 123456
                    name: "example-repo"
                    full_name: "sas-com/example-repo"
                    private: true

      responses:
        '200':
          description: 正常処理完了
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SuccessResponse'
              examples:
                success:
                  summary: 成功レスポンス
                  value:
                    status: "success"
                    delivery_id: "12345678-1234-1234-1234-123456789012"
                    event_type: "push"
                    processing_time_ms: 150
                    timestamp: "2025-09-10T21:00:00.000Z"
                    metadata:
                      repository: "sas-com/example-repo"
                      sender: "developer"
                      action: "push"
        
        '400':
          description: 不正なリクエスト
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
              examples:
                invalid_payload:
                  summary: 不正なペイロード
                  value:
                    error: "INVALID_PAYLOAD"
                    message: "Invalid JSON payload"
                    details: "Payload validation failed"
                    timestamp: "2025-09-10T21:00:00.000Z"
                    request_id: "req_1234567890"
                    validation_errors:
                      - field: "repository.full_name"
                        message: "Required field is missing"
                        value: null
        
        '401':
          description: 認証失敗
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
              examples:
                invalid_signature:
                  summary: 署名検証失敗
                  value:
                    error: "INVALID_SIGNATURE"
                    message: "Invalid webhook signature"
                    details: "HMAC-SHA256 signature verification failed"
                    timestamp: "2025-09-10T21:00:00.000Z"
                    request_id: "req_1234567890"
        
        '403':
          description: アクセス拒否
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
              examples:
                forbidden_ip:
                  summary: IP制限
                  value:
                    error: "FORBIDDEN_IP"
                    message: "Access denied: IP not allowed"
                    details: "Request from unauthorized IP address"
                    timestamp: "2025-09-10T21:00:00.000Z"
                    request_id: "req_1234567890"
        
        '413':
          description: ペイロードサイズ超過
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
              examples:
                payload_too_large:
                  summary: ペイロードサイズ超過
                  value:
                    error: "PAYLOAD_TOO_LARGE"
                    message: "Request payload too large"
                    details: "Maximum payload size is 10MB"
                    timestamp: "2025-09-10T21:00:00.000Z"
                    request_id: "req_1234567890"
        
        '429':
          description: レート制限超過
          headers:
            X-RateLimit-Limit:
              schema:
                type: integer
              description: レート制限値
            X-RateLimit-Remaining:
              schema:
                type: integer
              description: 残りリクエスト数
            X-RateLimit-Reset:
              schema:
                type: integer
              description: リセット時刻（Unix timestamp）
            Retry-After:
              schema:
                type: integer
              description: 再試行までの秒数
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
              examples:
                rate_limit_exceeded:
                  summary: レート制限超過
                  value:
                    error: "RATE_LIMIT_EXCEEDED"
                    message: "Too many requests"
                    details: "Rate limit of 60 requests per minute exceeded"
                    timestamp: "2025-09-10T21:00:00.000Z"
                    request_id: "req_1234567890"
        
        '500':
          description: 内部サーバーエラー
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
              examples:
                internal_error:
                  summary: 内部エラー
                  value:
                    error: "INTERNAL_SERVER_ERROR"
                    message: "Internal server error"
                    details: "An unexpected error occurred"
                    timestamp: "2025-09-10T21:00:00.000Z"
                    request_id: "req_1234567890"

  # ヘルスチェック
  /health:
    get:
      summary: ヘルスチェック
      description: |
        サービスの健全性をチェックします。
        
        ## チェック項目
        - アプリケーション状態
        - 依存サービス接続状態
        - リソース使用状況
        - 設定値検証
        
      operationId: healthCheck
      tags:
        - System
      responses:
        '200':
          description: サービス正常
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HealthCheckResponse'
              examples:
                healthy:
                  summary: 正常状態
                  value:
                    status: "healthy"
                    timestamp: "2025-09-10T21:00:00.000Z"
                    version: "1.0.0"
                    service: "github-webhook-security-server"
                    uptime_seconds: 86400
                    dependencies:
                      database: "healthy"
                      redis: "healthy"
                      elasticsearch: "healthy"
        
        '503':
          description: サービス異常
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HealthCheckResponse'
              examples:
                unhealthy:
                  summary: 異常状態
                  value:
                    status: "unhealthy"
                    timestamp: "2025-09-10T21:00:00.000Z"
                    version: "1.0.0"
                    service: "github-webhook-security-server"
                    uptime_seconds: 86400
                    dependencies:
                      database: "unhealthy"
                      redis: "healthy"
                      elasticsearch: "healthy"

  # メトリクス
  /metrics:
    get:
      summary: Prometheusメトリクス
      description: |
        Prometheus形式でメトリクスを出力します。
        
        ## 取得可能メトリクス
        - webhook_requests_total: 総リクエスト数
        - webhook_processing_duration_seconds: 処理時間
        - webhook_errors_total: エラー総数
        - webhook_rate_limit_exceeded_total: レート制限違反数
        - webhook_security_events_total: セキュリティイベント数
        
      operationId: getMetrics
      tags:
        - Monitoring
      responses:
        '200':
          description: メトリクス取得成功
          content:
            text/plain:
              schema:
                $ref: '#/components/schemas/MetricsResponse'

  # 設定情報
  /config:
    get:
      summary: 設定情報取得
      description: |
        現在のAPI設定情報を取得します。
        機密情報は除かれます。
        
      operationId: getConfig
      tags:
        - System
      security:
        - BearerAuth: []
      responses:
        '200':
          description: 設定情報
          content:
            application/json:
              schema:
                type: object
                properties:
                  version:
                    type: string
                  environment:
                    type: string
                  rate_limits:
                    type: object
                    properties:
                      global_per_minute:
                        type: integer
                      per_ip_per_minute:
                        type: integer
                  security:
                    type: object
                    properties:
                      allowed_events:
                        type: array
                        items:
                          type: string
                      max_payload_size_mb:
                        type: integer
                      signature_algorithm:
                        type: string
```

## 🔗 エンドポイント仕様

### 主要エンドポイント一覧

| メソッド | エンドポイント | 説明 | 認証 | Rate Limit |
|----------|---------------|------|------|-----------|
| `POST` | `/webhook/github` | Webhook受信 | HMAC-SHA256 | 60/分 |
| `GET` | `/health` | ヘルスチェック | なし | 制限なし |
| `GET` | `/metrics` | メトリクス取得 | なし | 10/分 |
| `GET` | `/config` | 設定情報 | Bearer Token | 10/分 |

### Webhookイベント対応表

| イベントタイプ | 説明 | 処理内容 | セキュリティチェック |
|-------------|------|----------|-------------------|
| `push` | リポジトリプッシュ | コミット解析、機密情報検出 | ✅ |
| `pull_request` | プルリクエスト操作 | セキュリティレビュー判定 | ✅ |
| `issues` | イシュー操作 | 自動ラベリング | ❌ |
| `repository` | リポジトリ操作 | アクセス権限同期 | ✅ |
| `organization` | 組織操作 | メンバー権限更新 | ✅ |
| `member` | メンバー操作 | アクセス監査ログ | ✅ |
| `team` | チーム操作 | 権限継承処理 | ✅ |
| `installation` | GitHub App操作 | インストール状況同期 | ✅ |
| `secret_scanning_alert` | シークレット検出 | 緊急アラート発出 | ✅ |
| `code_scanning_alert` | コード解析アラート | 脆弱性通知 | ✅ |
| `dependabot_alert` | 依存関係アラート | 依存関係更新通知 | ✅ |

## 🔐 認証・認可

### HMAC-SHA256署名検証

#### 検証プロセス
```typescript
function verifyGitHubSignature(
  payload: string,
  signature: string,
  secret: string
): boolean {
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');
    
  const expected = `sha256=${expectedSignature}`;
  
  // 定数時間比較でタイミング攻撃防止
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  );
}
```

#### セキュリティ要件
- **署名アルゴリズム**: HMAC-SHA256
- **署名フォーマット**: `sha256=<hex_digest>`
- **検証方式**: 定数時間比較
- **秘密鍵管理**: AWS Secrets Manager / Azure Key Vault
- **鍵ローテーション**: 90日周期

### IP制限・ホワイトリスト

#### GitHub公式IP範囲
```json
{
  "webhook_source_ips": [
    "140.82.112.0/20",
    "143.55.64.0/20", 
    "185.199.108.0/22",
    "192.30.252.0/22",
    "20.201.28.151/32",
    "20.205.243.166/32",
    "20.248.137.48/32",
    "20.207.73.82/32",
    "20.27.177.113/32",
    "20.200.245.247/32",
    "20.233.54.53/32"
  ],
  "validation": {
    "strict_mode": true,
    "allow_private_ranges": false,
    "geo_restriction": ["JP", "US", "SG"],
    "custom_allowlist": []
  }
}
```

## 📝 リクエスト・レスポンス形式

### リクエスト形式

#### 必須ヘッダー
```http
POST /webhook/github HTTP/1.1
Host: webhook.sas-com.internal
Content-Type: application/json
Content-Length: 2048
User-Agent: GitHub-Hookshot/abc123
X-GitHub-Delivery: 12345678-1234-1234-1234-123456789012
X-GitHub-Event: push
X-GitHub-Hook-ID: 123456
X-GitHub-Hook-Installation-Target-ID: 789012
X-Hub-Signature-256: sha256=1234567890abcdef...
```

#### ペイロード例
```json
{
  "ref": "refs/heads/main",
  "before": "0000000000000000000000000000000000000000",
  "after": "1234567890abcdef1234567890abcdef12345678",
  "repository": {
    "id": 123456,
    "name": "example-repo",
    "full_name": "sas-com/example-repo",
    "private": true,
    "html_url": "https://github.com/sas-com/example-repo",
    "description": "サンプルリポジトリ",
    "default_branch": "main"
  },
  "commits": [
    {
      "id": "1234567890abcdef1234567890abcdef12345678",
      "message": "feat: 新機能追加\n\n詳細な説明",
      "timestamp": "2025-09-10T21:00:00Z",
      "url": "https://github.com/sas-com/example-repo/commit/1234567890abcdef1234567890abcdef12345678",
      "author": {
        "name": "Developer",
        "email": "developer@sas-com.com"
      },
      "committer": {
        "name": "Developer", 
        "email": "developer@sas-com.com"
      },
      "added": ["src/new-feature.js", "tests/new-feature.test.js"],
      "removed": [],
      "modified": ["README.md", "package.json"]
    }
  ],
  "pusher": {
    "name": "developer",
    "email": "developer@sas-com.com"
  },
  "sender": {
    "id": 12345,
    "login": "developer",
    "avatar_url": "https://avatars.githubusercontent.com/u/12345?v=4",
    "html_url": "https://github.com/developer"
  }
}
```

### レスポンス形式

#### 成功レスポンス
```json
{
  "status": "success",
  "delivery_id": "12345678-1234-1234-1234-123456789012",
  "event_type": "push",
  "processing_time_ms": 156,
  "timestamp": "2025-09-10T21:00:00.123Z",
  "metadata": {
    "repository": "sas-com/example-repo",
    "sender": "developer",
    "action": "push",
    "commits_processed": 1,
    "security_checks_passed": true,
    "sensitive_data_detected": false
  }
}
```

#### エラーレスポンス
```json
{
  "error": "INVALID_SIGNATURE",
  "message": "Invalid webhook signature",
  "details": "HMAC-SHA256 signature verification failed. Expected signature does not match provided signature.",
  "timestamp": "2025-09-10T21:00:00.123Z",
  "request_id": "req_1234567890abcdef",
  "validation_errors": null,
  "help_url": "https://docs.github.com/webhooks/securing/",
  "correlation_id": "correlation_abc123def456"
}
```

## ⚠️ エラーハンドリング

### エラーコード一覧

| エラーコード | HTTPステータス | 説明 | 対処法 |
|-------------|---------------|------|--------|
| `INVALID_SIGNATURE` | 401 | 署名検証失敗 | Webhook秘密鍵を確認 |
| `INVALID_PAYLOAD` | 400 | ペイロード不正 | JSONフォーマットを確認 |
| `FORBIDDEN_IP` | 403 | IP制限 | 許可IP範囲を確認 |
| `UNSUPPORTED_EVENT` | 400 | 未サポートイベント | サポート対象イベント確認 |
| `PAYLOAD_TOO_LARGE` | 413 | ペイロードサイズ超過 | ペイロードサイズを削減 |
| `RATE_LIMIT_EXCEEDED` | 429 | レート制限超過 | 送信頻度を調整 |
| `MISSING_HEADERS` | 400 | 必須ヘッダー不足 | ヘッダー設定を確認 |
| `INTERNAL_SERVER_ERROR` | 500 | 内部サーバーエラー | システム管理者に連絡 |
| `SERVICE_UNAVAILABLE` | 503 | サービス利用不可 | メンテナンス状況確認 |
| `TIMEOUT` | 504 | 処理タイムアウト | リクエスト再送信 |

### エラーレスポンス仕様

#### 基本構造
```typescript
interface ErrorResponse {
  error: string;           // エラーコード
  message: string;         // エラーメッセージ
  details?: string;        // 詳細情報
  timestamp: string;       // ISO 8601形式
  request_id: string;      // リクエスト追跡ID
  validation_errors?: ValidationError[]; // 検証エラー詳細
  help_url?: string;       // ヘルプURL
  correlation_id?: string; // 相関ID
}

interface ValidationError {
  field: string;           // エラーフィールド
  message: string;         // エラーメッセージ  
  value?: any;            // 不正値
  expected?: string;       // 期待値
}
```

## ⏱️ レート制限

### 制限レベル

| レベル | 制限 | 対象 | ウィンドウ | バーストキャパシティ |
|--------|------|------|----------|-------------------|
| **Global** | 1000 req/min | 全体 | 60秒 | 100 |
| **Per IP** | 60 req/min | 送信元IP | 60秒 | 20 |
| **Per Hook** | 120 req/min | Webhook設定 | 60秒 | 30 |
| **Per Repo** | 100 req/min | リポジトリ | 60秒 | 25 |

### レート制限ヘッダー

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 57
X-RateLimit-Reset: 1694374800
X-RateLimit-Used: 3
X-RateLimit-Window: 60
Retry-After: 30
```

### 制限超過時の処理

#### 段階的制限
1. **警告レベル (80%)**：ヘッダーで警告
2. **制限レベル (100%)**：429エラー返却
3. **ブロックレベル (150%)**：一時的IP制限
4. **緊急レベル (200%)**：緊急アラート発出

## 🛡️ セキュリティ仕様

### セキュリティヘッダー

```http
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Content-Security-Policy: default-src 'self'; script-src 'none'; object-src 'none'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

### 入力検証・サニタイゼーション

#### 検証ルール
```yaml
validation_rules:
  payload_size:
    max_bytes: 10485760  # 10MB
    min_bytes: 1
    
  string_fields:
    max_length: 65536
    allowed_chars: "^[\\x20-\\x7E\\x0A\\x0D]*$"  # ASCII + CRLF
    
  json_structure:
    max_depth: 10
    max_objects: 1000
    max_arrays: 100
    
  headers:
    required:
      - "x-github-delivery"
      - "x-github-event"  
      - "x-hub-signature-256"
      - "user-agent"
    validation:
      x-github-delivery: "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
      x-github-event: "^(push|pull_request|issues|repository|organization|member|team|installation|.*_alert)$"
      x-hub-signature-256: "^sha256=[a-f0-9]{64}$"
      user-agent: "^GitHub-Hookshot/[a-f0-9]+$"
```

## 📊 監視・メトリクス

### Prometheusメトリクス

#### カウンターメトリクス
```
# リクエスト総数
webhook_requests_total{event_type="push",status="success"} 1234

# エラー総数
webhook_errors_total{error_type="invalid_signature"} 56

# セキュリティイベント総数
webhook_security_events_total{event_type="sensitive_data_detected"} 3

# レート制限違反総数
webhook_rate_limit_exceeded_total{limit_type="per_ip"} 12
```

#### ヒストグラムメトリクス
```
# 処理時間
webhook_processing_duration_seconds_bucket{event_type="push",le="0.1"} 800
webhook_processing_duration_seconds_bucket{event_type="push",le="0.5"} 950
webhook_processing_duration_seconds_bucket{event_type="push",le="1.0"} 990
webhook_processing_duration_seconds_bucket{event_type="push",le="+Inf"} 1000

# ペイロードサイズ
webhook_payload_size_bytes_bucket{event_type="push",le="1000"} 600
webhook_payload_size_bytes_bucket{event_type="push",le="10000"} 900
webhook_payload_size_bytes_bucket{event_type="push",le="100000"} 980
webhook_payload_size_bytes_bucket{event_type="push",le="+Inf"} 1000
```

#### ゲージメトリクス
```
# アクティブ接続数
webhook_active_connections 45

# 処理中リクエスト数
webhook_processing_requests 3

# メモリ使用量
webhook_memory_usage_bytes 256000000

# CPU使用率
webhook_cpu_usage_percent 15.6
```

## 🔧 SDK・クライアントライブラリ

### Node.js/TypeScript SDK

#### インストール
```bash
npm install @sas-com/github-webhook-sdk
```

#### 使用例
```typescript
import { GitHubWebhookClient } from '@sas-com/github-webhook-sdk';

const client = new GitHubWebhookClient({
  baseUrl: 'https://webhook.sas-com.internal/api/v1',
  apiKey: 'your-api-key',
  timeout: 30000,
  retryConfig: {
    retries: 3,
    retryDelay: 1000
  }
});

// Webhook送信
const result = await client.sendWebhook({
  event: 'push',
  payload: pushPayload,
  signature: webhookSignature
});

console.log(result);
```

### Python SDK

#### インストール
```bash
pip install sas-com-github-webhook-sdk
```

#### 使用例
```python
from sas_com.github_webhook import GitHubWebhookClient

client = GitHubWebhookClient(
    base_url="https://webhook.sas-com.internal/api/v1",
    api_key="your-api-key",
    timeout=30,
    max_retries=3
)

# Webhook送信
result = await client.send_webhook(
    event="push",
    payload=push_payload,
    signature=webhook_signature
)

print(result)
```

### 共通機能

#### 自動リトライ機能
- **指数バックオフ**: 初期遅延1秒、最大16秒
- **ジッター**: ランダム遅延追加で負荷分散
- **リトライ対象**: 5xx エラー、ネットワークエラー
- **最大リトライ**: 3回

#### エラーハンドリング
- **型安全**: TypeScript完全対応
- **詳細エラー**: エラーコード・詳細メッセージ
- **構造化ログ**: JSON形式ログ出力
- **メトリクス**: 自動メトリクス送信

---

**更新履歴**:
- 2025-09-10: 初版作成 (OpenAPI 3.1準拠)
- セキュリティレビュー: 承認待ち
- 次回更新予定: 2025-12-10

**関連ドキュメント**:
- [GITHUB_WEBHOOK_SECURITY_GUIDE.md](./GITHUB_WEBHOOK_SECURITY_GUIDE.md)
- [WEBHOOK_DEPLOYMENT_GUIDE.md](./WEBHOOK_DEPLOYMENT_GUIDE.md)

**担当者**:
- API設計: GitHub管理チーム
- セキュリティレビュー: セキュリティチーム  
- 承認: CTO Office