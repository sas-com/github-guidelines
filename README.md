# GitHub 運用ガイドライン

**エス・エー・エス株式会社**  
*最終更新日: 2025年9月5日*  
*バージョン: 1.0.0*

## 📌 概要

このリポジトリは、エス・エー・エス株式会社におけるGitHub利用に関する**全社共通**ガイドラインをまとめたものです。
各プロジェクト固有のガイドラインは、[プロジェクト別ガイドライン作成マニュアル](./PROJECT_GUIDELINE_TEMPLATE.md)を参考に、各プロジェクトリポジトリ内に作成してください。

---

## 🚀 SAS Flow - マイクロサービス向けブランチ戦略

### 新しいブランチ戦略の導入
エス・エー・エス株式会社では、マイクロサービス環境に最適化された新しいブランチ戦略「SAS Flow」を導入します。

| ドキュメント | 対象者 | 概要 |
|------------|--------|------|
| **[SAS Flow実装仕様書](./SAS_FLOW_SPECIFICATION.md)** | 全開発者・アーキテクト | 技術仕様と設計原則 |
| **[ブランチ管理ルール](./BRANCH_MANAGEMENT_RULES.md)** | 全開発者・リーダー | ブランチ命名規則・保護設定 |
| **[CI/CDワークフロー設計](./CICD_WORKFLOW_DESIGN.md)** | DevOps・インフラ担当 | 自動化パイプライン設計 |
| **[運用手順書](./SAS_FLOW_OPERATIONS_GUIDE.md)** | 全開発者・運用チーム | 日常業務・緊急対応手順 |
| **[教育・導入計画](./SAS_FLOW_EDUCATION_PLAN.md)** | PM・人事・管理職 | チーム教育・段階的導入 |

**導入開始**: 2025年9月10日〜（8週間の段階的移行）  
**対象**: 全マイクロサービス開発チーム（20名）

---

## 📚 対象者別ドキュメントガイド

### 🆕 新規参画者の方

| 順番 | ドキュメント | 説明 |
|------|------------|------|
| 1 | **[GitHubアカウント作成・設定ガイド](./GITHUB_ACCOUNT_SETUP.md)** | アカウント作成から2FA設定までの詳細手順 |
| 2 | **[新規参画者向けオンボーディング](./ONBOARDING.md)** | 環境構築から開発開始までの手順（WSL2対応） |
| 3 | **[統合ガイドライン](./MASTER_GITHUB_GUIDELINES.md)** 🆕 | GitHub運用の全体像（10セクション構成） |
| 4 | **[クイックリファレンス](./QUICK_REFERENCE.md)** | よく使うコマンドと操作の簡易マニュアル |
| 5 | **[緊急時対応マニュアル](./EMERGENCY_RESPONSE.md)** | インシデント発生時の対応手順 |

### 👨‍💻 既存開発者の方

| 優先度 | ドキュメント | 説明 |
|--------|------------|------|
| 高 | **[クイックリファレンス](./QUICK_REFERENCE.md)** | よく使うコマンドと操作の簡易マニュアル（日常業務で活用） |
| 高 | **[開発チーム向けガイド](./TEAM_CUSTOMIZATION_DEV.md)** 🆕 | 開発者専用のワークフローと自動化 |
| 中 | **[統合ガイドライン](./MASTER_GITHUB_GUIDELINES.md)** 🆕 | GitHub運用の包括的ガイド（必要時に参照） |
| 中 | **[緊急時対応マニュアル](./EMERGENCY_RESPONSE.md)** | インシデント発生時の対応手順 |

### 📋 PM・テックリードの方

| 優先度 | ドキュメント | 説明 |
|--------|------------|------|
| 高 | **[統合ガイドライン](./MASTER_GITHUB_GUIDELINES.md)** 🆕 | GitHub運用の包括的ガイド（全体管理） |
| 高 | **[Issue/Project管理ガイド](./ISSUE_PROJECT_MANAGEMENT_GUIDE.md)** 🆕 | Issue管理とProject Board運用 |
| 高 | **[実装サマリー](./IMPLEMENTATION_SUMMARY.md)** 🆕 | 統合システムの全体像とROI分析 |
| 中 | **[プロジェクト別ガイドライン作成マニュアル](./PROJECT_GUIDELINE_TEMPLATE.md)** | 各プロジェクト固有ガイドラインの作成手順 |

