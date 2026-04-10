# ブランチ管理ルール

**エス・エー・エス株式会社**  
**SAS Git Flow対応ブランチ管理・保護設定**

## 1. ブランチ管理体系

### 1.1 ブランチ階層と責任範囲
```
main (本番環境ブランチ)
├── 責任者: リリースマネージャー
├── 用途: 本番環境デプロイ、タグ作成
└── 更新頻度: 週1-2回（定期リリース）

staging (ステージング環境ブランチ)
├── 責任者: QAリード、テックリード
├── 用途: 統合テスト、受入テスト
└── 更新頻度: 日次（開発完了機能の統合）

dev (開発環境ブランチ)
├── 責任者: テックリード、開発チーム
├── 用途: 機能統合、継続的テスト
└── 更新頻度: 複数回/日（機能完成時）
```

### 1.2 作業ブランチ分類

#### 1.2.1 機能開発ブランチ
```
feature/[component]/[feature-description]

命名規則:
- component: コンポーネント名（ケバブケース）
- feature-description: 機能説明（動詞-名詞形式）

プロジェクトタイプ別例:
✅ feature/auth/add-profile-validation        # API/モノリシック
✅ feature/ui/implement-dark-mode             # Web/モバイル
✅ feature/api/add-user-endpoints            # ライブラリ
✅ feature/docs/update-installation-guide    # ドキュメント
✅ feature/shared/update-common-utils        # 共通コンポーネント
❌ feature/UserAuth/AddProfile (大文字使用)
❌ feature/user/profile (component不明確)
```

#### 1.2.2 バグ修正ブランチ
```
bugfix/[component]/[issue-description]

プロジェクトタイプ別例:
✅ bugfix/frontend/fix-login-form-validation   # Web/モバイル
✅ bugfix/api/resolve-timeout-issue            # API/モノリシック
✅ bugfix/docs/fix-broken-links                # ドキュメント
✅ bugfix/build/fix-webpack-config             # ビルドシステム
❌ fix/frontend/login (prefixが不適切)
```

#### 1.2.3 緊急修正ブランチ
```
hotfix/[severity]/[component]/[issue-id]

severity レベル:
- critical: アプリケーション停止、データ消失、セキュリティ侵害
- high: 主要機能不全、パフォーマンス問題  
- medium: 一部機能の障害、UI/UX問題
- low: 軽微な不具合、ドキュメント修正

プロジェクトタイプ別例:
✅ hotfix/critical/auth/SAS-2024-001          # 認証系緊急修正
✅ hotfix/high/ui/performance-issue           # UIパフォーマンス問題
✅ hotfix/medium/docs/security-disclosure     # ドキュメント修正
```

#### 1.2.4 リリース準備ブランチ
```
release/v[major].[minor].[patch]

例:
✅ release/v2.1.0
✅ release/v1.15.3
❌ release/2.1.0 (vプレフィックスなし)
```

#### 1.2.5 統合テストブランチ
```
integration/[purpose]-[date]

例:
✅ integration/batch-deployment-20250910
✅ integration/performance-test-20250915
```

## 2. ブランチ保護設定

### 2.1 main ブランチ保護
```yaml
# GitHub Branch Protection Rules
main:
  protection:
    # 必須設定
    required_pull_request_reviews:
      required_approving_review_count: 2
      dismiss_stale_reviews: true
      require_code_owner_reviews: true
      require_last_push_approval: true
    
    # 必須ステータスチェック
    required_status_checks:
      strict: true
      contexts:
        - "ci/security-scan"
        - "ci/performance-test" 
        - "ci/integration-test"
        - "ci/dependency-check"
        - "ci/compliance-check"
    
    # アクセス制限
    restrictions:
      push:
        users: []
        teams: ["sas-admin-team"]
      merge:
        users: []
        teams: ["sas-release-team", "sas-admin-team"]
    
    # その他設定
    enforce_admins: true
    allow_force_pushes: false
    allow_deletions: false
    required_linear_history: true
```

