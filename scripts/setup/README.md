# SAS コミット規約バリデーション - セットアップガイド

**エス・エー・エス株式会社**  
*開発者向けコミットメッセージバリデーションツール導入ガイド*

## 📋 概要

このガイドでは、SAS株式会社のコミット規約に基づくバリデーションツールチェーンのセットアップ方法を説明します。

## 🎯 提供される機能

### ✨ 主要機能
- **リアルタイムバリデーション**: コミット時の自動検証
- **スマートテンプレート**: 変更内容に基づいた適切なテンプレート提供
- **セキュリティチェック**: 機密情報の検出・防止
- **インタラクティブ支援**: 規約違反の具体的な修正案提示
- **CI/CD統合**: Pull Request での自動チェック
- **品質メトリクス**: コミット統計の可視化

### 🔧 ツール構成
- **Git Hooks**: commit-msg, prepare-commit-msg
- **Commitlint**: Conventional Commits準拠チェック
- **Husky**: Git hooks管理
- **GitHub Actions**: CI/CDでの自動バリデーション
- **VS Code拡張**: エディタ統合

## 🚀 クイックスタート

### 1. 基本セットアップ（推奨）

```bash
# 1. リポジトリをクローン
git clone <repository-url>
cd <repository-name>

# 2. 自動セットアップ実行
./scripts/setup/install-hooks.sh

# 3. Node.js依存関係インストール（オプション）
npm install
```

### 2. 手動セットアップ

```bash
# Git hooks を手動でインストール
cp scripts/commit-hooks/commit-msg .git/hooks/
cp scripts/commit-hooks/prepare-commit-msg .git/hooks/
chmod +x .git/hooks/commit-msg .git/hooks/prepare-commit-msg

# コミットテンプレート設定
git config commit.template .gitmessage

# commitlint設定（Node.js環境の場合）
npm install -g @commitlint/cli @commitlint/config-conventional
```

## 📚 詳細セットアップ手順

### Node.js環境セットアップ

```bash
# 1. Node.js バージョン確認 (16.0.0以上推奨)
node --version

# 2. 依存関係インストール
npm install

# 3. Husky初期化
npx husky install

# 4. 開発環境セットアップ
npm run setup:dev
```

### VS Code拡張機能

推奨拡張機能が自動で提案されます：

```json
{
  "recommendations": [
    "vivaxy.vscode-conventional-commits",
    "joshbolduc.commitlint",
    "ms-vscode.vscode-json",
    "redhat.vscode-yaml"
  ]
}
```

### GitHub Actions設定

Pull Requestで自動実行される機能：
- コミットメッセージバリデーション
- セキュリティスキャン（機密情報検出）
- 品質メトリクス生成
- PRコメントでの結果表示

## 🎮 使用方法

### 基本的なコミット作業

```bash
# 1. 変更を作成
echo "新機能" > feature.txt
git add .

# 2. コミット作成（テンプレートが自動提供）
git commit
# → エディタが開き、スマートテンプレートが表示される

# 3. バリデーション結果確認
# → 規約違反があれば具体的な修正案が表示される
```

### インタラクティブコミット（推奨）

```bash
# Commitizenを使用したガイド付きコミット
npm run commit

# または
npx cz
```

### VS Code統合

1. **コマンドパレット** (`Ctrl+Shift+P`) を開く
2. **"SAS"** で検索
3. 利用可能なタスクを選択：
   - `SAS: Install Git Hooks`
   - `SAS: Interactive Commit`
   - `SAS: Validate Commit Message`

## 🔍 バリデーション項目

### 基本フォーマット
- Conventional Commits形式準拠
- 文字数制限（subject: 72文字、本文: 100文字/行）
- 必須フィールド検証

### タイプ検証
```bash
# 有効なタイプ
feat fix docs style refactor test chore
security perf build ci revert hotfix

# よくある間違いの自動修正案
update → fix または feat
add → feat
bug → fix
```

### スコープ検証
```bash
# 推奨スコープ例
auth api ui db payment notification
user product order admin config
header sidebar modal form table
```

### セキュリティチェック
- APIキー、パスワード、トークンの検出
- 個人情報の警告
- 長い文字列パターンの検証

### 日本語対応
- 丁寧語の使用警告（「〜しました」→「〜する」）
- 命令形チェック
- 適切な文字数制限

## 🛠️ カスタマイズ

### プロジェクト固有の設定

