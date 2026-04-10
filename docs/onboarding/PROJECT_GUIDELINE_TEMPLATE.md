# プロジェクト別ガイドライン作成マニュアル

**エス・エー・エス株式会社**  
*各プロジェクト固有のガイドライン作成手順書*  
*最終更新: 2025年9月5日*

## 📌 このマニュアルについて

本マニュアルは、各プロジェクトで固有のGitHub運用ガイドラインを作成する際のテンプレートと手順を提供します。
全社共通ガイドラインに加えて、プロジェクト特有のルールや手順を定義する際にご活用ください。

---

## 🎯 作成すべきドキュメント一覧

### 必須ドキュメント

| ファイル名 | 内容 | 優先度 |
|-----------|------|--------|
| `README.md` | プロジェクト概要と基本情報 | 🔴 必須 |
| `CONTRIBUTING.md` | 開発参加ガイド | 🔴 必須 |
| `.gitignore` | 除外ファイル設定 | 🔴 必須 |
| `DEVELOPMENT.md` | 開発環境構築手順 | 🔴 必須 |

### 推奨ドキュメント

| ファイル名 | 内容 | 優先度 |
|-----------|------|--------|
| `ARCHITECTURE.md` | システム設計書 | 🟠 推奨 |
| `API.md` | API仕様書 | 🟠 推奨 |
| `DEPLOYMENT.md` | デプロイ手順 | 🟠 推奨 |
| `TESTING.md` | テスト手順 | 🟠 推奨 |
| `TROUBLESHOOTING.md` | トラブルシューティング | 🟡 任意 |
| `CHANGELOG.md` | 変更履歴 | 🟡 任意 |

---

## 📝 README.md テンプレート

