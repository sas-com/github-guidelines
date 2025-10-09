# ワークフロードキュメント INDEX

**エス・エー・エス株式会社**
*GitHub運用におけるワークフロー関連ドキュメント一覧*

## 📚 ドキュメント一覧

このディレクトリには、エス・エー・エス株式会社のGitHub運用における各種ワークフロー、ルール、ガイドラインに関するドキュメントが格納されています。

---

## 🔄 SAS Git Flow関連

### [SAS_FLOW_SPECIFICATION.md](./SAS_FLOW_SPECIFICATION.md)
**SAS Git Flow実装仕様書**
- SAS Git Flowの詳細な技術仕様
- 環境構成（dev/staging/main）の定義
- プロジェクトタイプ別の適用方法
- セキュリティポリシーと緊急対応フロー

### [SAS_FLOW_OPERATIONS_GUIDE.md](./SAS_FLOW_OPERATIONS_GUIDE.md)
**SAS Flow運用手順書**
- 日常的な開発作業の具体的な手順
- 緊急時対応フロー（L1〜L4レベル別）
- トラブルシューティングガイド
- 運用上のベストプラクティス

### [SAS_FLOW_EDUCATION_PLAN.md](./SAS_FLOW_EDUCATION_PLAN.md)
**SAS Flow教育・導入計画書**
- 8週間の段階的導入計画
- 役割別トレーニングプログラム
- 成功指標（KPI）と評価基準
- 導入後のフォローアップ体制

### [SAS_GIT_FLOW_UPDATE_RECOMMENDATIONS.md](./SAS_GIT_FLOW_UPDATE_RECOMMENDATIONS.md)
**SAS Git Flow更新推奨事項**
- SAS FlowからSAS Git Flowへの移行ガイド
- 完了済み更新項目の記録
- 今後の改善提案と検討事項

---

## 🌿 ブランチ管理

### [BRANCH_MANAGEMENT_RULES.md](./BRANCH_MANAGEMENT_RULES.md)
**ブランチ管理ルール**
- ブランチ階層と責任範囲の定義
- 作業ブランチの分類と命名規則
- ブランチ保護設定の詳細
- マージ戦略とポリシー

---

## 📝 コミット規約

### [COMMIT_CONVENTION_GUIDE.md](./COMMIT_CONVENTION_GUIDE.md)
**コミット規約ガイドライン**
- Conventional Commitsベースのメッセージフォーマット
- タイプ別コミットの分類と使用例
- スコープ定義とベストプラクティス
- CI/CD連携とバージョニング

---

## 🔍 プルリクエスト（PR）関連

### [PR_REVIEW_GUIDELINES.md](./PR_REVIEW_GUIDELINES.md)
**プルリクエスト運用ガイドライン**
- PRレビューの目的と基準
- PRタイプ分類（Feature/Bugfix/Hotfix等）
- レビュアーの責務とSLA
- 効率的なレビュープロセス

### [PR_REVIEW_CHECKLIST.md](./PR_REVIEW_CHECKLIST.md)
**プルリクエストレビューチェックリスト**
- 基本品質チェック項目
- セキュリティレビューポイント
- パフォーマンス確認事項
- PRタイプ別・レビュアーレベル別チェックリスト

### [PR_TEST_AUTOMATION_GUIDE.md](./PR_TEST_AUTOMATION_GUIDE.md)
**PR自動テストガイド**
- 自動テストシステムの概要と目的
- テストタイプ別の設定方法
- CI/CDパイプラインとの統合
- テスト結果の解釈とトラブルシューティング

---

## 🎯 ドキュメント選択ガイド

### 新規参画者の方
1. [SAS_FLOW_SPECIFICATION.md](./SAS_FLOW_SPECIFICATION.md) - 基本概念の理解
2. [BRANCH_MANAGEMENT_RULES.md](./BRANCH_MANAGEMENT_RULES.md) - ブランチ運用の把握
3. [COMMIT_CONVENTION_GUIDE.md](./COMMIT_CONVENTION_GUIDE.md) - コミット作成ルール