#### 1. スコープのカスタマイズ
`.commitlintrc.json` を編集：

```json
{
  "rules": {
    "scope-enum": [1, "always", [
      "auth", "api", "ui",
      "your-custom-scope"
    ]]
  }
}
```

#### 2. 独自バリデーションルール追加
`scripts/validation/validate-commit-message.sh` を編集：

```bash
# プロジェクト固有のチェックを追加
check_project_specific() {
    # カスタムロジック
}
```

#### 3. テンプレートのカスタマイズ
`.gitmessage` を編集して、プロジェクト固有のテンプレートを設定。

### チーム固有設定

#### 1. 組織レベルの設定
```bash
# 組織全体での設定
git config --global commit.template /path/to/organization/.gitmessage
```

#### 2. プロジェクトテンプレート作成
```bash
# プロジェクト専用テンプレート
cp .gitmessage .gitmessage.project
# プロジェクト固有の項目を追加編集
```

## 🚨 トラブルシューティング

### よくある問題

#### 1. Hooks が実行されない
```bash
# 実行権限確認
ls -la .git/hooks/commit-msg
# 実行権限付与
chmod +x .git/hooks/commit-msg
```

#### 2. Node.js依存関係エラー
```bash
# Node.jsバージョン確認
node --version  # 16.0.0以上必要

# 依存関係再インストール
rm -rf node_modules package-lock.json
npm install
```

#### 3. commitlint設定エラー
```bash
# 設定ファイル検証
npx commitlint --print-config

# 手動テスト
echo "feat: テストメッセージ" | npx commitlint
```

#### 4. VS Code拡張機能が動作しない
1. 推奨拡張機能をインストール
2. VS Code再起動
3. ワークスペース設定確認

### デバッグ方法

#### 1. バリデーションスクリプトのテスト
```bash
# テストメッセージでバリデーション
echo "feat(test): テストメッセージ" > /tmp/test-msg
./scripts/validation/validate-commit-message.sh /tmp/test-msg
```

#### 2. Hooks動作確認
```bash
# Hook実行テスト
echo "test message" | .git/hooks/commit-msg /dev/stdin
```

#### 3. 詳細ログ出力
```bash
# デバッグモードでスクリプト実行
bash -x ./scripts/validation/validate-commit-message.sh /tmp/test-msg
```

## 🔄 更新・メンテナンス

### 定期更新手順

```bash
# 1. 最新版取得
git pull origin main

# 2. Hooks再インストール
./scripts/setup/install-hooks.sh

# 3. 依存関係更新
npm update
```

### バージョン管理

| コンポーネント | バージョン管理方法 |
|---------------|------------------|
| Git Hooks | リポジトリでバージョン管理 |
| commitlint設定 | `.commitlintrc.json` |
| VS Code設定 | `.vscode/` ディレクトリ |
| GitHub Actions | `.github/workflows/` |

## 📊 使用状況の確認

### コミット統計

```bash
# 月間統計
npm run docs:commit  # 統計表示コマンド

# または手動確認
git log --oneline --grep="^feat" --since="1 month ago" | wc -l  # feat数
git log --oneline --grep="^fix" --since="1 month ago" | wc -l   # fix数
```

### バリデーション結果確認

GitHub ActionsのワークフローでPR毎の詳細レポートが自動生成されます。

## 📞 サポート

### 問い合わせ先

- **技術サポート**: github@sas-com.com
- **緊急時**: github@sas-com.com
- **ドキュメント**: [COMMIT_CONVENTION_GUIDE.md](../../COMMIT_CONVENTION_GUIDE.md)

### よくある質問

#### Q: 既存プロジェクトに導入する際の注意点は？

A: 段階的導入を推奨：
1. まずwarningレベルで導入
2. チーム全体での慣れを確認
3. errorレベルに変更

#### Q: マージコミットやリバートコミットはどう扱われる？

A: 以下のコミットは自動でバリデーションをスキップ：
- Merge commits
- Revert commits
- fixup/squash commits

#### Q: 日本語コミットメッセージの制限は？

A: 以下の制限があります：
- 丁寧語禁止（〜しました、〜です）
- 命令形推奨
- 72文字制限（英語基準だが、日本語では50文字程度推奨）

---

**更新履歴**
- 2025-09-10: 初版作成
- 2025-09-10: VS Code統合機能追加
- 2025-09-10: GitHub Actions統合完了