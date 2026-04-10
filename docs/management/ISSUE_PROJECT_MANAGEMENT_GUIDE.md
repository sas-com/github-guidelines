# Issue/Project管理ガイドライン

**エス・エー・エス株式会社**  
*GitHub Issues & Project Boards 運用ガイド*

## 📌 概要

このガイドラインでは、GitHubのIssueとProject Boardsを効果的に活用するためのベストプラクティスを定義します。特にバックエンドアーキテクチャプロジェクトにおける課題管理とプロジェクト進行管理に焦点を当てています。

## 🏷️ Issue ラベリング戦略

### ラベル分類体系

#### 1. 優先度ラベル（Priority）
- `priority: critical` 🔴 - システム停止・データ損失を伴う重要な問題
- `priority: high` 🟠 - ビジネスに大きな影響を与える問題
- `priority: medium` 🟡 - 重要だが急を要さない問題
- `priority: low` 🟢 - 改善要望・将来的な課題

#### 2. 種別ラベル（Type）
- `type: bug` 🐛 - バグ・不具合報告
- `type: feature` ✨ - 新機能・機能追加
- `type: enhancement` 🚀 - 既存機能の改善
- `type: security` 🔒 - セキュリティ関連課題
- `type: performance` ⚡ - パフォーマンス最適化
- `type: refactor` ♻️ - コードリファクタリング
- `type: documentation` 📚 - ドキュメント関連
- `type: test` 🧪 - テスト関連
- `type: infrastructure` 🏗️ - インフラ・環境設定

#### 3. ステータスラベル（Status）
- `status: todo` ⏳ - 対応待ち
- `status: in-progress` 🔄 - 対応中
- `status: review` 👀 - レビュー待ち
- `status: blocked` 🚫 - ブロック中
- `status: on-hold` ⏸️ - 保留中
- `status: needs-info` ❓ - 情報不足

#### 4. コンポーネントラベル（Component）
- `component: api` 📡 - API関連
- `component: database` 🗃️ - データベース関連
- `component: auth` 🔑 - 認証・認可
- `component: middleware` 🔌 - ミドルウェア
- `component: monitoring` 📊 - モニタリング・ログ
- `component: deployment` 🚀 - デプロイ・CI/CD
- `component: config` ⚙️ - 設定管理
- `component: external-api` 🌐 - 外部API連携

#### 5. 技術スタックラベル（Tech Stack）
- `tech: nodejs` 🟢 - Node.js関連
- `tech: python` 🐍 - Python関連
- `tech: docker` 🐳 - Docker関連
- `tech: kubernetes` ☸️ - Kubernetes関連
- `tech: database` 🗄️ - データベース全般
- `tech: redis` 🔴 - Redis関連
- `tech: aws` ☁️ - AWS関連
- `tech: terraform` 🏗️ - Terraform関連

#### 6. 影響範囲ラベル（Impact）
- `impact: breaking` ⚠️ - 破壊的変更
- `impact: minor` 🔹 - 軽微な影響
- `impact: major` 🔶 - 大きな影響
- `impact: patch` 🩹 - パッチレベル
- `impact: hotfix` 🔥 - 緊急対応必要

### バックエンドアーキテクチャ専用ラベル

#### アーキテクチャパターン
- `arch: microservices` 🏛️ - マイクロサービス関連
- `arch: monolith` 🏢 - モノリス関連
- `arch: serverless` ⚡ - サーバーレス関連
- `arch: event-driven` 📨 - イベント駆動アーキテクチャ
- `arch: domain-driven` 🎯 - ドメイン駆動設計

#### データアーキテクチャ
- `data: migration` 🔄 - データ移行
- `data: modeling` 📐 - データモデリング
- `data: integrity` 🛡️ - データ整合性
- `data: backup` 💾 - バックアップ関連
- `data: sync` 🔁 - データ同期

## 📋 Project Board 設計

### プロジェクト構造

#### 1. スプリント管理ボード
```
Backlog → Ready → In Progress → Review → Testing → Done
```

#### 2. 機能開発ボード
```
Planning → Design → Development → Code Review → QA → Staging → Production
```

#### 3. バグ修正ボード
```
Reported → Triaged → Assigned → Fixing → Testing → Verified → Closed
```

