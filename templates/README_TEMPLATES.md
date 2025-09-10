# GitHub Actions テンプレート利用ガイド

**エス・エー・エス株式会社**  
*GitHub Actions ワークフローテンプレートの利用方法*

## 概要

このディレクトリには、エス・エー・エス株式会社の標準的なGitHub Actionsワークフローテンプレートが含まれています。これらのテンプレートは、セキュリティ、パフォーマンス、運用効率を考慮して設計されています。

## 利用可能なテンプレート

### 1. Node.js CI/CD パイプライン (`nodejs-ci.yml`)

**適用対象**: Node.js、TypeScript、React、Next.js等のプロジェクト

**主な機能**:
- 複数バージョンでのテスト (Node.js 16, 18, 20)
- ESLint、Prettier による品質チェック
- セキュリティスキャン (npm audit, Snyk)
- Docker イメージビルド・プッシュ
- 段階的デプロイ (dev → staging → production)
- Slack通知連携

**使用方法**:
```bash
# テンプレートをコピー
cp templates/workflows/nodejs-ci.yml .github/workflows/

# プロジェクトに合わせて設定を調整
# - Node.jsバージョン
# - テストコマンド
# - ビルドコマンド
# - デプロイ先環境
```

**必要な設定**:
- **Secrets**: `SLACK_WEBHOOK_URL`, `SNYK_TOKEN`
- **Environment**: `development`, `staging`, `production`
- **パッケージマネージャー**: npm または yarn

### 2. Python CI/CD パイプライン (`python-ci.yml`)

**適用対象**: Python、Django、FastAPI、Flask等のプロジェクト

**主な機能**:
- 複数Pythonバージョンでのテスト (3.9, 3.10, 3.11, 3.12)
- Poetry による依存関係管理
- Black、isort、flake8、mypy による品質チェック
- セキュリティスキャン (Bandit、Safety、Semgrep)
- PyPI への自動パッケージ公開
- Docker イメージビルド

**使用方法**:
```bash
# テンプレートをコピー
cp templates/workflows/python-ci.yml .github/workflows/

# pyproject.toml または requirements.txt の確認
# Poetry設定の調整（必要に応じて）
```

**必要な設定**:
- **依存関係管理**: Poetry推奨
- **Secrets**: `SNYK_TOKEN`, `SLACK_WEBHOOK_URL`
- **PyPI公開**: PyPA trusted publishersの設定

### 3. Docker セキュリティスキャン (`docker-security.yml`)

**適用対象**: Dockerを使用するすべてのプロジェクト

**主な機能**:
- Dockerfileの静的解析 (Hadolint、Checkov)
- Docker Composeセキュリティチェック
- 脆弱性スキャン (Trivy、Snyk、Docker Scout)
- イメージサイズ・レイヤー分析
- セキュリティベストプラクティスチェック
- 定期的な脆弱性監視

**使用方法**:
```bash
# テンプレートをコピー
cp templates/workflows/docker-security.yml .github/workflows/

# Dockerfileの確認・調整
# スケジュール実行時間の調整
```

**特徴**:
- PRでの軽量スキャン
- 本番環境での包括的スキャン  
- セキュリティレポート自動生成

## テンプレートのカスタマイズ

### 1. 基本的なカスタマイズ項目

#### 共通設定
```yaml
# ワークフロー名（必須変更）
name: "Your Project CI/CD"

# トリガー条件
on:
  push:
    branches: [main, develop]  # プロジェクトのブランチ戦略に合わせて調整

# 環境変数
env:
  NODE_VERSION: '18.x'  # 使用するバージョンに合わせて調整
  PYTHON_VERSION: '3.11'
```

#### プロジェクト固有設定
```yaml
# テストコマンド（プロジェクトに応じて調整）
- name: Run tests
  run: |
    npm test              # Node.js
    # または
    poetry run pytest     # Python
    # または  
    mvn test              # Java

# ビルドコマンド
- name: Build application  
  run: |
    npm run build         # Node.js
    # または
    poetry build          # Python
    # または
    ./gradlew build       # Java/Kotlin
```

### 2. セキュリティ設定の調整

#### Secrets設定
```bash
# Repository Secrets (Settings > Secrets and variables > Actions)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SNYK_TOKEN=your-snyk-token
REGISTRY_PASSWORD=your-registry-password

# Environment Secrets (Settings > Environments > [環境名] > Secrets)  
DATABASE_URL=your-database-url
API_KEY=your-api-key
```

