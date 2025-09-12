# GitHub 運用ガイドライン

**エス・エー・エス株式会社**  
*最終更新日: 2025年9月5日*  
*バージョン: 1.0.0*

## 📌 概要

このリポジトリは、エス・エー・エス株式会社におけるGitHub利用に関する**全社共通**ガイドラインをまとめたものです。
各プロジェクト固有のガイドラインは、[プロジェクト別ガイドライン作成マニュアル](./PROJECT_GUIDELINE_TEMPLATE.md)を参考に、各プロジェクトリポジトリ内に作成してください。

---

## 📚 対象者別ドキュメントマトリクス

適切なドキュメントを見つけやすくするため、対象者別に優先度マトリクスを整理しています。

### 凡例
- **◎** = 必須（Must read - 最初に読むべきドキュメント）
- **○** = 推奨（Recommended - 業務で頻繁に参照）
- **△** = 参考（Reference - 必要時に参照）
- **－** = 対象外（Not applicable）

---

### 📊 Matrix 1: 開発者向けドキュメントマトリクス

| No | 種別 | ドキュメント | 説明 | 重要度 | 新規参画者 | 既存開発者 | テックリード |
|----|------|------------|------|--------|-----------|-----------|-------------|
| 1 | 基本 | **[GitHub環境構築ガイド](./docs/onboarding/GITHUB_ENVIRONMENT_SETUP.md)** | WSL2、Git、GitHubの完全セットアップ | 高 | ◎ | △ | △ |
| 2 | 基本 | **[オンボーディング](./docs/onboarding/ONBOARDING.md)** | 環境構築から開発開始までの手順 | 高 | ◎ | － | △ |
| 3 | 基本 | **[統合ガイドライン](./docs/overview/MASTER_GITHUB_GUIDELINES.md)** | GitHub運用の全体像（10セクション構成） | 高 | ◎ | ○ | ◎ |
| 4 | 基本 | **[クイックリファレンス](./docs/reference/QUICK_REFERENCE.md)** | よく使うコマンドと操作 | 高 | ◎ | ◎ | ○ |
| 5 | 運用 | **[ブランチ管理ルール](./docs/workflow/BRANCH_MANAGEMENT_RULES.md)** | ブランチ戦略・命名規則 | 高 | ○ | ◎ | ◎ |
| 6 | 運用 | **[コミット規約](./docs/workflow/COMMIT_CONVENTION_GUIDE.md)** | コミットメッセージフォーマット | 高 | ◎ | ◎ | ○ |
| 7 | 運用 | **[PRレビューガイド](./docs/workflow/PR_REVIEW_GUIDELINES.md)** | レビュープロセスと基準 | 高 | ○ | ◎ | ◎ |
| 8 | 運用 | **[PRチェックリスト](./docs/workflow/PR_REVIEW_CHECKLIST.md)** | PR作成時の確認項目 | 中 | ○ | ◎ | ○ |
| 9 | 運用 | **[SAS Git Flow仕様](./docs/workflow/SAS_FLOW_SPECIFICATION.md)** | 独自Gitフロー詳細仕様 | 高 | ○ | ○ | ◎ |
| 10 | 運用 | **[SAS Flow運用ガイド](./docs/workflow/SAS_FLOW_OPERATIONS_GUIDE.md)** | Gitフロー運用手順 | 中 | △ | ○ | ◎ |
| 11 | 技術 | **[開発チーム向けガイド](./docs/team/TEAM_CUSTOMIZATION_DEV.md)** | 開発者専用ワークフロー | 高 | ○ | ◎ | ◎ |
| 12 | 技術 | **[PRテスト自動化](./docs/workflow/PR_TEST_AUTOMATION_GUIDE.md)** | 自動テスト実装ガイド | 中 | △ | ○ | ◎ |
| 13 | 技術 | **[CI/CDワークフロー](./docs/cicd/CICD_WORKFLOW_DESIGN.md)** | パイプライン設計 | 中 | △ | ○ | ◎ |
| 14 | 技術 | **[GitHub Actions運用](./docs/cicd/GITHUB_ACTIONS_OPERATIONS.md)** | Actions実装・運用 | 中 | △ | ○ | ◎ |
| 15 | 技術 | **[テスト戦略](./docs/management/TEST_STRATEGY.md)** | 品質保証プロセス | 中 | △ | ○ | ◎ |
| 16 | セキュリティ | **[セキュアコーディング](./docs/security/SECURE_CODING_GUIDE.md)** | 安全なコード実装 | 高 | ○ | ◎ | ◎ |
| 17 | セキュリティ | **[シークレット管理](./docs/security/SECRETS_MANAGEMENT_GUIDE.md)** | 機密情報の取り扱い | 高 | ◎ | ◎ | ◎ |
| 18 | セキュリティ | **[PRセキュリティチェック](./docs/security/PR_SECURITY_CHECKLIST.md)** | セキュリティレビュー項目 | 中 | △ | ○ | ◎ |
| 19 | 緊急対応 | **[緊急時対応マニュアル](./docs/reference/EMERGENCY_RESPONSE.md)** | インシデント対応手順 | 高 | ○ | ○ | ◎ |
| 20 | 緊急対応 | **[トラブルシューティング](./docs/management/TROUBLESHOOTING.md)** | 問題解決ガイド | 中 | △ | ○ | ○ |