### 2.2 staging ブランチ保護
```yaml
staging:
  protection:
    required_pull_request_reviews:
      required_approving_review_count: 1
      dismiss_stale_reviews: true
      require_code_owner_reviews: false
    
    required_status_checks:
      strict: true
      contexts:
        - "ci/unit-test"
        - "ci/integration-test"
        - "ci/security-scan"
        - "ci/lint"
    
    restrictions:
      push:
        teams: ["sas-develop-team", "sas-qa-team", "sas-admin-team"]
      merge:
        teams: ["sas-techlead-team", "sas-qa-team", "sas-admin-team"]
    
    enforce_admins: false
    allow_force_pushes: false
    allow_deletions: false
```

### 2.3 dev ブランチ保護
```yaml
dev:
  protection:
    required_pull_request_reviews:
      required_approving_review_count: 1
      dismiss_stale_reviews: false
      require_code_owner_reviews: false
    
    required_status_checks:
      strict: false
      contexts:
        - "ci/unit-test"
        - "ci/lint"
        - "ci/basic-security-check"
    
    restrictions:
      push:
        teams: ["sas-develop-team", "sas-admin-team"]
      merge:
        teams: ["sas-develop-team", "sas-admin-team"]
    
    enforce_admins: false
    allow_force_pushes: false
    allow_deletions: true
```

## 3. マージ戦略

### 3.1 環境別マージ方式

#### 3.1.1 main への マージ
```yaml
merge_strategy:
  method: "squash"
  reason: "履歴の簡潔性、リリースノート作成の容易さ"
  title_format: "[SERVICE] Brief description (#PR_NUMBER)"
  
example:
  title: "[user-service] Add profile validation feature (#123)"
  description: |
    ## Changes
    - Added email validation
    - Implemented phone number format check
    - Updated user registration flow
    
    ## Testing
    - Unit tests: 95% coverage
    - Integration tests: All pass
    - Performance test: <100ms response time
    
    ## Deployment Notes
    - Database migration required
    - Feature flag: profile_validation_v2
```

#### 3.1.2 staging への マージ
```yaml
merge_strategy:
  method: "merge_commit"
  reason: "トレーサビリティ確保、統合テスト結果の紐付け"
  auto_merge: false
  
merge_commit_message:
  format: "Merge feature/[service]/[feature] into staging"
  include_pr_info: true
```

#### 3.1.3 dev への マージ  
```yaml
merge_strategy:
  method: "squash"
  reason: "開発効率重視、クリーンな開発履歴"
  auto_merge: true
  conditions:
    - all_checks_pass: true
    - required_reviews: 1
```

### 3.2 コンフリクト解決ルール

#### 3.2.1 自動解決可能なケース
```bash
# ドキュメントファイル（Markdown）
# 設定ファイル（非機能部分）
# テストファイル（異なるテストケース）

# 自動マージツールの使用
git config merge.ours.driver true
echo "*.md merge=ours" >> .gitattributes
```

#### 3.2.2 手動解決が必要なケース
```bash
# ビジネスロジック
# データベーススキーマ
# API仕様
# 共通ライブラリのインターフェース

# 解決手順
1. git checkout feature/my-branch
2. git fetch origin
3. git rebase origin/target-branch
4. # コンフリクト解決
5. git add .
6. git rebase --continue
7. git push --force-with-lease origin feature/my-branch
```

## 4. コードオーナー設定