### 🤝 クライアント様

| 順番 | ドキュメント | 説明 |
|------|------------|------|
| 1 | **[クライアント様向け利用ガイド](./CLIENT_GUIDE.md)** | 進捗確認とフィードバックの方法 |
| 2 | **[GitHubアカウント作成・設定ガイド](./GITHUB_ACCOUNT_SETUP.md)** | アカウント作成手順（必要に応じて） |

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

1. **[GitHubアカウント作成・設定ガイド](./GITHUB_ACCOUNT_SETUP.md)** でアカウント作成
2. **[オンボーディングガイド](./ONBOARDING.md)** を確認
3. 環境構築（WSL2、Git、GitHub）
4. SSH鍵の設定
5. 練習リポジトリでトレーニング

### 開発者の方

1. **[クイックリファレンス](./QUICK_REFERENCE.md)** を手元に
2. プロジェクトリポジトリをクローン
3. ブランチルールに従って開発
4. PRを作成してレビューを依頼

### クライアント様

1. **[クライアント様向けガイド](./CLIENT_GUIDE.md)** を確認
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

### ブランチ構成

```
main        # 本番環境（今後構築予定）
staging     # ステージング環境（今後構築予定）
dev         # 開発環境（現在運用中）

feature/[機能名]  # 新機能開発
bugfix/[説明]     # バグ修正
hotfix/[説明]     # 緊急修正
```

**※現在の運用**: dev環境のみ運用中。devブランチで開発作業を実施。**強制プッシュは厳禁**。

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

**詳細は [緊急時対応マニュアル](./EMERGENCY_RESPONSE.md) を参照**

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
- **[MASTER_GITHUB_GUIDELINES.md](./MASTER_GITHUB_GUIDELINES.md)** 🆕 - 統合ガイドライン（単一情報源）
- **[IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)** 🆕 - 実装成果・ROI分析

#### 🚀 運用・ワークフロー
- **[BRANCH_MANAGEMENT_RULES.md](./BRANCH_MANAGEMENT_RULES.md)** - ブランチ管理
- **[COMMIT_CONVENTION_GUIDE.md](./COMMIT_CONVENTION_GUIDE.md)** - コミット規約
- **[PR_REVIEW_GUIDELINES.md](./PR_REVIEW_GUIDELINES.md)** - PRレビューガイド
- **[ISSUE_PROJECT_MANAGEMENT_GUIDE.md](./ISSUE_PROJECT_MANAGEMENT_GUIDE.md)** 🆕 - Issue/Project管理

#### 🛡️ セキュリティ・品質
- **[GITHUB_SECURITY_BEST_PRACTICES.md](./GITHUB_SECURITY_BEST_PRACTICES.md)** - セキュリティベストプラクティス
- **[SECRETS_MANAGEMENT_GUIDE.md](./SECRETS_MANAGEMENT_GUIDE.md)** - シークレット管理
- **[TEST_STRATEGY.md](./TEST_STRATEGY.md)** - テスト戦略

#### 🔧 CI/CD・デプロイメント
- **[CICD_WORKFLOW_DESIGN.md](./CICD_WORKFLOW_DESIGN.md)** - CI/CDワークフロー設計
- **[CICD_DEPLOYMENT_STRATEGY.md](./CICD_DEPLOYMENT_STRATEGY.md)** - デプロイメント戦略
- **[ENVIRONMENT_DEPLOYMENT_STRATEGY.md](./ENVIRONMENT_DEPLOYMENT_STRATEGY.md)** - 環境別デプロイ

#### 👥 チーム別カスタマイズ
- **[TEAM_CUSTOMIZATION_DEV.md](./TEAM_CUSTOMIZATION_DEV.md)** 🆕 - 開発チーム向け
- **[TEAM_CUSTOMIZATION_INFRA.md](./TEAM_CUSTOMIZATION_INFRA.md)** 🆕 - インフラチーム向け
- **[TEAM_CUSTOMIZATION_SECURITY.md](./TEAM_CUSTOMIZATION_SECURITY.md)** 🆕 - セキュリティチーム向け

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