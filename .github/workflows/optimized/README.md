# GitHub Actions 最適化済みワークフローテンプレート

**エス・エー・エス株式会社**  
*最終更新: 2025-09-10*

## 概要

このディレクトリには、GitHub Actionsのパフォーマンスを最大化し、コストを最小化するための最適化済みワークフローテンプレートが含まれています。

## 🎯 目標と成果

### 達成目標
- **実行時間**: 30-50%削減
- **コスト**: 40%削減
- **キャッシュヒット率**: 85%以上
- **並列処理効率**: 75%以上
- **品質**: 現状維持または向上

### 期待される成果
- 開発者の待ち時間削減
- CI/CDコストの大幅削減
- デプロイ頻度の向上
- フィードバックループの高速化

## 📁 ファイル構成

```
.github/workflows/optimized/
├── README.md                    # このファイル
├── ci-cd-optimized.yml         # 最適化済みCI/CDパイプライン
├── cache-optimized.yml          # キャッシュ戦略特化ワークフロー
└── environment-configs.yml      # 環境別最適化設定
```

## 🚀 クイックスタート

### 1. 基本的な使い方

既存のワークフローを最適化済みテンプレートで置き換えます：

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main, dev]
  pull_request:

jobs:
  ci:
    uses: ./.github/workflows/optimized/ci-cd-optimized.yml
    secrets: inherit
```

### 2. キャッシュ最適化の適用

```yaml
# プロジェクトに応じたキャッシュ戦略を適用
jobs:
  build:
    uses: ./.github/workflows/optimized/cache-optimized.yml
    with:
      node_version: '18'
      python_version: '3.11'
```

### 3. 環境別設定の使用

```yaml
# 環境に応じた最適化設定を自動適用
jobs:
  deploy:
    uses: ./.github/workflows/optimized/environment-configs.yml
    with:
      environment: ${{ github.ref == 'refs/heads/main' && 'production' || 'dev' }}
```

## 📊 パフォーマンス監視

### ワークフロー分析ツールの実行

```bash
# パフォーマンス分析
python scripts/performance-monitor/workflow-analyzer.py \
  --token $GITHUB_TOKEN \
  --owner sas-com \
  --repo my-repo \
  --output performance-report.html

# コスト追跡
./scripts/cost-analyzer/github-actions-cost-tracker.sh \
  -o sas-com \
  -r my-repo \
  -t $GITHUB_TOKEN \
  -f html \
  -s cost-report.html
```

## 🔧 カスタマイズガイド

### 並列処理の調整

```yaml
strategy:
  matrix:
    # プロジェクトサイズに応じて調整
    shard: [1, 2, 3, 4]  # 小規模: 2, 中規模: 4, 大規模: 8
  max-parallel: 4  # 同時実行数の制限
```

### キャッシュキーの最適化

```yaml
- name: Custom Cache Strategy
  uses: actions/cache@v3
  with:
    path: |
      ~/.npm
      node_modules
      # プロジェクト固有のキャッシュパスを追加
      .next/cache
      dist
    key: ${{ runner.os }}-${{ env.CACHE_VERSION }}-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-${{ env.CACHE_VERSION }}-
```

### 環境変数の設定

```yaml
env:
  # グローバル設定
  NODE_VERSION: '18'
  CACHE_VERSION: v1
  ENABLE_CACHE: true
  
  # 環境別設定
  ${{ github.ref == 'refs/heads/main' && 'PRODUCTION=true' || 'DEVELOPMENT=true' }}
```

## 📈 最適化のベストプラクティス

### 1. Fail Fast戦略
```yaml
# 軽量チェックを先に実行
jobs:
  quick-checks:
    runs-on: ubuntu-latest
    steps:
      - name: Syntax Check
        run: npm run lint:quick
      
  full-tests:
    needs: quick-checks
    # 続きの処理...
```

### 2. 差分ベース実行
```yaml
# 変更されたファイルのみ処理
- name: Detect Changes
  uses: dorny/paths-filter@v2
  id: changes
  with:
    filters: |
      frontend:
        - 'src/frontend/**'
      backend:
        - 'src/backend/**'
```

### 3. 条件付き実行
```yaml
# 必要な場合のみ実行
- name: Deploy
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'
  run: npm run deploy
```

## 🔍 トラブルシューティング

### よくある問題と解決方法

| 問題 | 原因 | 解決方法 |
|------|------|----------|
| キャッシュミス頻発 | キーが厳密すぎる | restore-keysを追加 |
| 並列実行エラー | リソース競合 | max-parallelを減らす |
| タイムアウト | 処理が重い | タイムアウト値を増やすかジョブを分割 |
| コスト超過 | 無駄な実行 | concurrencyで重複実行を防ぐ |

### デバッグモード

```yaml
# デバッグ情報を有効化
env:
  ACTIONS_RUNNER_DEBUG: true
  ACTIONS_STEP_DEBUG: true
```

## 📊 メトリクスとKPI

### 監視すべき指標

1. **実行時間メトリクス**
   - 平均ワークフロー実行時間
   - P95実行時間
   - 最長実行ステップ

2. **コストメトリクス**
   - 月間使用分数
   - 環境別コスト
   - ランナータイプ別使用率

3. **品質メトリクス**
   - テストカバレッジ
   - ビルド成功率
   - デプロイ頻度

### レポート生成

```bash
# 週次レポート
./generate-weekly-report.sh

# 月次コスト分析
./monthly-cost-analysis.sh
```

## 🔄 継続的改善

### 定期レビュープロセス

1. **週次**: ワークフロー実行時間の確認
2. **隔週**: キャッシュヒット率の分析
3. **月次**: コスト最適化の評価
4. **四半期**: 全体的な最適化戦略の見直し

### 改善提案の実装

1. メトリクスに基づく改善点の特定
2. 小規模な変更から段階的に適用
3. A/Bテストによる効果測定
4. 成功パターンの横展開

## 📚 関連ドキュメント

- [CICD_PERFORMANCE_OPTIMIZATION_GUIDE.md](../../../CICD_PERFORMANCE_OPTIMIZATION_GUIDE.md) - 詳細な最適化ガイド
- [GITHUB_ACTIONS_OPERATIONS.md](../../../GITHUB_ACTIONS_OPERATIONS.md) - 運用ガイド
- [パフォーマンス監視ツール](../../../scripts/performance-monitor/) - 監視スクリプト
- [コスト管理ツール](../../../scripts/cost-analyzer/) - コスト分析ツール

## 🤝 サポート

### 質問・改善提案
- GitHub Issues: 最適化に関する提案
- Slack: #github-actions-optimization
- Email: github@sas-com.com

### 貢献ガイドライン
1. 改善案はIssueで議論
2. パフォーマンステストを含むPR
3. レビュー後にマージ

---

**注意事項**
- 本テンプレートは継続的に改善されます
- 適用前に必ずテスト環境で検証してください
- プロジェクト固有の要件に応じてカスタマイズが必要です