#### 権限設定
```yaml
# 最小権限の原則に従って調整
permissions:
  contents: read          # リポジトリ読み取り（基本）
  packages: write         # パッケージ公開時に必要
  security-events: write  # セキュリティスキャン結果アップロード時
  pull-requests: write    # PR へのコメント投稿時
```

### 3. 環境固有の設定

#### 開発環境 (dev)
```yaml
deploy-dev:
  environment:
    name: development
    url: https://dev.your-domain.com  # 実際のURL
  # リソース制限を緩く、迅速なデプロイ
```

#### ステージング環境 (staging)  
```yaml
deploy-staging:
  environment:
    name: staging
    url: https://staging.your-domain.com
  # 本番環境により近い設定、E2Eテスト実行
```

#### 本番環境 (production)
```yaml
deploy-production:
  environment:
    name: production  
    url: https://your-domain.com
  # 手動承認必須、最高レベルのセキュリティ
```

## ベストプラクティス

### 1. セキュリティ

```yaml
# ✅ Good: バージョン固定
uses: actions/checkout@v4.1.1

# ❌ Bad: 不安定なバージョン  
uses: actions/checkout@main

# ✅ Good: 最小権限
permissions:
  contents: read

# ❌ Bad: 過剰な権限
permissions: write-all
```

### 2. パフォーマンス

```yaml
# ✅ Good: キャッシュ活用
- name: Cache dependencies
  uses: actions/cache@v4
  with:
    path: node_modules
    key: ${{ hashFiles('package-lock.json') }}

# ✅ Good: 条件付き実行
- name: Deploy to production
  if: github.ref == 'refs/heads/main'
```

### 3. 可読性・保守性

```yaml
# ✅ Good: 明確な名前
name: "E-Commerce Platform CI/CD"

# ✅ Good: 適切なコメント
# Node.js 18.x を使用（LTSバージョン）
- name: Setup Node.js
  uses: actions/setup-node@v4
  with:
    node-version: '18.x'
```

## トラブルシューティング

### よくある問題と解決法

#### 1. ワークフローが実行されない
```bash
# YAML構文チェック
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"

# Actions有効化確認
# Settings > Actions > General > "Allow all actions and reusable workflows"
```

#### 2. 権限エラー
```yaml
# 必要な権限を permissions に追加
permissions:
  contents: read
  packages: write  # パッケージ公開時
  pull-requests: write  # PR操作時
```

#### 3. Secrets が見つからない
```bash
# Settings > Secrets and variables > Actions で確認
# Environment secrets の場合は Environment設定も確認
```

#### 4. タイムアウト
```yaml
# タイムアウト時間を延長
jobs:
  build:
    timeout-minutes: 30  # デフォルト: 360分

# または並列化でパフォーマンス向上
strategy:
  matrix:
    node-version: [16, 18, 20]
```

## 検証・テスト

### 1. 自動検証ツール

```bash
# テンプレートの検証
./scripts/actions-checker.sh
./scripts/workflow-validator.py .github/workflows/

# ローカルテスト（act使用）
act -n  # dry-run
act push  # 実際の実行シミュレーション
```

### 2. 段階的適用

1. **開発ブランチでテスト**: 最初は`develop`ブランチで動作確認
2. **制限付き本番適用**: 本番環境デプロイは手動承認から開始  
3. **監視強化**: 初期は詳細ログ・通知を有効化
4. **段階的最適化**: 安定後にパフォーマンス最適化実施

## サポート・連絡先

### 技術サポート
- **Email**: github@sas-com.com
- **対応時間**: 営業日 9:00-18:00 (JST)

### 緊急時
- **Level 1 (Critical)**: 即座に github@sas-com.com に連絡
- **Level 2-4**: レベルに応じたエスカレーション手順に従う

### リソース
- [GitHub Actions 設定チェックリスト](../GITHUB_ACTIONS_CHECKLIST.md)
- [運用手順書](../GITHUB_ACTIONS_OPERATIONS.md)  
- [エス・エー・エス GitHub運用ガイドライン](../GUIDELINES_DETAIL.md)

---

**更新履歴**
- 2025-09-10: 初版作成

*このガイドは、エス・エー・エス株式会社のGitHub Actions運用品質向上のための実践的なテンプレート利用ガイドです。プロジェクトの特性に応じてカスタマイズし、継続的な改善を実施してください。*