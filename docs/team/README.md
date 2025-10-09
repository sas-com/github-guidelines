# docs/team ディレクトリ インデックス

**エス・エー・エス株式会社**
*チーム別GitHub運用ガイドラインドキュメント集*

---

## 📚 ドキュメント一覧

このディレクトリには、各チーム向けに特化したGitHub運用ガイドラインが含まれています。
ご自身のチームに該当するドキュメントをご参照ください。

---

## 🚀 開発チーム向け

### [TEAM_CUSTOMIZATION_DEV.md](./TEAM_CUSTOMIZATION_DEV.md)
**開発チーム版ガイドライン**

#### 概要
開発者向けの実践的なGitHub運用ガイドです。日常的な開発ワークフロー、コード品質管理、自動化ツールの活用方法を詳しく解説しています。

#### 主な内容
- クイックスタート（30秒で始める開発フロー）
- Issue駆動開発のワークフロー
- ブランチ戦略とコミット規約
- コードレビューのベストプラクティス
- VS CodeやDockerを活用した開発効率化
- テスト戦略と優先順位付け
- トラブルシューティングガイド
- 開発チームKPIと成功指標

#### こんな方におすすめ
- フロントエンド/バックエンド開発者
- テストエンジニア
- ジュニア〜シニア開発者

---

## 🔧 インフラ/DevOpsチーム向け

### [TEAM_CUSTOMIZATION_INFRA.md](./TEAM_CUSTOMIZATION_INFRA.md)
**インフラストラクチャ・DevOpsチーム版ガイドライン**

#### 概要
インフラエンジニアとDevOpsエンジニア向けの包括的な運用ガイドです。CI/CDパイプライン、Infrastructure as Code、監視・自動化の実装方法を網羅しています。

#### 主な内容
- CI/CDパイプラインの設計と管理
- Terraform/Kubernetesによる Infrastructure as Code
- Prometheus/Grafanaを使った監視スタック構築
- Blue-Green/カナリアデプロイメント戦略
- 自動スケーリング設定
- バックアップとディザスタリカバリ
- パフォーマンス最適化テクニック
- SLO/SLI設定と運用KPI

#### こんな方におすすめ
- インフラエンジニア
- SRE（Site Reliability Engineer）
- DevOpsエンジニア
- クラウドアーキテクト

---

## 🔐 セキュリティチーム向け

### [TEAM_CUSTOMIZATION_SECURITY.md](./TEAM_CUSTOMIZATION_SECURITY.md)
**セキュリティチーム版ガイドライン**

#### 概要
セキュリティエンジニア向けの脅威対策とコンプライアンス管理ガイドです。脆弱性管理、インシデント対応、セキュリティ自動化の詳細な手順を提供しています。

#### 主な内容
- セキュリティレビューのプロセスとチェックリスト
- CVSS評価に基づく脆弱性管理マトリックス
- インシデント対応プレイブック（P1〜P4分類）
- SAST/DAST/依存関係スキャンの自動化
- フォレンジックツールキット
- コンプライアンス管理（PCI-DSS、GDPR、ISO27001）
- STRIDE脅威モデリング
- Key Risk Indicators (KRI) の設定と監視

#### こんな方におすすめ
- セキュリティエンジニア
- セキュリティアナリスト
- コンプライアンス担当者
- CISO/セキュリティ管理者

---

## 📊 メトリクス・ダッシュボード

### [TEAM_METRICS_DASHBOARDS.md](./TEAM_METRICS_DASHBOARDS.md)
**チーム別成功指標ダッシュボードテンプレート**

#### 概要
各チームのKPI/KRIを可視化するためのダッシュボード設定集です。メトリクスの定義、収集方法、レポーティングテンプレートを提供しています。

#### 主な内容
- 開発チームKPI（ベロシティ、品質、生産性指標）
- インフラチームKPI（可用性、パフォーマンス、効率性指標）
- セキュリティチームKRI（脆弱性、インシデント、コンプライアンス指標）
- 統合エグゼクティブダッシュボード
- Prometheus/Grafana設定例
- 月次レポートテンプレート

#### こんな方におすすめ
- チームリーダー/マネージャー
- プロジェクトマネージャー
- 経営層/ステークホルダー
- メトリクス分析担当者