### 4.1 CODEOWNERS ファイル（プロジェクトタイプ別）
```bash
# /CODEOWNERS

# Global rules
* @sas-com/sas-admin-team

# Web/Mobile Application
/src/components/ @sas-com/sas-product-frontend-team
/src/pages/ @sas-com/sas-product-frontend-team
/public/ @sas-com/sas-product-frontend-team
/mobile/ @sas-com/sas-mobile-team

# API/Backend
/src/api/ @sas-com/sas-product-backend-team
/src/controllers/ @sas-com/sas-product-backend-team
/src/services/ @sas-com/sas-product-backend-team
/src/models/ @sas-com/sas-product-backend-team

# Library/Package
/lib/ @sas-com/sas-library-team
/dist/ @sas-com/sas-library-team
package.json @sas-com/sas-library-team

# Microservices (if applicable)
/services/ @sas-com/sas-service-team
/microservices/ @sas-com/sas-service-team

# Shared/Common
/shared/ @sas-com/sas-platform-team
/common/ @sas-com/sas-platform-team
/utils/ @sas-com/sas-platform-team

# Configuration & Infrastructure
/config/ @sas-com/sas-devops-team
/infrastructure/ @sas-com/sas-devops-team
/k8s/ @sas-com/sas-devops-team
/.github/ @sas-com/sas-admin-team
/docker/ @sas-com/sas-devops-team

# Database
/migrations/ @sas-com/sas-database-team
/schemas/ @sas-com/sas-database-team
/sql/ @sas-com/sas-database-team

# Testing
/tests/ @sas-com/sas-qa-team
/e2e/ @sas-com/sas-qa-team
/__tests__/ @sas-com/sas-qa-team

# Security
/security/ @sas-com/sas-security-team
/secrets/ @sas-com/sas-security-team

# Documentation
/docs/ @sas-com/sas-techwriter-team
/README.md @sas-com/sas-techwriter-team
/CHANGELOG.md @sas-com/sas-techwriter-team
```

### 4.2 チーム権限マトリクス
```yaml
teams:
  sas-admin-team:
    permissions: ["admin"]
    repositories: ["all"]
    
  sas-release-team:
    permissions: ["write"]
    branches: ["main", "staging"]
    
  sas-techlead-team:
    permissions: ["write"] 
    branches: ["staging", "dev"]
    
  sas-develop-team:
    permissions: ["write"]
    branches: ["dev", "feature/*", "bugfix/*"]
    
  sas-qa-team:
    permissions: ["read", "write"]
    branches: ["staging", "dev"]
    focus: ["testing", "quality-assurance"]
```

## 5. 自動化設定

### 5.1 ブランチ自動作成
```yaml
# .github/workflows/auto-branch-creation.yml
name: Auto Branch Creation

on:
  issues:
    types: [labeled]

jobs:
  create-branch:
    if: contains(github.event.label.name, 'feature') || contains(github.event.label.name, 'bug')
    runs-on: ubuntu-latest
    steps:
      - name: Create Branch
        run: |
          ISSUE_NUMBER=${{ github.event.issue.number }}
          ISSUE_TITLE="${{ github.event.issue.title }}"
          LABEL_NAME="${{ github.event.label.name }}"
          
          # ブランチ名生成
          BRANCH_PREFIX=""
          if [[ "$LABEL_NAME" == *"feature"* ]]; then
            BRANCH_PREFIX="feature"
          elif [[ "$LABEL_NAME" == *"bug"* ]]; then
            BRANCH_PREFIX="bugfix"
          fi
          
          SERVICE_NAME=$(echo "$ISSUE_TITLE" | grep -oP '\[.*?\]' | tr -d '[]')
          DESCRIPTION=$(echo "$ISSUE_TITLE" | sed 's/\[.*\] //' | tr ' ' '-' | tr '[:upper:]' '[:lower:]')
          
          BRANCH_NAME="${BRANCH_PREFIX}/${SERVICE_NAME}/${DESCRIPTION}"
          
          git checkout -b "$BRANCH_NAME"
          git push origin "$BRANCH_NAME"
```

### 5.2 ブランチ自動削除
```yaml
# .github/workflows/cleanup-branches.yml
name: Cleanup Merged Branches

on:
  pull_request:
    types: [closed]

jobs:
  cleanup:
    if: github.event.pull_request.merged == true
    runs-on: ubuntu-latest
    steps:
      - name: Delete merged branch
        run: |
          BRANCH_NAME="${{ github.event.pull_request.head.ref }}"
          if [[ "$BRANCH_NAME" != "main" && "$BRANCH_NAME" != "staging" && "$BRANCH_NAME" != "dev" ]]; then
            git push origin --delete "$BRANCH_NAME"
          fi
```

