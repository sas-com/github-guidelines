# Visual Studio Code Git統合完全ガイド

**エス・エー・エス株式会社**
*VS CodeでのGit操作とGitHub連携の包括的マニュアル*
*最終更新: 2025年10月*

---

## 📚 目次

1. **[🎯 はじめに](#-はじめに)**
   - 本ガイドの目的
   - 対象者
   - 前提条件

2. **[🔧 第1章: VS Code Git機能の初期設定](#-第1章-vs-code-git機能の初期設定)**
   - Git統合の有効化
   - WSL2環境との連携設定
   - 認証情報の設定
   - Git設定の同期

3. **[📂 第2章: リポジトリのクローンと管理](#-第2章-リポジトリのクローンと管理)**
   - コマンドパレットからのクローン
   - SSH URLでのクローン
   - 複数リポジトリの管理
   - ワークスペースの活用

4. **[🎮 第3章: ソース管理ビューの基本操作](#-第3章-ソース管理ビューの基本操作)**
   - ソース管理パネルの構成
   - ステージング操作
   - 変更の確認と差分表示
   - ファイルの状態管理

5. **[✏️ 第4章: コミット作成とメッセージ規約](#-第4章-コミット作成とメッセージ規約)**
   - コミットメッセージの作成
   - SAS規約に準拠したテンプレート
   - 複数行メッセージの記述
   - コミット履歴の確認

6. **[🌿 第5章: ブランチ操作と管理](#-第5章-ブランチ操作と管理)**
   - ブランチの作成と切り替え
   - SASブランチ戦略の実践
   - リモートブランチの追跡
   - ブランチの削除と整理

7. **[📤 第6章: プッシュ・プル・同期](#-第6章-プッシュプル同期)**
   - 変更のプッシュ
   - リモートからのプル
   - 自動フェッチの設定
   - 同期操作のベストプラクティス

8. **[⚔️ 第7章: コンフリクト解決](#-第7章-コンフリクト解決)**
   - コンフリクトの検出
   - 3-way マージエディタの使用
   - インラインコンフリクト解決
   - マージツールの設定

9. **[🔌 第8章: GitLens拡張機能の活用](#-第8章-gitlens拡張機能の活用)**
   - GitLensのインストール
   - Blame情報の表示
   - コミット履歴の探索
   - ファイル履歴の追跡

10. **[🔄 第9章: GitHub Pull Requests拡張機能](#-第9章-github-pull-requests拡張機能)**
    - PR作成と管理
    - コードレビューの実施
    - Issue連携
    - CI/CDステータスの確認

11. **[🎨 第10章: おすすめ拡張機能と設定](#-第10章-おすすめ拡張機能と設定)**
    - 必須拡張機能
    - 生産性向上拡張機能
    - カスタマイズ設定
    - チーム共有設定

12. **[🛠️ 第11章: トラブルシューティング](#-第11章-トラブルシューティング)**
    - よくある問題と解決法
    - WSL2固有の問題
    - パフォーマンス最適化
    - デバッグ方法

---

## 🎯 はじめに

### 📌 本ガイドの目的

このガイドは、Visual Studio Code（VS Code）のGit統合機能を最大限活用し、エス・エー・エス株式会社の開発標準に従った効率的なGit操作を実現することを目的としています。

### 👥 対象者

- VS Codeを使用する全開発者
- Git操作をGUIで行いたい開発者
- WSL2環境でVS Codeを使用する開発者
- GitHub連携を効率化したい開発者

### ✅ 前提条件

以下の環境構築が完了していることを前提とします：

- ✅ WSL2のインストール
- ✅ Gitのインストールと初期設定
- ✅ GitHubアカウントの作成と2FA設定
- ✅ SSH鍵の設定と登録
- ✅ VS Codeのインストール

詳細は[GitHub環境構築ガイド](/home/kurosawa/github-guidelines/docs/onboarding/GITHUB_ENVIRONMENT_SETUP.md)を参照してください。

---

## 🔧 第1章: VS Code Git機能の初期設定

### 1.1 Git統合の有効化

VS CodeはデフォルトでGit統合が有効になっていますが、確認と最適化を行います。

#### 設定の確認

1. **コマンドパレットを開く**
   - ショートカット: `Ctrl+Shift+P`

2. **設定を開く**
   - 入力: `Preferences: Open Settings (UI)`
   - または: `Ctrl+,`

3. **Git設定を検索**
   - 検索ボックスに`git.enabled`を入力
   - 「Git: Enabled」にチェックが入っていることを確認

### 1.2 WSL2環境との連携設定

WSL2を使用した開発環境の設定：

#### WSL拡張機能のインストール

1. **拡張機能ビューを開く**
   - ショートカット: `Ctrl+Shift+X`
   - サイドバーの拡張機能アイコンをクリック

2. **WSL拡張機能を検索**
   - 検索: `WSL`
   - 「WSL」by Microsoft をインストール

3. **WSL2でVS Codeを起動**
   ```bash
   # WSL2ターミナルで実行
   cd ~/projects/your-project
   code .
   ```

#### WSL2でのGit設定確認

```bash
# WSL2内で実行
# Gitバージョン確認
git --version

# 設定確認
git config --global --list

# 必須設定（未設定の場合）
git config --global user.name "taro-yamada"
git config --global user.email "yamada@sas-com.com"
git config --global core.editor "code --wait"
```

### 1.3 認証情報の設定

#### SSH認証の確認

VS CodeはSSH鍵を自動的に使用しますが、以下を確認：

```bash
# WSL2ターミナルで実行
# SSH鍵の存在確認
ls -la ~/.ssh/

# SSHエージェントの起動
eval "$(ssh-agent -s)"

# SSH鍵の追加
ssh-add ~/.ssh/id_ed25519

# 接続テスト
ssh -T git@github.com
```

#### VS Code内での認証設定

1. **設定を開く**: `Ctrl+,`
2. **検索**: `git.terminalAuthentication`
3. **有効化**: チェックを入れる

### 1.4 Git設定の同期

#### settings.jsonの編集

```json
{
  // Git基本設定
  "git.enabled": true,
  "git.autofetch": true,
  "git.autofetchPeriod": 180,
  "git.confirmSync": false,
  "git.enableSmartCommit": true,
  "git.suggestSmartCommit": true,

  // コミット設定
  "git.inputValidation": "warn",
  "git.inputValidationLength": 72,
  "git.inputValidationSubjectLength": 50,

  // ブランチ設定
  "git.pruneOnFetch": true,
  "git.fetchOnPull": true,

  // 差分表示設定
  "diffEditor.ignoreTrimWhitespace": false,
  "diffEditor.renderSideBySide": true,

  // WSL2設定
  "remote.WSL.enabled": true,
  "terminal.integrated.defaultProfile.linux": "bash",

  // エディタ設定
  "files.eol": "\n",
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true
}
```

---

## 📂 第2章: リポジトリのクローンと管理

### 2.1 コマンドパレットからのクローン

#### 手順

1. **コマンドパレットを開く**: `Ctrl+Shift+P`

2. **Git: Clone を実行**
   - 入力: `Git: Clone`
   - Enterキーを押す

3. **リポジトリURLの入力**
   - SSH URL推奨: `git@github.com:sas-com/repository-name.git`
   - または「Clone from GitHub」を選択してGitHubから直接選択

4. **保存先の選択**
   - 推奨パス: `~/projects/client-name/`
   - フォルダを選択または作成

5. **クローン後の操作**
   - 「Open」をクリックして開く
   - 「Add to Workspace」でワークスペースに追加

### 2.2 SSH URLでのクローン

#### GitHubからSSH URLを取得

1. GitHubでリポジトリを開く
2. 「Code」ボタンをクリック
3. 「SSH」タブを選択
4. URLをコピー

#### VS Codeでクローン

```bash
# ターミナルビューで実行（Ctrl+`）
cd ~/projects
git clone git@github.com:sas-com/repository-name.git
cd repository-name
code .
```

### 2.3 複数リポジトリの管理

#### マルチルートワークスペース

1. **最初のリポジトリを開く**
   - File → Open Folder

2. **追加リポジトリを追加**
   - File → Add Folder to Workspace

3. **ワークスペースとして保存**
   - File → Save Workspace As
   - 名前: `sas-project.code-workspace`

#### ワークスペース設定ファイル

```json
{
  "folders": [
    {
      "path": "frontend-app",
      "name": "フロントエンド"
    },
    {
      "path": "backend-api",
      "name": "バックエンドAPI"
    },
    {
      "path": "shared-library",
      "name": "共通ライブラリ"
    }
  ],
  "settings": {
    "git.autofetch": true,
    "git.confirmSync": false
  }
}
```

### 2.4 リポジトリの切り替え

#### クイックアクセス

1. **ソース管理ビュー**: `Ctrl+Shift+G`
2. **リポジトリ選択**
   - 上部のドロップダウンから選択
   - または各リポジトリのセクションを展開

---

## 🎮 第3章: ソース管理ビューの基本操作

### 3.1 ソース管理パネルの構成

#### パネルを開く

- **ショートカット**: `Ctrl+Shift+G`
- **アクティビティバー**: 左側の分岐アイコン
- **View** → **SCM**

#### パネルの構成要素

```
ソース管理
├── リポジトリ名（現在のブランチ）
├── 変更 (Changes)
│   ├── 変更されたファイル（M）
│   ├── 新規ファイル（U）
│   └── 削除されたファイル（D）
├── ステージされた変更 (Staged Changes)
│   └── コミット準備済みファイル
└── マージの変更 (Merge Changes) ※コンフリクト時
```

### 3.2 ファイル状態の理解

#### ステータス記号

| 記号 | 意味 | 説明 |
|------|------|------|
| **M** | Modified | 変更されたファイル |
| **A** | Added | 新規追加（ステージ済み） |
| **D** | Deleted | 削除されたファイル |
| **U** | Untracked | 未追跡の新規ファイル |
| **C** | Conflicted | コンフリクトあり |
| **R** | Renamed | リネームされたファイル |
| **!** | Ignored | .gitignoreで除外 |

### 3.3 ステージング操作

#### 個別ファイルのステージング

1. **ファイル単位でステージ**
   - ファイル名の横の「+」をクリック
   - または右クリック → 「Stage Changes」

2. **部分的なステージング**
   - ファイルをクリックして差分表示
   - 変更行の横の「+」で行単位でステージ

#### 一括操作

```
すべてステージ: 「Changes」の横の「+」
すべてアンステージ: 「Staged Changes」の横の「-」
変更を破棄: ファイル右クリック → 「Discard Changes」
```

### 3.4 変更の確認と差分表示

#### インライン差分表示

1. **ファイルをクリック**
   - ソース管理ビューでファイル名をクリック
   - 差分エディタが開く

2. **表示モード切り替え**
   - サイドバイサイド: デフォルト
   - インライン: 右上のアイコンで切り替え

#### 差分ナビゲーション

```
次の変更: F7
前の変更: Shift+F7
変更をすべて確認: Ctrl+K, Ctrl+D
```

---

## ✏️ 第4章: コミット作成とメッセージ規約

### 4.1 コミットメッセージの作成

#### メッセージ入力欄

1. **ソース管理ビュー上部**
   - 「Message」テキストボックス
   - Ctrl+Enterでコミット

2. **SAS規約形式**
   ```
   <type>(<scope>): <subject>

   例：
   feat(auth): OAuth2.0ログイン機能を追加
   fix(api): ユーザー検索のタイムアウトを修正
   docs(readme): インストール手順を更新
   ```

### 4.2 コミットメッセージテンプレート

#### テンプレートファイルの作成

```bash
# ~/.gitmessage.txt
# <type>(<scope>): <subject>
#
# <body>
#
# <footer>

# Type:
# - feat: 新機能
# - fix: バグ修正
# - docs: ドキュメント
# - style: フォーマット
# - refactor: リファクタリング
# - test: テスト
# - chore: その他

# Scope: auth, api, ui, db, etc.

# Subject: 72文字以内で変更内容を記述

# Body: 詳細説明（任意）

# Footer: Issue参照など
# Closes #123
```

#### Git設定

```bash
git config --global commit.template ~/.gitmessage.txt
```

### 4.3 VS Code用スニペット設定

#### コミットメッセージスニペット

1. **File** → **Preferences** → **Configure User Snippets**
2. **New Global Snippets file** → `git-commit.code-snippets`

```json
{
  "SAS Commit Feature": {
    "prefix": "feat",
    "body": [
      "feat(${1:scope}): ${2:新機能の説明}",
      "",
      "${3:詳細説明}",
      "",
      "Closes #${4:issue}"
    ],
    "description": "新機能コミット"
  },
  "SAS Commit Fix": {
    "prefix": "fix",
    "body": [
      "fix(${1:scope}): ${2:バグ修正の説明}",
      "",
      "${3:問題の詳細と解決方法}",
      "",
      "Fixes #${4:issue}"
    ],
    "description": "バグ修正コミット"
  },
  "SAS Commit Docs": {
    "prefix": "docs",
    "body": [
      "docs(${1:scope}): ${2:ドキュメント更新の説明}"
    ],
    "description": "ドキュメント更新"
  }
}
```

### 4.4 コミット履歴の確認

#### タイムラインビュー

1. **エクスプローラーでファイルを選択**
2. **下部の「TIMELINE」パネルを展開**
3. **コミット履歴とローカル変更を確認**

#### Git Historyビュー（拡張機能）

```
コマンド: Git: View History
ショートカット: Alt+H（カスタム設定）
```

---

## 🌿 第5章: ブランチ操作と管理

### 5.1 ブランチの作成

#### コマンドパレットから作成

1. **コマンドパレット**: `Ctrl+Shift+P`
2. **入力**: `Git: Create Branch`
3. **ブランチ名入力**
   ```
   feature/auth/add-oauth-login
   bugfix/api/fix-timeout-issue
   ```

#### ステータスバーから作成

1. **左下のブランチ名をクリック**
2. **「Create new branch」を選択**
3. **命名規則に従って入力**

### 5.2 ブランチの切り替え

#### クイック切り替え

1. **ステータスバー左下**
   - 現在のブランチ名をクリック
   - リストから選択

2. **キーボードショートカット**
   - 設定: `Ctrl+K, Ctrl+S`
   - 「Git: Checkout to」にショートカット割り当て

### 5.3 リモートブランチの追跡

#### フェッチとプル

```
自動フェッチ: settings.jsonで設定
手動フェッチ: Ctrl+Shift+P → Git: Fetch
プル: Ctrl+Shift+P → Git: Pull
```

#### 新規リモートブランチの取得

1. **Git: Fetch From All Remotes**
2. **ブランチ切り替えメニューでリモートブランチを選択**
3. **自動的にローカルブランチが作成**

### 5.4 ブランチの削除と整理

#### ローカルブランチの削除

1. **コマンドパレット**: `Git: Delete Branch`
2. **削除するブランチを選択**
3. **確認ダイアログで「Delete」**

#### マージ済みブランチの整理

```bash
# ターミナルで実行
# マージ済みブランチ一覧
git branch --merged

# マージ済みブランチを削除
git branch -d feature/completed-feature

# リモートで削除済みのブランチを整理
git remote prune origin
```

---

## 📤 第6章: プッシュ・プル・同期

### 6.1 変更のプッシュ

#### 基本的なプッシュ

1. **ソース管理ビュー**
   - 「...」メニュー → 「Push」
   - またはステータスバーの同期アイコン

2. **初回プッシュ（新規ブランチ）**
   - 自動的に`--set-upstream`が実行される
   - リモートブランチが作成される

#### プッシュ設定

```json
{
  // 常に現在のブランチをプッシュ
  "git.pushMode": "simple",

  // タグも一緒にプッシュ
  "git.followTagsWhenSync": true,

  // プッシュ前に確認
  "git.confirmPush": true
}
```

### 6.2 リモートからのプル

#### プル戦略

1. **通常のプル**
   - `Ctrl+Shift+P` → `Git: Pull`
   - マージコミットが作成される

2. **リベースプル**
   - `Ctrl+Shift+P` → `Git: Pull (Rebase)`
   - 履歴をクリーンに保つ

#### 自動フェッチ設定

```json
{
  // 自動フェッチを有効化
  "git.autofetch": true,

  // フェッチ間隔（秒）
  "git.autofetchPeriod": 180,

  // プル時に自動フェッチ
  "git.fetchOnPull": true
}
```

### 6.3 同期操作

#### 同期ボタンの動作

ステータスバーの同期アイコン：
- **上向き矢印の数字**: プッシュ待ちコミット数
- **下向き矢印の数字**: プル待ちコミット数
- **クリック**: プルしてからプッシュ

#### 同期の自動化

```json
{
  // 同期時の確認を無効化
  "git.confirmSync": false,

  // コミット後に自動同期
  "git.postCommitCommand": "sync",

  // スマートコミット有効化
  "git.enableSmartCommit": true
}
```

---

## ⚔️ 第7章: コンフリクト解決

### 7.1 コンフリクトの検出

#### コンフリクト表示

ソース管理ビューでの表示：
```
マージの変更
├── ⚠️ file1.js (Conflicted)
├── ⚠️ file2.ts (Conflicted)
└── ⚠️ file3.md (Conflicted)
```

### 7.2 3-way マージエディタ

#### マージエディタの起動

1. **コンフリクトファイルをクリック**
2. **「Open in Merge Editor」を選択**

#### エディタの構成

```
┌─────────────────────────────────────┐
│  Incoming (Their Changes)           │
├─────────────────────────────────────┤
│  Current (Your Changes)             │
├─────────────────────────────────────┤
│  Result (Merged Output)             │
└─────────────────────────────────────┘
```

#### 操作方法

- **Accept Current**: 自分の変更を採用
- **Accept Incoming**: 相手の変更を採用
- **Accept Both**: 両方の変更を採用
- **手動編集**: Resultペインで直接編集

### 7.3 インラインコンフリクト解決

#### コンフリクトマーカー

```javascript
<<<<<<< HEAD (Current Change)
const config = {
  apiUrl: 'https://api.dev.example.com'
};
=======
const config = {
  apiUrl: 'https://api.staging.example.com'
};
>>>>>>> feature/update-config (Incoming Change)
```

#### インライン解決ボタン

- **Accept Current Change**: 現在の変更を採用
- **Accept Incoming Change**: 入ってくる変更を採用
- **Accept Both Changes**: 両方を採用
- **Compare Changes**: 差分を比較

### 7.4 コンフリクト解決後の操作

1. **すべてのコンフリクトを解決**
2. **ファイルをステージング**
3. **マージコミットを作成**
   ```
   Merge branch 'feature/branch-name' into dev

   # Conflicts:
   #   file1.js
   #   file2.ts
   ```

---

## 🔌 第8章: GitLens拡張機能の活用

### 8.1 GitLensのインストール

#### インストール手順

1. **拡張機能ビュー**: `Ctrl+Shift+X`
2. **検索**: `GitLens`
3. **「GitLens — Git supercharged」をインストール**

### 8.2 主要機能

#### Current Line Blame

エディタで現在行の情報を表示：
```
山田太郎, 2日前 • feat(auth): ユーザー認証を追加
```

#### File Annotations

ファイル全体のBlame情報：
- **Toggle File Blame**: `Alt+B`
- **Toggle File Changes**: `Alt+C`
- **Toggle File Heatmap**: `Alt+H`

### 8.3 GitLensビュー

#### サイドバービュー

```
GITLENS
├── Repositories
│   ├── Branches
│   ├── Remotes
│   ├── Stashes
│   └── Tags
├── File History
├── Line History
└── Compare
```

#### Interactive Rebase Editor

1. **コマンド**: `GitLens: Interactive Rebase Editor`
2. **視覚的にコミットを並び替え・編集**

### 8.4 カスタム設定

```json
{
  // Blame表示設定
  "gitlens.currentLine.enabled": true,
  "gitlens.currentLine.format": "${author}, ${agoOrDate} • ${message}",

  // CodeLens設定
  "gitlens.codeLens.enabled": true,
  "gitlens.codeLens.recentChange.enabled": true,
  "gitlens.codeLens.authors.enabled": true,

  // Heatmap設定
  "gitlens.heatmap.toggleMode": "file",

  // Blame Annotations
  "gitlens.blame.format": "${author|10} ${date} ${message|40}",
  "gitlens.blame.avatars": true
}
```

---

## 🔄 第9章: GitHub Pull Requests拡張機能

### 9.1 拡張機能のセットアップ

#### インストール

1. **拡張機能ビュー**: `Ctrl+Shift+X`
2. **検索**: `GitHub Pull Requests`
3. **「GitHub Pull Requests and Issues」をインストール**

#### GitHub認証

1. **サインイン通知をクリック**
2. **ブラウザでGitHub認証**
3. **VS Codeに戻って確認**

### 9.2 Pull Request作成

#### VS Code内でPR作成

1. **ソース管理ビュー**
2. **「...」メニュー → 「Create Pull Request」**
3. **PR情報を入力**

#### PRテンプレート

`.github/pull_request_template.md`:
```markdown
## 概要
変更内容の簡潔な説明

## 変更内容
- [ ] 機能A実装
- [ ] バグB修正
- [ ] ドキュメント更新

## テスト
- [ ] ユニットテスト追加/更新
- [ ] 統合テスト実施
- [ ] 手動テスト完了

## スクリーンショット
必要に応じて

## 関連Issue
Closes #123

## レビュアー
@sas-com/backend-team
```

### 9.3 コードレビューの実施

#### PR一覧の確認

1. **GitHub Pull Requestsビュー**（サイドバー）
2. **セクション**:
   - Waiting For My Review
   - Assigned To Me
   - Created By Me
   - All Open

#### レビューコメントの追加

1. **PRを選択して開く**
2. **変更ファイルの行番号横の「+」**
3. **コメント入力**
4. **「Start Review」または「Add Single Comment」**

#### レビューの完了

1. **「Review Changes」ボタン**
2. **レビューサマリー入力**
3. **レビュータイプ選択**:
   - Comment: コメントのみ
   - Approve: 承認
   - Request Changes: 修正要求

### 9.4 Issue連携

#### Issue一覧

```
GITHUB: ISSUES
├── My Issues
├── Created Issues
└── All Issues
```

#### Issueからブランチ作成

1. **Issueを右クリック**
2. **「Start Working on Issue」**
3. **自動的にブランチが作成**

---

## 🎨 第10章: おすすめ拡張機能と設定

### 10.1 必須拡張機能

#### Git/GitHub関連

| 拡張機能 | 説明 | 必須度 |
|----------|------|--------|
| **GitLens** | Git履歴・Blame表示 | ⭐⭐⭐ |
| **GitHub Pull Requests and Issues** | PR/Issue管理 | ⭐⭐⭐ |
| **Git Graph** | ビジュアルなGit履歴 | ⭐⭐⭐ |
| **GitHub Actions** | CI/CD表示 | ⭐⭐ |
| **GitHub Copilot** | AIコーディング支援 | ⭐⭐ |

#### 開発支援

| 拡張機能 | 説明 | 必須度 |
|----------|------|--------|
| **WSL** | WSL2連携 | ⭐⭐⭐ |
| **EditorConfig** | コードスタイル統一 | ⭐⭐⭐ |
| **Prettier** | コードフォーマッター | ⭐⭐⭐ |
| **ESLint** | JavaScript Linter | ⭐⭐ |
| **Code Spell Checker** | スペルチェック | ⭐⭐ |

### 10.2 生産性向上拡張機能

#### コミット支援

1. **Conventional Commits**
   - コミットメッセージ規約サポート
   - インテリセンス付き入力

2. **Git Commit Message Editor**
   - 専用エディタでコミットメッセージ作成
   - テンプレート管理

#### 視覚化ツール

1. **Git Graph**
   ```
   表示: View → Git Graph
   機能:
   - ブランチの視覚化
   - コミット検索
   - Cherry-pick操作
   ```

2. **GitHub Actions**
   - ワークフロー実行状況
   - ログ表示
   - 再実行機能

### 10.3 VS Code設定最適化

#### keybindings.json

```json
[
  {
    "key": "ctrl+g ctrl+s",
    "command": "workbench.view.scm"
  },
  {
    "key": "ctrl+g ctrl+c",
    "command": "git.commit"
  },
  {
    "key": "ctrl+g ctrl+p",
    "command": "git.push"
  },
  {
    "key": "ctrl+g ctrl+l",
    "command": "git.pull"
  },
  {
    "key": "ctrl+g ctrl+b",
    "command": "git.checkout"
  },
  {
    "key": "alt+b",
    "command": "gitlens.toggleFileBlame"
  }
]
```

#### ワークスペース推奨拡張機能

`.vscode/extensions.json`:
```json
{
  "recommendations": [
    "eamodio.gitlens",
    "github.vscode-pull-request-github",
    "mhutchie.git-graph",
    "github.vscode-github-actions",
    "ms-vscode-remote.remote-wsl",
    "editorconfig.editorconfig",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "streetsidesoftware.code-spell-checker"
  ]
}
```

### 10.4 チーム共有設定

#### .vscode/settings.json

```json
{
  // プロジェクト固有のGit設定
  "git.branchPrefix": "feature/",
  "git.inputValidation": "warn",
  "git.inputValidationLength": 72,

  // フォーマット設定
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",

  // ファイル設定
  "files.eol": "\n",
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true,

  // 除外設定
  "files.exclude": {
    "**/.git": true,
    "**/.DS_Store": true,
    "**/node_modules": true,
    "**/dist": true
  },

  // 検索除外
  "search.exclude": {
    "**/node_modules": true,
    "**/bower_components": true,
    "**/dist": true,
    "**/.git": true
  }
}
```

---

## 🛠️ 第11章: トラブルシューティング

### 11.1 よくある問題と解決法

#### Git認証エラー

**問題**: `Permission denied (publickey)`

**解決方法**:
```bash
# SSH鍵の確認
ls -la ~/.ssh/

# SSHエージェント起動
eval "$(ssh-agent -s)"

# 鍵の追加
ssh-add ~/.ssh/id_ed25519

# 接続テスト
ssh -T git@github.com
```

#### リモートリポジトリに接続できない

**問題**: `Could not read from remote repository`

**解決方法**:
1. SSH接続の確認
2. リモートURLの確認: `git remote -v`
3. URLの修正: `git remote set-url origin git@github.com:sas-com/repo.git`

### 11.2 WSL2固有の問題

#### ファイルパーミッションの問題

**問題**: ファイルシステムでパーミッションエラー

**解決方法**:
```bash
# WSL2設定ファイル作成
sudo touch /etc/wsl.conf

# 設定追加
sudo bash -c 'cat > /etc/wsl.conf << EOF
[automount]
enabled = true
options = "metadata,umask=22,fmask=11"
EOF'

# WSL2再起動
wsl --shutdown
```

#### パフォーマンスの問題

**問題**: `/mnt/c/`でGit操作が遅い

**解決方法**:
```bash
# WSL2ファイルシステムを使用
cd ~/projects  # /mnt/c/ではなく

# プロジェクトをWSL2内にクローン
git clone git@github.com:sas-com/repo.git
```

### 11.3 VS Code設定の問題

#### 拡張機能が動作しない

**確認事項**:
1. WSL2でVS Codeを起動しているか
2. 拡張機能がWSL側にインストールされているか
3. 左下に「WSL: Ubuntu」と表示されているか

**解決方法**:
```bash
# WSL2内から起動
cd ~/projects/your-project
code .
```

#### Git統合が無効

**解決方法**:
1. 設定を開く: `Ctrl+,`
2. 「git.enabled」を検索
3. チェックボックスを有効化

### 11.4 デバッグとログ

#### Gitログの確認

```bash
# Gitのデバッグモード有効化
GIT_TRACE=1 git pull

# SSH接続のデバッグ
ssh -vT git@github.com

# Git設定の確認
git config --list --show-origin
```

#### VS Codeログ

1. **出力パネル**: `Ctrl+Shift+U`
2. **ドロップダウンから「Git」を選択**
3. **エラーメッセージを確認**

#### 拡張機能のログ

```
開発者ツール: Ctrl+Shift+I
コンソールタブでエラー確認
```

---

## 📊 パフォーマンス最適化

### Git設定の最適化

```bash
# パフォーマンス向上設定
git config --global core.preloadindex true
git config --global core.fscache true
git config --global gc.auto 256

# 大規模リポジトリ用
git config --global feature.manyFiles true
git config --global index.threads true
```

### VS Code設定の最適化

```json
{
  // 検索パフォーマンス
  "search.followSymlinks": false,
  "search.useIgnoreFiles": true,

  // Git パフォーマンス
  "git.autorefresh": false,
  "git.decorations.enabled": false,

  // ファイル監視
  "files.watcherExclude": {
    "**/.git/objects/**": true,
    "**/.git/subtree-cache/**": true,
    "**/node_modules/**": true,
    "**/dist/**": true,
    "**/.next/**": true
  }
}
```

---

## 🎯 ベストプラクティス

### 日常的なワークフロー

1. **朝の作業開始時**
   ```
   1. メインブランチを最新化
   2. 作業ブランチを作成
   3. GitLensで最近の変更確認
   ```

2. **コミット時**
   ```
   1. 差分を確認
   2. 関連する変更のみステージング
   3. 意味のある単位でコミット
   4. SAS規約に従ったメッセージ
   ```

3. **PR作成前**
   ```
   1. ローカルでテスト実施
   2. コミット履歴の整理
   3. 最新のベースブランチを取り込み
   4. コンフリクトがあれば解決
   ```

### セキュリティ考慮事項

- 機密情報のコミット防止
- `.gitignore`の適切な設定
- 認証情報の管理
- SSH鍵の定期的な更新

---

## 📚 関連ドキュメント

### 必読ドキュメント
- [GitHub環境構築ガイド](../onboarding/GITHUB_ENVIRONMENT_SETUP.md)
- [コミット規約ガイドライン](../workflow/COMMIT_CONVENTION_GUIDE.md)
- [ブランチ管理ルール](../workflow/BRANCH_MANAGEMENT_RULES.md)
- [新規参画者向けオンボーディング](../onboarding/ONBOARDING.md)

### 外部リソース
- [VS Code Git Documentation](https://code.visualstudio.com/docs/editor/versioncontrol)
- [GitLens Documentation](https://github.com/eamodio/vscode-gitlens)
- [GitHub VS Code Extension](https://vscode.github.com/)

---

## 🔄 更新履歴

- **2025-10-11**: 初版作成（v1.0.0）
  - VS Code Git統合の包括的ガイド作成
  - WSL2環境での設定を含む
  - SAS組織ルールに準拠

---

**© 2025 エス・エー・エス株式会社 - Visual Studio Code Git統合完全ガイド**