### 自動化ルール

#### カード移動自動化
- PR作成時: `Ready` → `In Progress`
- PR承認時: `In Progress` → `Review`
- PRマージ時: `Review` → `Done`
- Issue Close時: 現在のカラム → `Done`

#### ラベル連動
- `status: in-progress` → `In Progress`カラム
- `status: review` → `Review`カラム
- `status: blocked` → `Blocked`カラム

## 📝 Issue テンプレート

### バグ報告テンプレート
```markdown
---
name: 🐛 バグ報告
about: システムの不具合・バグを報告する
title: '[BUG] '
labels: ['type: bug', 'status: todo', 'priority: medium']
assignees: ''
---

## 🐛 バグの概要
<!-- バグの内容を簡潔に説明 -->

## 📋 再現手順
1. 
2. 
3. 

## 💭 期待される動作
<!-- 本来はどのような動作が期待されるか -->

## 🔍 実際の動作
<!-- 実際にはどのような動作になっているか -->

## 📸 スクリーンショット/ログ
<!-- 関連するスクリーンショットやエラーログ -->

## 🌐 環境情報
- OS: 
- ブラウザ: 
- バージョン: 
- 環境: [dev/staging/production]

## 📊 影響範囲
- [ ] ユーザー影響あり
- [ ] システム停止
- [ ] データ損失の可能性
- [ ] セキュリティリスク

## 🏷️ 分類
- コンポーネント: 
- 技術スタック: 
- 影響レベル: 
```

### 機能要望テンプレート
```markdown
---
name: ✨ 機能要望
about: 新機能・機能改善の要望を提出する
title: '[FEATURE] '
labels: ['type: feature', 'status: todo', 'priority: medium']
assignees: ''
---

## 🎯 機能の概要
<!-- 機能の目的と概要を説明 -->

## 📝 詳細仕様
<!-- 具体的な機能仕様を記載 -->

### 機能要件
- [ ] 
- [ ] 
- [ ] 

### 非機能要件
- [ ] パフォーマンス: 
- [ ] セキュリティ: 
- [ ] 可用性: 

## 🎨 UI/UX要件
<!-- UI/UX関連の要件（該当する場合） -->

## 🔧 技術的考慮事項
<!-- 技術的な制約や考慮事項 -->

## 📊 成功指標
<!-- 機能の成功をどう測定するか -->

## 🏷️ 分類
- コンポーネント: 
- 技術スタック: 
- アーキテクチャパターン: 
```

### パフォーマンス問題テンプレート
```markdown
---
name: ⚡ パフォーマンス問題
about: システムのパフォーマンス問題を報告する
title: '[PERF] '
labels: ['type: performance', 'status: todo', 'priority: high']
assignees: ''
---

## ⚡ パフォーマンス問題の概要
<!-- 問題の概要を説明 -->

## 📈 パフォーマンス指標
### 現在の状況
- 応答時間: 
- スループット: 
- リソース使用率: 
  - CPU: %
  - メモリ: MB
  - ディスク I/O: 

### 目標値
- 応答時間: 
- スループット: 

## 🔍 問題の詳細
### 発生条件
- 
- 

### 影響範囲
- [ ] API応答時間
- [ ] データベースクエリ
- [ ] 外部API連携
- [ ] ファイルI/O
- [ ] ネットワーク通信

## 📊 測定データ
<!-- パフォーマンス測定の結果やグラフ -->

## 🛠️ 想定される原因
- [ ] データベースクエリ最適化
- [ ] キャッシュ戦略見直し
- [ ] アルゴリズム改善
- [ ] インフラリソース不足
- [ ] 外部依存関係

## 🏷️ 分類
- コンポーネント: 
- 技術スタック: 
```

## ✅ データ検証ルール

### Issue作成時の検証

#### 必須フィールド検証
```yaml
validation:
  title:
    required: true
    minLength: 10
    pattern: "^\\[(BUG|FEATURE|PERF|SEC|INFRA)\\].*"
  
  body:
    required: true
    minLength: 50
    sections:
      - name: "概要"
        required: true
      - name: "詳細"
        required: true
  
  labels:
    required: true
    minimum: 2
    requiredLabels:
      - type: ["type: bug", "type: feature", "type: enhancement", "type: performance", "type: security"]
      - priority: ["priority: low", "priority: medium", "priority: high", "priority: critical"]
```