---

### 📊 Matrix 2: 管理者向けドキュメントマトリクス

| No | 種別 | ドキュメント | 説明 | 重要度 | PM | 基盤管理者 |
|----|------|------------|------|--------|-----|----------|
| 1 | 基本 | **[統合ガイドライン](./docs/overview/MASTER_GITHUB_GUIDELINES.md)** | GitHub運用の包括的ガイド | 高 | ◎ | ◎ |
| 2 | 基本 | **[実装サマリー](./docs/overview/IMPLEMENTATION_SUMMARY.md)** | システム全体像とROI分析 | 高 | ◎ | ○ |
| 3 | 基本 | **[詳細ガイドライン](./docs/overview/GUIDELINES_DETAIL.md)** | 運用ルール詳細 | 中 | ○ | ◎ |
| 4 | 管理 | **[Issue/Project管理](./docs/management/ISSUE_PROJECT_MANAGEMENT_GUIDE.md)** | 課題管理とProject Board | 高 | ◎ | ○ |
| 5 | 管理 | **[テスト戦略](./docs/management/TEST_STRATEGY.md)** | 品質管理プロセス | 高 | ◎ | △ |
| 6 | 管理 | **[チームメトリクス](./docs/team/TEAM_METRICS_DASHBOARDS.md)** | KPI・ダッシュボード | 高 | ◎ | ○ |
| 7 | 管理 | **[プロジェクトテンプレート](./docs/onboarding/PROJECT_GUIDELINE_TEMPLATE.md)** | プロジェクト別ガイド作成 | 中 | ○ | △ |
| 8 | アーキテクチャ | **[組織アーキテクチャ](./docs/overview/GITHUB_ORG_ARCHITECTURE.md)** | GitHub組織構造設計 | 高 | ○ | ◎ |
| 9 | アーキテクチャ | **[技術実装](./docs/overview/GITHUB_TECHNICAL_IMPLEMENTATION.md)** | 技術アーキテクチャ | 中 | △ | ◎ |
| 10 | CI/CD | **[CI/CDベストプラクティス](./docs/cicd/CICD_BEST_PRACTICES.md)** | CI/CD最適化手法 | 中 | ○ | ◎ |
| 11 | CI/CD | **[デプロイ戦略](./docs/cicd/CICD_DEPLOYMENT_STRATEGY.md)** | リリース管理手法 | 高 | ◎ | ◎ |
| 12 | CI/CD | **[環境別デプロイ](./docs/cicd/ENVIRONMENT_DEPLOYMENT_STRATEGY.md)** | 環境管理戦略 | 高 | ○ | ◎ |
| 13 | CI/CD | **[デプロイ運用ガイド](./docs/cicd/DEPLOYMENT_OPERATIONS_GUIDE.md)** | デプロイ実行手順 | 中 | △ | ◎ |
| 14 | CI/CD | **[パフォーマンス最適化](./docs/cicd/CICD_PERFORMANCE_OPTIMIZATION_GUIDE.md)** | CI/CD高速化 | 低 | △ | ○ |
| 15 | CI/CD | **[Actionsチェックリスト](./docs/cicd/GITHUB_ACTIONS_CHECKLIST.md)** | Actions実装確認項目 | 中 | △ | ◎ |
| 16 | CI/CD | **[Webhook仕様](./docs/cicd/WEBHOOK_API_SPECIFICATION.md)** | Webhook API設計 | 低 | △ | ○ |
| 17 | CI/CD | **[Webhookデプロイ](./docs/cicd/WEBHOOK_DEPLOYMENT_GUIDE.md)** | Webhook実装ガイド | 低 | △ | ○ |
| 18 | セキュリティ | **[セキュリティベストプラクティス](./docs/security/GITHUB_SECURITY_BEST_PRACTICES.md)** | セキュリティ対策全般 | 高 | ◎ | ◎ |
| 19 | セキュリティ | **[インシデント対応計画](./docs/security/SECURITY_INCIDENT_RESPONSE_PLAN.md)** | セキュリティインシデント対応 | 高 | ◎ | ◎ |
| 20 | セキュリティ | **[セキュリティレビュー](./docs/security/SECURITY_REVIEW_PROCESS.md)** | セキュリティ評価プロセス | 中 | ○ | ◎ |
| 21 | セキュリティ | **[リスクマトリクス](./docs/security/SECURITY_RISK_MATRIX.md)** | リスク評価基準 | 高 | ◎ | ○ |
| 22 | セキュリティ | **[監視設定](./docs/security/SECURITY_MONITORING_SETUP.md)** | セキュリティ監視構築 | 中 | △ | ◎ |
| 23 | セキュリティ | **[SAST/DAST統合](./docs/security/SAST_DAST_INTEGRATION_GUIDE.md)** | セキュリティテスト自動化 | 中 | △ | ◎ |
| 24 | チーム運用 | **[インフラチーム向け](./docs/team/TEAM_CUSTOMIZATION_INFRA.md)** | DevOps/SRE向けガイド | 中 | △ | ◎ |
| 25 | チーム運用 | **[セキュリティチーム向け](./docs/team/TEAM_CUSTOMIZATION_SECURITY.md)** | セキュリティ運用ガイド | 中 | △ | ○ |
| 26 | 教育 | **[SAS Flow教育計画](./docs/workflow/SAS_FLOW_EDUCATION_PLAN.md)** | トレーニングプログラム | 中 | ○ | △ |
| 27 | 教育 | **[セキュリティトレーニング](./docs/security/SECURITY_TRAINING_GUIDE.md)** | セキュリティ教育 | 中 | ○ | △ |
| 28 | 教育 | **[インシデント対応訓練](./docs/security/INCIDENT_RESPONSE_TRAINING.md)** | 対応訓練プログラム | 中 | ○ | ○ |
| 29 | 緊急対応 | **[緊急時対応マニュアル](./docs/reference/EMERGENCY_RESPONSE.md)** | インシデント対応手順 | 高 | ◎ | ◎ |
| 30 | 緊急対応 | **[インシデント分類](./docs/security/INCIDENT_CLASSIFICATION_GUIDE.md)** | インシデントレベル判定 | 高 | ◎ | ○ |
| 31 | 緊急対応 | **[デプロイトラブル対応](./docs/cicd/DEPLOYMENT_TROUBLESHOOTING_GUIDE.md)** | デプロイ問題解決 | 中 | ○ | ◎ |
| 32 | 緊急対応 | **[フォレンジック](./docs/security/FORENSICS_EVIDENCE_GUIDE.md)** | 証拠保全手順 | 低 | △ | ○ |