### 開発者の方
1. [SAS_FLOW_OPERATIONS_GUIDE.md](./SAS_FLOW_OPERATIONS_GUIDE.md) - 日常作業の手順
2. [PR_REVIEW_GUIDELINES.md](./PR_REVIEW_GUIDELINES.md) - PR作成と運用
3. [PR_TEST_AUTOMATION_GUIDE.md](./PR_TEST_AUTOMATION_GUIDE.md) - 自動テストの活用

### レビュアーの方
1. [PR_REVIEW_CHECKLIST.md](./PR_REVIEW_CHECKLIST.md) - レビューチェック項目
2. [PR_REVIEW_GUIDELINES.md](./PR_REVIEW_GUIDELINES.md) - レビュー基準とSLA

### マネージャー・リーダーの方
1. [SAS_FLOW_EDUCATION_PLAN.md](./SAS_FLOW_EDUCATION_PLAN.md) - チーム教育計画
2. [SAS_GIT_FLOW_UPDATE_RECOMMENDATIONS.md](./SAS_GIT_FLOW_UPDATE_RECOMMENDATIONS.md) - 改善提案

---

## 📊 クイックリファレンス

| ドキュメント | 主な対象者 | 更新頻度 | 重要度 |
|------------|-----------|---------|--------|
| SAS_FLOW_SPECIFICATION | 全員 | 四半期 | ⭐⭐⭐⭐⭐ |
| SAS_FLOW_OPERATIONS_GUIDE | 開発者 | 月次 | ⭐⭐⭐⭐⭐ |
| BRANCH_MANAGEMENT_RULES | 全員 | 四半期 | ⭐⭐⭐⭐⭐ |
| COMMIT_CONVENTION_GUIDE | 開発者 | 年次 | ⭐⭐⭐⭐ |
| PR_REVIEW_GUIDELINES | 開発者・レビュアー | 四半期 | ⭐⭐⭐⭐⭐ |
| PR_REVIEW_CHECKLIST | レビュアー | 月次 | ⭐⭐⭐⭐ |
| PR_TEST_AUTOMATION_GUIDE | 開発者・DevOps | 月次 | ⭐⭐⭐⭐ |
| SAS_FLOW_EDUCATION_PLAN | マネージャー | 年次 | ⭐⭐⭐ |
| SAS_GIT_FLOW_UPDATE_RECOMMENDATIONS | リーダー | 随時 | ⭐⭐⭐ |

---

## 🔍 キーワード検索

### 緊急対応が必要な場合
→ [SAS_FLOW_OPERATIONS_GUIDE.md](./SAS_FLOW_OPERATIONS_GUIDE.md) の「緊急時対応フロー」セクション

### ブランチ命名規則を確認したい
→ [BRANCH_MANAGEMENT_RULES.md](./BRANCH_MANAGEMENT_RULES.md) の「作業ブランチ分類」セクション

### コミットメッセージの書き方
→ [COMMIT_CONVENTION_GUIDE.md](./COMMIT_CONVENTION_GUIDE.md) の「基本フォーマット」セクション

### PRがマージされない理由を知りたい
→ [PR_REVIEW_CHECKLIST.md](./PR_REVIEW_CHECKLIST.md) で未対応項目を確認

### 自動テストが失敗した場合
→ [PR_TEST_AUTOMATION_GUIDE.md](./PR_TEST_AUTOMATION_GUIDE.md) の「トラブルシューティング」セクション

---

## 📞 お問い合わせ

ドキュメントに関する質問や改善提案がある場合は、以下までご連絡ください：

- **GitHub管理チーム**: github@sas-com.com
- **Slackチャンネル**: #github-support
- **Issue作成**: [github-guidelines リポジトリ](https://github.com/sas-com/github-guidelines/issues)

---

*最終更新: 2025年10月*