## 6. 監視・レポート

### 6.1 ブランチヘルススコア
```yaml
# branch-health-metrics.yaml
metrics:
  branch_age:
    warning_threshold: 14 # days
    critical_threshold: 30 # days
    
  merge_frequency:
    target: "daily"
    measurement: "merges per day to main"
    
  review_time:
    target: "< 24 hours"
    measurement: "PR creation to approval"
    
  conflict_rate:
    target: "< 10%"
    measurement: "PRs with merge conflicts"
```

### 6.2 自動レポート生成
```yaml
# .github/workflows/branch-report.yml
name: Weekly Branch Report

on:
  schedule:
    - cron: '0 9 * * 1' # 毎週月曜日 9:00

jobs:
  generate-report:
    runs-on: ubuntu-latest
    steps:
      - name: Generate Branch Health Report
        run: |
          # 古いブランチの検出
          git for-each-ref --format='%(refname:short) %(committerdate)' refs/remotes/origin/ | \
            while read branch date; do
              if [[ $(date -d "$date" +%s) -lt $(date -d "30 days ago" +%s) ]]; then
                echo "🚨 Old branch: $branch ($date)"
              fi
            done
          
          # マージ頻度の計算
          MERGE_COUNT=$(git log --oneline --merges --since="7 days ago" | wc -l)
          echo "📊 Merges this week: $MERGE_COUNT"
          
          # コンフリクト率の計算
          # (実装は実際のデータソースに依存)
```

## 7. トラブルシューティング

### 7.1 よくある問題

#### 7.1.1 ブランチ保護設定の確認
```bash
# CLI での確認
gh api repos/:owner/:repo/branches/main/protection | jq .

# 設定の修正
gh api -X PUT repos/:owner/:repo/branches/main/protection \
  --input protection-config.json
```

#### 7.1.2 権限不足エラー
```bash
# エラー例
remote: Permission to sas-com/service-name.git denied to user.
fatal: unable to access 'https://github.com/sas-com/service-name.git/': The requested URL returned error: 403

# 解決策
1. チーム所属確認: GitHub組織のTeam設定を確認
2. ブランチ権限確認: Branch protection rulesを確認
3. 2FA設定確認: Two-factor authenticationの有効化
```

#### 7.1.3 マージコンフリクトの予防
```bash
# 定期的な同期（推奨）
git checkout feature/my-feature
git fetch origin
git rebase origin/dev

# リベース前の安全確認
git log --oneline origin/dev..HEAD
git diff origin/dev...HEAD
```

## 8. 移行・導入手順

### 8.1 既存プロジェクトの移行
```bash
# 1. 現在のブランチ構造の分析
git branch -r | grep -v "origin/HEAD"

# 2. 不要ブランチの特定
git for-each-ref --format='%(refname:short) %(committerdate)' refs/remotes/origin/ | \
  awk '$2 < "'$(date -d '3 months ago' '+%Y-%m-%d')'"'

# 3. ブランチのリネーム（必要に応じて）
git branch -m old-branch-name new-branch-name
git push origin -u new-branch-name
git push origin --delete old-branch-name
```

### 8.2 チーム教育チェックリスト
```
□ SAS Flow概要の説明会実施
□ ブランチ命名規則の周知
□ マージ戦略の理解確認
□ 緊急対応フローの訓練
□ 権限・責任範囲の明確化
□ ツール操作の実習
□ トラブルシューティング演習
```

---

**更新履歴**
- 2025-09-10: 初版作成（v1.0.0）

**承認者**: GitHub管理チーム  
**関連ドキュメント**: [SAS_FLOW_SPECIFICATION.md](/home/kurosawa/github-guidelines/SAS_FLOW_SPECIFICATION.md)