---

### 📊 Matrix 3: クライアント向けドキュメントマトリクス

| No | 種別 | ドキュメント | 説明 | 重要度 | クライアント |
|----|------|------------|------|--------|------------|
| 1 | 基本 | **[クライアント向けガイド](./docs/onboarding/CLIENT_GUIDE.md)** | 進捗確認とフィードバック方法 | 高 | ◎ |
| 2 | 基本 | **[GitHub環境構築ガイド](./docs/onboarding/GITHUB_ENVIRONMENT_SETUP.md)** | 環境セットアップ（必要に応じて） | 中 | ○ |
| 3 | 基本 | **[クイックリファレンス](./docs/reference/QUICK_REFERENCE.md)** | 基本操作ガイド | 低 | △ |
| 4 | 管理 | **[実装サマリー](./docs/overview/IMPLEMENTATION_SUMMARY.md)** | プロジェクト成果・ROI | 中 | △ |
| 5 | 管理 | **[Issue/Project管理](./docs/management/ISSUE_PROJECT_MANAGEMENT_GUIDE.md)** | 進捗確認方法（閲覧のみ） | 中 | △ |
| 6 | セキュリティ | **[セキュリティベストプラクティス](./docs/security/GITHUB_SECURITY_BEST_PRACTICES.md)** | セキュリティ対策概要 | 低 | △ |
| 7 | 緊急対応 | **[緊急時対応マニュアル](./docs/reference/EMERGENCY_RESPONSE.md)** | 問題発生時の連絡方法 | 中 | ○ |

