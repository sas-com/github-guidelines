# GitHub Actions 運用手順書

**エス・エー・エス株式会社**  
*GitHub Actions の実践的な運用ガイド*

## 目次

1. [概要](#概要)
2. [新規ワークフロー作成手順](#新規ワークフロー作成手順)
3. [既存ワークフロー診断手順](#既存ワークフロー診断手順)
4. [トラブルシューティングガイド](#トラブルシューティングガイド)
5. [セキュリティ対応手順](#セキュリティ対応手順)
6. [パフォーマンス最適化](#パフォーマンス最適化)
7. [監視・アラート設定](#監視アラート設定)
8. [緊急時対応](#緊急時対応)

---

## 概要

### 適用範囲
- **現在の環境**: dev環境のみ運用中
- **将来の計画**: main/staging/dev の3環境構成
- **対象技術**: JavaScript/TypeScript、Python、Java、Go、Docker等

### 基本原則
1. **セキュリティファースト**: すべての設定でセキュリティを最優先
2. **最小権限の原則**: 必要最小限の権限のみ付与
3. **自動化の徹底**: 手動作業を最小限に抑制
4. **監視・可視化**: すべての処理を監視・記録
5. **継続的改善**: 定期的な見直しと最適化

---

## 新規ワークフロー作成手順

### 1. 事前準備

#### 1.1 要件定義
```bash
# 要件確認チェックリスト
echo "新規ワークフロー要件確認"
echo "========================="
echo "□ プロジェクト名と技術スタック"
echo "□ デプロイ対象環境（dev/staging/production）"
echo "□ 実行トリガー（push/PR/schedule/manual）"
echo "□ 必要な権限とSecrets"
echo "□ 外部サービス連携（Slack、監視ツール等）"
echo "□ 実行時間の予想とリソース要件"
echo "□ コンプライアンス要件"
```

#### 1.2 テンプレート選択
```bash
# 利用可能なテンプレートを確認
ls -la templates/workflows/
echo ""
echo "利用可能なテンプレート:"
echo "- nodejs-ci.yml: Node.js プロジェクト用"
echo "- python-ci.yml: Python プロジェクト用"  
echo "- docker-security.yml: Docker セキュリティスキャン"
echo "- 基本テンプレートから技術スタックに応じて選択"
```

### 2. ワークフロー実装

#### 2.1 基本構造の作成
```yaml
# .github/workflows/new-workflow.yml の基本構造
name: "明確で識別しやすいワークフロー名"

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  workflow_dispatch:

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}

permissions:
  contents: read  # 最小権限から開始

env:
  # グローバル環境変数

jobs:
  # ジョブ定義
```

#### 2.2 セキュリティ設定
```bash
# セキュリティチェックリストの適用
./scripts/actions-checker.sh .

# Python検証ツールでの詳細チェック
./scripts/workflow-validator.py .github/workflows/new-workflow.yml
```

#### 2.3 テスト実行
```bash
# ローカルでのワークフロー検証
act -n  # dry-run mode

# Git管理への追加
git add .github/workflows/new-workflow.yml
git commit -m "feat(workflow): 新規ワークフローを追加

- プロジェクト用CI/CDパイプラインを実装
- セキュリティスキャンを統合
- 段階的デプロイメントを設定"
```

### 3. 段階的デプロイメント

#### 3.1 開発環境での検証
1. 開発ブランチでプッシュして動作確認
2. ログとメトリクスを監視
3. セキュリティスキャン結果を確認
4. 実行時間とリソース使用量を測定

#### 3.2 本番環境への適用
```bash
# 本番適用前のチェックリスト確認
echo "本番適用前チェックリスト"
echo "========================"
echo "□ 開発環境での十分なテスト完了"
echo "□ セキュリティスキャン通過"
echo "□ パフォーマンス要件満足"
echo "□ ドキュメント作成完了"
echo "□ 関係者レビュー完了"
echo "□ 緊急時停止手順確認"
```

---

## 既存ワークフロー診断手順

### 1. 定期診断の実行

#### 1.1 自動診断スクリプトの実行
```bash
# 包括的なチェックの実行
./scripts/actions-checker.sh --verbose --format json --output check-results.json

# Python検証ツールでの詳細分析
./scripts/workflow-validator.py --format json --output validation-results.json
```

#### 1.2 診断結果の分析
```bash
# 診断結果サマリー表示
echo "診断結果サマリー"
echo "================"

# Critical/Highレベル問題の抽出
grep -E "(CRITICAL|HIGH)" check-results.json | wc -l

# セキュリティ関連問題の詳細確認
jq '.issues[] | select(.category == "security")' validation-results.json
```

### 2. 問題対応の優先順位

#### 2.1 緊急対応（Critical）
- セキュリティ脆弱性
- 本番環境への影響
- データ漏洩リスク

#### 2.2 高優先度（High）
- パフォーマンス問題
- 運用効率の著しい低下
- コンプライアンス違反

#### 2.3 中優先度（Medium）
- ベストプラクティス違反
- 保守性の問題
- コスト最適化

### 3. 改善計画の策定

#### 3.1 改善作業計画
```bash
# 改善計画テンプレート
cat > improvement-plan.md << 'EOF'
# ワークフロー改善計画

## 現状分析
- 診断日時: $(date)
- 発見問題数: X件（Critical: X, High: X, Medium: X, Low: X）

## 優先対応項目
1. [Critical] セキュリティ脆弱性の修正
2. [High] パフォーマンス最適化
3. [Medium] ベストプラクティス適用

## 実施計画
- Week 1: Critical問題対応
- Week 2: High問題対応  
- Week 3: Medium問題対応・テスト
- Week 4: レビュー・本番適用

## 成功指標
- セキュリティスコア: 95%以上
- 実行時間: 20%短縮
- 失敗率: 5%以下
EOF
```

---

## トラブルシューティングガイド

### 1. よくある問題と対処法

#### 1.1 ワークフローが開始されない
**症状**: プッシュ・PRしてもワークフローが実行されない

**原因と対処法**:
```bash
# 1. YAML構文エラーのチェック
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/workflow.yml'))"

# 2. トリガー条件の確認
grep -A 10 "^on:" .github/workflows/workflow.yml

# 3. Actions権限の確認
echo "Settings > Actions > General で Actions が有効化されているか確認"

# 4. ブランチ保護ルールとの競合確認
echo "Settings > Branches でブランチ保護設定を確認"
```

#### 1.2 権限エラー
**症状**: `Permission denied` または `insufficient permissions`

**対処法**:
```yaml
# permissions セクションの見直し
permissions:
  contents: read        # リポジトリ読み取り
  packages: write       # パッケージ書き込み
  pull-requests: write  # PR操作
  security-events: write # セキュリティイベント
```

#### 1.3 Secrets が利用できない
**症状**: `Secret is not defined` エラー

**対処法**:
```bash
# 1. Secretsの存在確認
echo "Settings > Secrets and variables > Actions で確認"

# 2. 環境別Secretsの確認
echo "Environment secrets の設定確認"

# 3. 大文字小文字の確認
echo "Secret名は大文字小文字を区別"

# 4. 使用方法の確認
echo '${{ secrets.SECRET_NAME }} の形式で参照'
```

#### 1.4 タイムアウトエラー
**症状**: `The job was canceled because it exceeded the maximum execution time`

**対処法**:
```yaml
# 1. タイムアウト時間の調整
jobs:
  job_name:
    timeout-minutes: 30  # デフォルトは360分

# 2. 並列実行の活用
strategy:
  matrix:
    node-version: [16, 18, 20]

# 3. キャッシュの活用
- name: Cache dependencies
  uses: actions/cache@v4
  with:
    path: node_modules
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
```

### 2. デバッグ手法

#### 2.1 詳細ログの有効化
```yaml
# デバッグログの有効化
env:
  ACTIONS_RUNNER_DEBUG: true
  ACTIONS_STEP_DEBUG: true
```

#### 2.2 中間結果の出力
```yaml
# デバッグ用の中間出力
- name: Debug Environment
  run: |
    echo "Current directory: $(pwd)"
    echo "Environment variables:"
    env | sort
    echo "File list:"
    ls -la
```

#### 2.3 条件付きデバッグ
```yaml
- name: Debug on failure
  if: failure()
  run: |
    echo "Workflow failed. Debugging information:"
    cat log-file.txt
    docker ps -a
    df -h
```

---

## セキュリティ対応手順

### 1. セキュリティインシデント対応

#### 1.1 緊急時対応フロー
```bash
# 1. インシデント確認
echo "セキュリティインシデント対応開始: $(date)"

# 2. 影響範囲の特定
git log --oneline --since="24 hours ago" .github/workflows/

# 3. 緊急停止（必要に応じて）
# リポジトリの Actions を一時無効化

# 4. 関係者への通知
echo "緊急連絡先: github@sas-com.com"
```

#### 1.2 脆弱性対応
```bash
# 1. 脆弱性スキャン実行
./scripts/workflow-validator.py --config security-strict.yml

# 2. 脆弱なアクションの特定
grep -r "uses:" .github/workflows/ | grep -E "@(main|master|v[0-9]+$)"

# 3. アクションの更新
# バージョンを具体的なタグに固定
# 例: actions/checkout@v4.1.1
```

### 2. Secrets管理

#### 2.1 Secrets監査
```bash
# 1. Secrets一覧の確認
echo "設定済みSecrets監査"
echo "Repository Secrets: Settings > Secrets and variables > Actions"
echo "Environment Secrets: Settings > Environments > [環境名] > Secrets"

# 2. 不要なSecretsの削除
echo "未使用Secretsの特定と削除"

# 3. Secrets更新
echo "定期的なSecrets更新（90日サイクル推奨）"
```

#### 2.2 Secrets使用規約
```yaml
# 安全なSecrets使用例
- name: Deploy with secrets
  run: |
    # 直接的なecho等での出力は禁止
    # echo "${{ secrets.API_KEY }}"  # NG
    
    # マスクされた形での使用
    curl -H "Authorization: Bearer ${{ secrets.API_KEY }}" https://api.example.com
  env:
    API_KEY: ${{ secrets.API_KEY }}  # 環境変数として渡すことを推奨
```

---

## パフォーマンス最適化

### 1. 実行時間の最適化

#### 1.1 並列実行の活用
```yaml
# Matrix strategy による並列実行
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
    node-version: [16, 18, 20]
  fail-fast: false  # 一つが失敗しても他を継続

# Job レベルでの並列実行
jobs:
  test:
    # 独立したテストジョブ
  build:
    needs: test
    # テスト完了後の並列ビルド
  deploy-dev:
    needs: build
    if: github.ref == 'refs/heads/develop'
  deploy-staging:
    needs: build
    if: github.ref == 'refs/heads/main'
```

#### 1.2 キャッシュ戦略
```yaml
# Node.js プロジェクトのキャッシュ
- name: Cache Node.js modules
  uses: actions/cache@v4
  with:
    path: |
      ~/.npm
      node_modules
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-node-

# Python プロジェクトのキャッシュ
- name: Cache pip packages
  uses: actions/cache@v4
  with:
    path: |
      ~/.cache/pip
      .venv
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

# Docker レイヤーキャッシュ
- name: Build with cache
  uses: docker/build-push-action@v5
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

#### 1.3 不要な処理の削除
```yaml
# 条件付き実行による最適化
- name: Skip on documentation only changes
  if: |
    !contains(github.event.head_commit.message, '[docs]') &&
    !contains(join(github.event.commits.*.modified, ' '), 'README.md')
  run: npm test

# パス制限による最適化
on:
  push:
    paths-ignore:
      - '**.md'
      - 'docs/**'
      - '.gitignore'
```

### 2. コスト最適化

#### 2.1 実行時間監視
```bash
# 月次コスト分析スクリプト
cat > analyze-costs.sh << 'EOF'
#!/bin/bash
echo "GitHub Actions コスト分析"
echo "========================="

# ワークフロー実行時間の分析
echo "平均実行時間 Top 5:"
# GitHub API を使用して実行時間データを取得・分析

echo ""
echo "コスト最適化推奨事項:"
echo "- 長時間実行ワークフローの並列化"
echo "- キャッシュ効率の改善"  
echo "- 不要な実行の削減"
EOF

chmod +x analyze-costs.sh
```

#### 2.2 リソース効率化
```yaml
# セルフホストランナーの活用（大規模プロジェクト）
runs-on: self-hosted

# 条件付きジョブ実行
deploy-production:
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'
  # 本番デプロイは条件を厳密に
```

---

## 監視・アラート設定

### 1. 監視項目

#### 1.1 成功率監視
```bash
# 週次成功率レポート
cat > weekly-report.sh << 'EOF'
#!/bin/bash
echo "GitHub Actions 週次レポート"
echo "========================="
echo "期間: $(date -d '7 days ago' '+%Y-%m-%d') - $(date '+%Y-%m-%d')"
echo ""

# 成功率統計
echo "ワークフロー成功率:"
echo "- CI/CD Pipeline: 95.2% (目標: >95%)"
echo "- Security Scan: 98.1% (目標: >98%)"
echo "- Deployment: 92.3% (目標: >90%)"
echo ""

echo "改善が必要な項目:"
echo "- Deployment成功率の向上"
EOF
```

#### 1.2 パフォーマンス監視
```yaml
# 実行時間アラート
- name: Performance Check
  run: |
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    if [ $DURATION -gt 1800 ]; then  # 30分超過
      echo "::warning::Long execution time: ${DURATION}s"
    fi
  env:
    START_TIME: ${{ steps.start.outputs.timestamp }}
```

### 2. 通知設定

#### 2.2 Slack通知設定
```yaml
# 失敗時の通知
- name: Notify failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: failure
    channel: '#ci-cd-alerts'
    text: |
      🚨 ワークフロー実行失敗
      
      リポジトリ: ${{ github.repository }}
      ブランチ: ${{ github.ref_name }}
      実行者: ${{ github.actor }}
      エラー詳細: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

#### 2.3 メール通知
```yaml
# 本番デプロイ完了通知
- name: Email notification
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.sas-com.com
    server_port: 587
    username: ${{ secrets.MAIL_USERNAME }}
    password: ${{ secrets.MAIL_PASSWORD }}
    subject: "[本番デプロイ完了] ${{ github.repository }}"
    body: |
      本番環境へのデプロイが完了しました。
      
      デプロイ内容: ${{ github.event.head_commit.message }}
      デプロイ時刻: ${{ steps.deploy.outputs.timestamp }}
    to: deployments@sas-com.com
    from: noreply@sas-com.com
```

---

## 緊急時対応

### 1. 緊急度レベル

#### Level 1 (Critical) - 即座対応
- 本番環境の完全停止
- セキュリティインシデント
- データ損失リスク

#### Level 2 (High) - 1時間以内  
- 本番環境の部分停止
- 重要機能の障害
- セキュリティ脆弱性発見

#### Level 3 (Medium) - 4時間以内
- 開発環境の問題
- パフォーマンス劣化
- 軽微な機能障害

#### Level 4 (Low) - 翌営業日
- ドキュメント更新
- 軽微な改善要望
- 一般的な質問

### 2. エスカレーション手順

#### 2.1 連絡フロー
```bash
# 緊急時連絡スクリプト
cat > emergency-contact.sh << 'EOF'
#!/bin/bash
LEVEL=$1
MESSAGE=$2

echo "緊急時対応開始: $(date)"
echo "レベル: $LEVEL"
echo "内容: $MESSAGE"

case $LEVEL in
  "L1"|"L2")
    echo "即座にSAS Github管理チーム (github@sas-com.com) に連絡"
    # 実際の環境では自動メール送信等を実装
    ;;
  "L3")
    echo "4時間以内にSAS Github管理チーム (github@sas-com.com) に連絡"
    ;;
  "L4")
    echo "翌営業日にSAS Github管理チーム (github@sas-com.com) に連絡"
    ;;
esac
EOF
```

#### 2.2 緊急停止手順
```bash
# ワークフロー緊急停止
cat > emergency-stop.sh << 'EOF'
#!/bin/bash
echo "GitHub Actions 緊急停止手順"
echo "========================="
echo "1. GitHub リポジトリ > Settings > Actions > General"
echo "2. 'Disable Actions for this repository' を選択"
echo "3. 実行中のワークフローを手動キャンセル"
echo "4. インシデント対応チームに状況報告"
echo ""
echo "停止理由を記録:"
read -p "停止理由: " REASON
echo "停止時刻: $(date)" >> emergency-log.txt
echo "停止理由: $REASON" >> emergency-log.txt
EOF
```

### 3. 復旧手順

#### 3.1 段階的復旧
```bash
# 復旧確認チェックリスト
cat > recovery-checklist.sh << 'EOF'
#!/bin/bash
echo "GitHub Actions 復旧チェックリスト"
echo "==============================="
echo ""
echo "□ 根本原因の特定・修正完了"
echo "□ セキュリティリスクの評価完了"
echo "□ テスト環境での動作確認完了"
echo "□ 関係者への復旧計画通知完了"
echo "□ 監視体制の強化準備完了"
echo "□ ロールバック手順の準備完了"
echo ""
echo "すべて確認後、段階的に復旧を開始"
EOF
```

#### 3.2 事後対応
```markdown
# インシデント後レビューテンプレート

## インシデント概要
- 発生日時: 
- 検知日時: 
- 復旧日時: 
- 影響範囲: 
- インシデントレベル: 

## 根本原因
- 直接原因: 
- 根本原因: 
- 寄与要因: 

## 対応内容
- 緊急対応: 
- 根本修正: 
- 再発防止策: 

## 学習事項
- 改善が必要な点: 
- 手順の見直し: 
- ツール・監視の改善: 

## アクションアイテム
- [ ] 項目1 (担当者: XXX, 期限: YYYY-MM-DD)
- [ ] 項目2 (担当者: XXX, 期限: YYYY-MM-DD)
```

---

## 付録

### A. 便利なコマンド集

```bash
# GitHub Actions 関連のよく使うコマンド
alias ga-check='./scripts/actions-checker.sh'
alias ga-validate='./scripts/workflow-validator.py'
alias ga-logs='gh run list --limit 10'
alias ga-view='gh run view --log'

# ワークフロー実行状況確認
gh run list --workflow="CI/CD Pipeline" --limit 5

# 失敗したワークフローのログ確認
gh run view $(gh run list --status failure --limit 1 --json databaseId --jq '.[0].databaseId') --log

# Secrets一覧表示（名前のみ）
gh secret list

# 環境一覧表示
gh api repos/:owner/:repo/environments --jq '.environments[].name'
```

### B. 設定ファイルテンプレート

#### B.1 Dependabot設定
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
      timezone: "Asia/Tokyo"
    open-pull-requests-limit: 5
    reviewers:
      - "sas-devops-team"
    assignees:
      - "sas-devops-team"
    commit-message:
      prefix: "chore(deps)"
      include: "scope"
```

#### B.2 Issue/PR テンプレート
```markdown
<!-- .github/ISSUE_TEMPLATE/github-actions-issue.md -->
---
name: GitHub Actions 問題報告
about: ワークフローの問題を報告
title: '[Actions] '
labels: 'github-actions, bug'
assignees: 'sas-devops-team'
---

## 問題の概要
<!-- 発生している問題を簡潔に記述 -->

## 影響を受けるワークフロー
- [ ] CI/CD Pipeline
- [ ] Security Scan
- [ ] Deploy

## 発生環境
- [ ] dev
- [ ] staging  
- [ ] production

## 再現手順
1. 
2. 
3. 

## 期待される動作


## 実際の動作


## ログ・エラーメッセージ
```console

```

## その他の情報
<!-- スクリーンショット、関連するコミット等 -->
```

---

**更新履歴**
- 2025-09-10: 初版作成

**関連ドキュメント**
- [GitHub Actions設定チェックリスト](./GITHUB_ACTIONS_CHECKLIST.md)
- [エス・エー・エス GitHub運用ガイドライン](./GUIDELINES_DETAIL.md)

---

*本手順書は、エス・エー・エス株式会社のGitHub Actions運用における実践的なガイドラインです。定期的な見直しと改善を実施し、最新の状態を維持してください。*