```markdown
# [プロジェクト名]

**クライアント**: [クライアント名]  
**プロジェクト期間**: 2025年X月 - 2025年Y月  
**担当チーム**: [チーム名]

## 📌 概要

[プロジェクトの概要を2-3文で記載]

## 🎯 主な機能

- 機能1: [説明]
- 機能2: [説明]
- 機能3: [説明]

## 🚀 クイックスタート

### 前提条件

- Node.js v18以上 / Python 3.9以上 / その他
- [必要なツール・ライブラリ]

### インストール

\```bash
# リポジトリのクローン
git clone git@github.com:sas-com/[repository-name].git
cd [repository-name]

# 依存関係のインストール
npm install  # または pip install -r requirements.txt

# 環境変数の設定
cp .env.example .env
# .envファイルを編集
\```

### 開発サーバーの起動

\```bash
npm run dev  # または python manage.py runserver
\```

## 📁 プロジェクト構成

\```
project-root/
├── src/               # ソースコード
│   ├── components/    # コンポーネント
│   ├── services/      # サービス層
│   └── utils/         # ユーティリティ
├── tests/             # テストコード
├── docs/              # ドキュメント
├── scripts/           # スクリプト
└── config/            # 設定ファイル
\```

## 🔧 開発ガイドライン

### ブランチ戦略

#### 現在の構成（デフォルト）
- `dev`: 開発環境（現在運用中）
- `feature/*`: 機能開発
- `bugfix/*`: バグ修正
- `hotfix/*`: 緊急修正

#### 将来の構成（3環境運用時）
- `main`: 本番環境
- `staging`: ステージング環境
- `dev`: 開発環境
- `feature/*`: 機能開発
- `bugfix/*`: バグ修正
- `hotfix/*`: 緊急修正

### コミットメッセージ規約

[全社共通ガイドライン](https://github.com/sas-com/github-guidelines)に準拠

追加ルール:
- [プロジェクト固有のルールがあれば記載]

## 📊 環境情報

| 環境 | URL | ブランチ | 備考 |
|------|-----|----------|------|
| 本番 | https://production.example.com | main | 今後構築予定 |
| ステージング | https://staging.example.com | staging | 今後構築予定 |
| 開発 | https://dev.example.com | dev | 現在運用中 |

## 🧪 テスト

\```bash
# ユニットテスト
npm test

# E2Eテスト
npm run test:e2e

# カバレッジ
npm run test:coverage
\```

## 📦 デプロイ

詳細は [DEPLOYMENT.md](./DEPLOYMENT.md) を参照

\```bash
# 本番環境へのデプロイ
npm run deploy:production

# ステージング環境へのデプロイ
npm run deploy:staging
\```

## 📞 連絡先

| 役割 | 担当者 | 連絡先 |
|------|--------|--------|
| プロジェクト全般 | SAS Github管理チーム | github@sas-com.com |
| 技術サポート | SAS Github管理チーム | github@sas-com.com |
| 緊急時対応 | SAS Github管理チーム | github@sas-com.com |

## 📚 関連ドキュメント

- [全社共通GitHubガイドライン](https://github.com/sas-com/github-guidelines)
- [開発環境構築手順](./DEVELOPMENT.md)
- [API仕様書](./docs/API.md)
- [アーキテクチャ設計書](./ARCHITECTURE.md)

## ⚠️ 注意事項

- [プロジェクト固有の注意事項]
- 機密情報は絶対にコミットしない
- 本番環境へのデプロイは必ず承認を得る

## 📄 ライセンス

[ライセンス情報またはProprietary]

---

**© 2025 エス・エー・エス株式会社**
```

---

## 📝 CONTRIBUTING.md テンプレート

```markdown
# コントリビューションガイド

## 🎯 開発に参加する前に

1. [全社共通ガイドライン](https://github.com/sas-com/github-guidelines)を確認
2. プロジェクト固有のルールを理解
3. 開発環境をセットアップ

## 🔧 開発環境セットアップ

[DEVELOPMENT.md](./DEVELOPMENT.md) を参照

## 📋 開発フロー

### 1. Issueの確認・作成

- 作業開始前に必ずIssueを確認
- 新規タスクの場合はIssueを作成
- 適切なラベルを付与

### 2. ブランチの作成

\```bash
# 最新のdevを取得
git checkout dev
git pull origin dev

# 作業ブランチを作成
git checkout -b feature/[issue-number]-[feature-name]
\```

### 3. 開発作業

- コーディング規約に従って実装
- 適切な単位でコミット
- テストを作成

### 4. プルリクエスト

- PRテンプレートに従って記載
- レビュアーをアサイン
- CIがグリーンであることを確認

## 📏 コーディング規約

### JavaScript/TypeScript
\```javascript
// 良い例
const calculateTotal = (items) => {
  return items.reduce((sum, item) => sum + item.price, 0);
};

// 悪い例
const calc = (i) => {
  let t = 0;
  for(let x of i) t += x.price;
  return t;
};
\```

### Python
\```python
# 良い例
def calculate_total(items: List[Item]) -> float:
    """アイテムの合計金額を計算"""
    return sum(item.price for item in items)

# 悪い例
def calc(i):
    t = 0
    for x in i:
        t += x.price
    return t
\```

## 🧪 テスト

### テストの書き方

\```javascript
describe('UserService', () => {
  it('should create a new user', async () => {
    // Given
    const userData = { name: 'John', email: 'john@example.com' };
    
    // When
    const user = await userService.create(userData);
    
    // Then
    expect(user.id).toBeDefined();
    expect(user.name).toBe('John');
  });
});
\```

### テスト実行

\```bash
# 全テスト実行
npm test

# 特定のテストのみ
npm test -- UserService

# ウォッチモード
npm test -- --watch
\```

## 🚀 リリースプロセス

### 現在のフロー
1. devブランチで開発・テスト
2. devブランチからデプロイ

### 将来のフロー（3環境構成時）
1. dev → staging へPR
2. ステージング環境でテスト
3. staging → main へPR
4. プロダクトオーナーの承認
5. mainへマージ
6. タグ付け
7. 本番デプロイ

## 💬 コミュニケーション

- 日次スタンドアップ: 10:00
- 週次レビュー: 金曜 15:00
- Teamsチャンネル: #proj-[project-name]

## ❓ よくある質問

### Q: ビルドが失敗する
A: `npm ci` を実行して依存関係を再インストール

### Q: テストが通らない
A: 環境変数が正しく設定されているか確認

---

**© 2025 エス・エー・エス株式会社**
```

---

## 📝 DEVELOPMENT.md テンプレート

```markdown
# 開発環境構築ガイド

## 📋 前提条件

### 必須ソフトウェア

| ソフトウェア | バージョン | インストール方法 |
|------------|-----------|---------------|
| Node.js | v18以上 | https://nodejs.org |
| Git | 2.30以上 | https://git-scm.com |
| Docker | 20.10以上 | https://docker.com |
| VS Code | 最新版 | https://code.visualstudio.com |

### 推奨VS Code拡張機能

- ESLint
- Prettier
- GitLens
- [言語別拡張機能]

## 🚀 セットアップ手順

### 1. リポジトリのクローン

\```bash
git clone git@github.com:sas-com/[repository-name].git
cd [repository-name]
\```

### 2. 依存関係のインストール

\```bash
# Node.jsプロジェクトの場合
npm ci

# Pythonプロジェクトの場合
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
\```

### 3. 環境変数の設定

\```bash
# .envファイルを作成
cp .env.example .env

# 必要な値を設定
# エディタで.envを開いて編集
\```

#### 環境変数一覧

| 変数名 | 説明 | 例 |
|--------|------|-----|
| DATABASE_URL | データベース接続文字列 | postgresql://... |
| API_KEY | 外部API用キー | sk_test_... |
| NODE_ENV | 実行環境 | development |

### 4. データベースセットアップ

\```bash
# Dockerでデータベースを起動
docker-compose up -d db

# マイグレーション実行
npm run db:migrate

# 初期データ投入
npm run db:seed
\```

### 5. 動作確認

\```bash
# 開発サーバー起動
npm run dev

# ブラウザで確認
open http://localhost:3000
\```

## 🐳 Docker環境

### 全サービス起動

\```bash
docker-compose up
\```

### 個別サービス起動

\```bash
# データベースのみ
docker-compose up db

# Redisのみ
docker-compose up redis
\```

### トラブルシューティング

\```bash
# コンテナの再ビルド
docker-compose build --no-cache

# ボリュームも含めて削除
docker-compose down -v
\```

## 🔧 開発用コマンド

| コマンド | 説明 |
|---------|------|
| `npm run dev` | 開発サーバー起動 |
| `npm run build` | ビルド |
| `npm run test` | テスト実行 |
| `npm run lint` | Lint実行 |
| `npm run format` | コード整形 |

## 📱 モバイルアプリ開発（該当する場合）

### iOS

\```bash
# 依存関係インストール
cd ios && pod install

# シミュレータで実行
npm run ios
\```

### Android

\```bash
# エミュレータ起動
npm run android
\```

## 🐛 デバッグ

### VS Codeでのデバッグ

1. `.vscode/launch.json`が設定済み
2. F5キーでデバッグ開始
3. ブレークポイントを設定可能

### Chrome DevTools

\```bash
# デバッグモードで起動
npm run dev:debug
\```

chrome://inspect でデバッグ接続

## ⚠️ よくある問題と解決方法

### npm install が失敗する

\```bash
# キャッシュクリア
npm cache clean --force

# node_modules削除して再インストール
rm -rf node_modules package-lock.json
npm install
\```

### ポート競合

\```bash
# 使用中のポートを確認
lsof -i :3000

# プロセスを終了
kill -9 [PID]
\```

### 権限エラー

\```bash
# WSL2の場合
sudo chown -R $USER:$USER .
\```

---

**© 2025 エス・エー・エス株式会社**
```

---

## 📁 .github/ISSUE_TEMPLATE 作成ガイド

### bug_report.yml

```yaml
name: 🐛 バグ報告
description: バグを報告してください
title: "[Bug]: "
labels: ["bug", "triage"]
body:
  - type: markdown
    attributes:
      value: |
        バグ報告ありがとうございます。以下の情報を記入してください。
  
  - type: textarea
    id: description
    attributes:
      label: バグの説明
      description: バグの内容を簡潔に説明してください
      placeholder: "ログインボタンをクリックしてもログインできない"
    validations:
      required: true
  
  - type: textarea
    id: reproduction
    attributes:
      label: 再現手順
      description: バグを再現する手順を記載してください
      value: |
        1. 
        2. 
        3. 
    validations:
      required: true
  
  - type: textarea
    id: expected
    attributes:
      label: 期待する動作
      description: 正常な場合の動作を説明してください
    validations:
      required: true
  
  - type: textarea
    id: actual
    attributes:
      label: 実際の動作
      description: 現在の動作を説明してください
    validations:
      required: true
  
  - type: dropdown
    id: priority
    attributes:
      label: 優先度
      options:
        - 🔴 Critical - システム停止
        - 🟠 High - 主要機能に影響
        - 🟡 Medium - 副次機能に影響
        - 🟢 Low - 軽微な問題
    validations:
      required: true
  
  - type: input
    id: environment
    attributes:
      label: 環境
      description: OS, ブラウザ, バージョンなど
      placeholder: "Windows 11, Chrome 120"
  
  - type: textarea
    id: logs
    attributes:
      label: ログ・スクリーンショット
      description: エラーログやスクリーンショットを添付
```

### feature_request.yml

```yaml
name: ✨ 機能要望
description: 新機能を提案してください
title: "[Feature]: "
labels: ["enhancement"]
body:
  - type: markdown
    attributes:
      value: |
        新機能の提案ありがとうございます。
  
  - type: textarea
    id: description
    attributes:
      label: 機能の説明
      description: 提案する機能を説明してください
    validations:
      required: true
  
  - type: textarea
    id: motivation
    attributes:
      label: 背景・動機
      description: なぜこの機能が必要か
    validations:
      required: true
  
  - type: textarea
    id: solution
    attributes:
      label: 解決策
      description: どのように実装するか
  
  - type: textarea
    id: alternatives
    attributes:
      label: 代替案
      description: 他の解決方法があれば
```

---

## 📁 .github/pull_request_template.md

```markdown
## 📋 概要
<!-- 変更の概要を簡潔に記載 -->

## 🔗 関連Issue
Closes #

## 📝 変更内容
<!-- 詳細な変更内容をリスト形式で -->
- 
- 
- 

## 📸 スクリーンショット
<!-- UI変更がある場合は必須 -->

## ✅ チェックリスト
- [ ] コードが正常に動作する
- [ ] テストが全て通る
- [ ] Lintエラーがない
- [ ] ドキュメントを更新した
- [ ] レビュー準備完了

## 🧪 テスト方法
<!-- どのようにテストすればよいか -->

## 💬 備考
<!-- レビュアーへの注意事項など -->
```

---

## 🔧 プロジェクト固有設定ファイル

### .github/CODEOWNERS

```
# デフォルトオーナー
* @sas-com/[team-name]

# フロントエンド
/frontend/ @sas-com/sas-product-frontend-team
/src/components/ @sas-com/sas-product-frontend-team

# バックエンド
/backend/ @sas-com/sas-product-backend-team
/api/ @sas-com/sas-product-backend-team

# インフラ
/infrastructure/ @sas-com/sas-platform-team
/.github/workflows/ @sas-com/sas-platform-team

# ドキュメント
/docs/ @sas-com/[project-manager]
*.md @sas-com/[project-manager]
```

### .editorconfig

```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space
indent_size = 2

[*.{md,markdown}]
trim_trailing_whitespace = false

[*.py]
indent_size = 4

[Makefile]
indent_style = tab
```

---

## 📋 作成チェックリスト

### 初期セットアップ時

- [ ] README.md を作成
- [ ] CONTRIBUTING.md を作成
- [ ] DEVELOPMENT.md を作成
- [ ] .gitignore を設定
- [ ] .github/ISSUE_TEMPLATE を作成
- [ ] .github/pull_request_template.md を作成
- [ ] .github/CODEOWNERS を設定
- [ ] ブランチ保護ルールを設定
- [ ] 必要なラベルを作成

### プロジェクト進行中

- [ ] ARCHITECTURE.md を更新
- [ ] API.md を更新
- [ ] DEPLOYMENT.md を作成
- [ ] CHANGELOG.md を維持
- [ ] ドキュメントの定期レビュー

### 納品前

- [ ] すべてのドキュメントが最新か確認
- [ ] セキュリティ情報が含まれていないか確認
- [ ] クライアント向けドキュメントを準備
- [ ] 引き継ぎドキュメントを作成

---

## 📚 参考リンク

- [全社共通GitHubガイドライン](https://github.com/sas-com/github-guidelines)
- [Markdownガイド](https://www.markdownguide.org/)
- [GitHub Docs](https://docs.github.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

## ⚠️ 注意事項

1. **全社共通ガイドラインを必ず確認**
2. **プロジェクト固有のルールは明確に文書化**
3. **機密情報は絶対に含めない**
4. **定期的にドキュメントを更新**
5. **新規参画者が理解できる内容に**

---

**© 2025 エス・エー・エス株式会社 - プロジェクト別ガイドライン作成マニュアル**