---

## 🔑 基本原則

### 1. セキュリティファースト
- ✅ すべてのリポジトリは原則 **Private**
- ✅ 2要素認証（2FA）**必須**
- ✅ 機密情報はコミットしない
- ✅ 定期的な権限見直し

### 2. 品質重視
- ✅ コードレビュー必須
- ✅ テスト実施
- ✅ ドキュメント整備

### 3. 透明性
- ✅ 進捗の可視化
- ✅ 問題の早期共有
- ✅ 建設的なコミュニケーション

---

## 🚀 クイックスタート

### 新規参画者の方

1. **[GitHub環境構築ガイド](./docs/onboarding/GITHUB_ENVIRONMENT_SETUP.md)** で環境構築
2. **[オンボーディングガイド](./docs/onboarding/ONBOARDING.md)** を確認
3. 環境構築（WSL2、Git、GitHub）
4. SSH鍵の設定
5. 練習リポジトリでトレーニング

### 開発者の方

1. **[クイックリファレンス](./docs/reference/QUICK_REFERENCE.md)** を手元に
2. プロジェクトリポジトリをクローン
3. ブランチルールに従って開発
4. PRを作成してレビューを依頼

### クライアント様

1. **[クライアント様向けガイド](./docs/onboarding/CLIENT_GUIDE.md)** を確認
2. GitHubアカウント作成
3. プロジェクト招待を承認
4. 進捗確認とフィードバック

---

## 📝 主要ルール サマリー

### コミットメッセージ規約

```
<type>(<scope>): <subject> (#Issue番号)

例：
feat(auth): ログイン機能を実装 (#123)
fix(api): ユーザー検索のバグを修正 (#456)
docs(readme): インストール手順を更新 (#789)
```

### ブランチ戦略（SAS Git Flow）

```
main        # 本番環境
staging     # ステージング環境
dev         # 開発環境

feature/[component]/[機能名]  # 新機能開発
bugfix/[component]/[説明]     # バグ修正
hotfix/[component]/[説明]     # 緊急修正
```

詳細は **[ブランチ管理ルール](./docs/workflow/BRANCH_MANAGEMENT_RULES.md)** を参照。

### 優先度ラベル

| ラベル | 意味 | 対応期限 |
|--------|------|----------|
| 🔴 `priority: critical` | 最優先 | 即座 |
| 🟠 `priority: high` | 高優先度 | 当日中 |
| 🟡 `priority: medium` | 中優先度 | 今週中 |
| 🟢 `priority: low` | 低優先度 | 時間があるとき |

---

## 🆘 緊急時対応

### 緊急度レベル

| レベル | 状況 | 対応時間 | 連絡先 |
|--------|------|----------|--------|
| **L1** | システム停止・情報漏洩 | 15分以内 | SAS Github管理チーム |
| **L2** | 重大な機能障害 | 1時間以内 | SAS Github管理チーム |
| **L3** | 部分的障害 | 4時間以内 | SAS Github管理チーム |
| **L4** | 軽微な問題 | 翌営業日 | SAS Github管理チーム |

**詳細は [緊急時対応マニュアル](./docs/reference/EMERGENCY_RESPONSE.md) を参照**

---

## 📞 サポート・問い合わせ

### 社内サポート

| 種別 | 連絡先 | 対応時間 |
|------|--------|----------|
| **技術的問題** | SAS Github管理チーム (github@sas-com.com) | 営業時間内 |
| **権限・アクセス** | SAS Github管理チーム (github@sas-com.com) | 営業時間内 |
| **セキュリティ** | SAS Github管理チーム (github@sas-com.com) | 24時間 |
| **緊急時** | SAS Github管理チーム (github@sas-com.com) | 24時間 |