---

## 🎯 ドキュメント選択ガイド

### あなたの役割から探す

| 役割 | 推奨ドキュメント |
|------|------------------|
| フロントエンド開発者 | [TEAM_CUSTOMIZATION_DEV.md](./TEAM_CUSTOMIZATION_DEV.md) |
| バックエンド開発者 | [TEAM_CUSTOMIZATION_DEV.md](./TEAM_CUSTOMIZATION_DEV.md) |
| インフラエンジニア | [TEAM_CUSTOMIZATION_INFRA.md](./TEAM_CUSTOMIZATION_INFRA.md) |
| DevOpsエンジニア | [TEAM_CUSTOMIZATION_INFRA.md](./TEAM_CUSTOMIZATION_INFRA.md) |
| セキュリティエンジニア | [TEAM_CUSTOMIZATION_SECURITY.md](./TEAM_CUSTOMIZATION_SECURITY.md) |
| チームリーダー | [TEAM_METRICS_DASHBOARDS.md](./TEAM_METRICS_DASHBOARDS.md) |
| プロジェクトマネージャー | すべてのドキュメント |

### 目的から探す

| 目的 | 推奨ドキュメント |
|------|------------------|
| 開発フローを理解したい | [TEAM_CUSTOMIZATION_DEV.md](./TEAM_CUSTOMIZATION_DEV.md) |
| CI/CDを構築したい | [TEAM_CUSTOMIZATION_INFRA.md](./TEAM_CUSTOMIZATION_INFRA.md) |
| セキュリティレビューを実施したい | [TEAM_CUSTOMIZATION_SECURITY.md](./TEAM_CUSTOMIZATION_SECURITY.md) |
| チームの成果を測定したい | [TEAM_METRICS_DASHBOARDS.md](./TEAM_METRICS_DASHBOARDS.md) |
| インシデント対応手順を知りたい | [TEAM_CUSTOMIZATION_SECURITY.md](./TEAM_CUSTOMIZATION_SECURITY.md) |
| 自動化を推進したい | [TEAM_CUSTOMIZATION_INFRA.md](./TEAM_CUSTOMIZATION_INFRA.md) |

---

## 📝 ドキュメント利用上の注意

1. **最新版の確認**
   - 各ドキュメントの更新日を確認してください
   - 定期的に最新版をチェックすることを推奨します

2. **カスタマイズ推奨**
   - これらのドキュメントはテンプレートです
   - プロジェクトの特性に合わせてカスタマイズしてください

3. **フィードバック歓迎**
   - 改善提案は GitHub Issues で受け付けています
   - 実践で得た知見の共有をお願いします

4. **機密情報の取り扱い**
   - 特にセキュリティ関連ドキュメントは機密情報を含む可能性があります
   - 適切なアクセス制御を設定してください

---

## 🔄 関連ドキュメント

### 基本ガイドライン
- [/README.md](/README.md) - プロジェクト全体の概要
- [/GUIDELINES_DETAIL.md](/GUIDELINES_DETAIL.md) - 詳細な運用ガイドライン
- [/QUICK_REFERENCE.md](/QUICK_REFERENCE.md) - クイックリファレンス

### その他の専門ドキュメント
- [/docs/workflow/](../workflow/) - ワークフロー関連ドキュメント
- [/docs/security/](../security/) - セキュリティ関連ドキュメント
- [/EMERGENCY_RESPONSE.md](/EMERGENCY_RESPONSE.md) - 緊急時対応マニュアル

---

## 📞 サポート

### 各チーム連絡先
- **開発チーム**: dev-support@sas-com.com
- **インフラチーム**: infra@sas-com.com
- **セキュリティチーム**: security@sas-com.com
- **GitHub管理チーム**: github@sas-com.com

### Slackチャンネル
- `#dev-team` - 開発チーム
- `#infra-team` - インフラチーム
- `#security-team` - セキュリティチーム
- `#github-support` - GitHub全般のサポート

---

**最終更新日**: 2025-10-09
**バージョン**: 1.0.0
**メンテナー**: エス・エー・エス株式会社 GitHub管理チーム