#### ラベル組み合わせ検証
```yaml
labelCombinations:
  invalid:
    - ["type: bug", "type: feature"]  # 複数typeラベル禁止
    - ["priority: low", "priority: high"]  # 複数priorityラベル禁止
  
  required:
    "type: security":
      - "component: auth" OR "component: api"  # セキュリティ問題はコンポーネント必須
    "priority: critical":
      - "impact: breaking" OR "impact: major"  # 重要度criticalは影響度必須
```

### 自動ラベル付与ルール

#### タイトルベース
```yaml
autoLabeling:
  title:
    "database|db|sql|query":
      - "component: database"
      - "tech: database"
    "api|endpoint|rest":
      - "component: api"
    "auth|login|jwt|oauth":
      - "component: auth"
      - "tech: nodejs"  # if project uses Node.js
    "docker|container":
      - "tech: docker"
    "performance|slow|timeout":
      - "type: performance"
```

#### コンテンツベース
```yaml
autoLabeling:
  body:
    "breaking change|backward compatibility":
      - "impact: breaking"
    "emergency|urgent|production down":
      - "priority: critical"
    "security vulnerability|exploit|attack":
      - "type: security"
      - "priority: high"
```

## 🔄 ワークフロー統合

### GitHub Actions連携

#### Issue作成時処理
```yaml
name: Issue Management
on:
  issues:
    types: [opened, edited]

jobs:
  validate-issue:
    steps:
      - name: Validate Issue Format
        uses: ./.github/actions/validate-issue
      
      - name: Auto Label Assignment
        uses: ./.github/actions/auto-label
      
      - name: Add to Project Board
        uses: ./.github/actions/add-to-project
```

#### 通知ルール
```yaml
notifications:
  priority_critical:
    channels: ['#alerts', '#on-call']
    mentions: ['@sas-com/sas-sre-team', '@sas-com/sas-security-team']
  
  security_issues:
    channels: ['#security']
    mentions: ['@sas-com/sas-security-team']
  
  performance_issues:
    channels: ['#performance']
    mentions: ['@sas-com/sas-product-backend-team']
```

## 📊 メトリクスとレポート

### 追跡指標

#### Issue管理指標
- Issue作成数（週次/月次）
- 平均解決時間（Priority別）
- ラベル別分布
- 担当者別ワークロード

#### プロジェクト進捗指標
- スプリント完了率
- バーンダウンチャート
- 機能リリース頻度
- バグ修正率

### 定期レポート
- 週次: スプリント進捗報告
- 月次: Issue傾向分析
- 四半期: プロジェクト健全性評価

## 🔧 運用ルール

### Issue管理ルール

#### 作成ルール
1. 適切なテンプレートを使用する
2. 必要な情報を漏れなく記載する
3. 適切なラベル付けを行う
4. 担当者を明確にする

#### 更新ルール
1. 進捗は定期的に更新する
2. ステータス変更時はコメントで理由を記載
3. ブロックされた場合は即座に報告
4. 完了時は検証結果を記載

### Project Board運用

#### カード管理
1. すべてのIssue/PRはProject Boardに追加
2. カードの移動は作業の実態を反映
3. 長期停滞カードは定期的にレビュー
4. 完了カードは定期的にアーカイブ

#### レビューサイクル
- 日次: 進行中作業の確認
- 週次: スプリント進捗レビュー
- 月次: プロジェクト全体振り返り

## 📚 関連ドキュメント

- [PR_REVIEW_GUIDELINES.md](./PR_REVIEW_GUIDELINES.md) - プルリクエストレビューガイドライン
- [COMMIT_CONVENTION_GUIDE.md](./COMMIT_CONVENTION_GUIDE.md) - コミット規約
- [GITHUB_SECURITY_BEST_PRACTICES.md](./GITHUB_SECURITY_BEST_PRACTICES.md) - セキュリティベストプラクティス
- [TEST_STRATEGY.md](./TEST_STRATEGY.md) - テスト戦略

---

**更新日**: 2025-09-10  
**版数**: v1.0  
**承認者**: SAS Github管理チーム