### よく使うリンク

- [GitHub公式ドキュメント](https://docs.github.com/ja)
- [Pro Git Book（日本語）](https://git-scm.com/book/ja/v2)
- [GitHub Status](https://www.githubstatus.com/) - 障害情報

---

## 📊 ドキュメント構成

### 全社共通ガイドライン（このリポジトリ）

#### 📖 基本ドキュメント
- **[README.md](./README.md)** - このファイル（全体サマリー）
- **[統合ガイドライン](./docs/overview/MASTER_GITHUB_GUIDELINES.md)** 🆕 - 単一情報源
- **[実装サマリー](./docs/overview/IMPLEMENTATION_SUMMARY.md)** 🆕 - 実装成果・ROI分析

#### 🚀 運用・ワークフロー
- **[ブランチ管理](./docs/workflow/BRANCH_MANAGEMENT_RULES.md)** - ブランチ戦略・保護ルール
- **[コミット規約](./docs/workflow/COMMIT_CONVENTION_GUIDE.md)** - メッセージフォーマット
- **[PRレビュー](./docs/workflow/PR_REVIEW_GUIDELINES.md)** - レビューガイドライン
- **[Issue/Project管理](./docs/management/ISSUE_PROJECT_MANAGEMENT_GUIDE.md)** 🆕 - 課題管理

#### 🛡️ セキュリティ・品質
- **[セキュリティベストプラクティス](./docs/security/GITHUB_SECURITY_BEST_PRACTICES.md)** - セキュリティ対策
- **[シークレット管理](./docs/security/SECRETS_MANAGEMENT_GUIDE.md)** - 機密情報保護
- **[テスト戦略](./docs/management/TEST_STRATEGY.md)** - 品質保証

#### 🔧 CI/CD・デプロイメント
- **[CI/CDワークフロー](./docs/cicd/CICD_WORKFLOW_DESIGN.md)** - パイプライン設計
- **[デプロイ戦略](./docs/cicd/CICD_DEPLOYMENT_STRATEGY.md)** - リリース手法
- **[環境別デプロイ](./docs/cicd/ENVIRONMENT_DEPLOYMENT_STRATEGY.md)** - 環境管理

#### 👥 チーム別カスタマイズ
- **[開発チーム向け](./docs/team/TEAM_CUSTOMIZATION_DEV.md)** 🆕 - 開発者ワークフロー
- **[インフラチーム向け](./docs/team/TEAM_CUSTOMIZATION_INFRA.md)** 🆕 - DevOps/SRE
- **[セキュリティチーム向け](./docs/team/TEAM_CUSTOMIZATION_SECURITY.md)** 🆕 - セキュリティ運用

#### 🤖 自動化・ツール
- **scripts/** - 自動化スクリプト群
  - github-automation/ - GitHub設定自動化
  - migration/ - 移行チェックリスト
- **ml_pipeline/** 🆕 - 違反検出MLシステム

### 各プロジェクトリポジトリで作成すべきドキュメント
```
[project-repository]/
├── README.md                    # プロジェクト概要
├── CONTRIBUTING.md              # 開発参加ガイド
├── DEVELOPMENT.md               # 開発環境構築手順
├── ARCHITECTURE.md              # システム設計書（推奨）
├── API.md                       # API仕様書（推奨）
├── DEPLOYMENT.md                # デプロイ手順（推奨）
└── .github/
    ├── ISSUE_TEMPLATE/          # Issueテンプレート
    └── pull_request_template.md # PRテンプレート
```

---

## ⚠️ 重要な注意事項

1. **セキュリティインシデントは即座に報告**
2. **強制プッシュ（--force）は絶対に使用しない**
3. **機密情報は絶対にコミットしない**
4. **不明な点は必ず確認してから作業する**
5. **定期的にガイドラインを確認し、最新情報を把握する**

---

## 📝 改訂履歴

| バージョン | 日付 | 変更内容 | 承認者 |
|-----------|------|---------|--------|
| 1.1.0 | 2025-09-11 | 統合ガイドライン・自動化ツール追加 | 管理責任者 |
| 1.0.0 | 2025-09-05 | 初版作成 | 管理責任者 |

---

**© 2025 エス・エー・エス株式会社 - GitHub運用ガイドライン**