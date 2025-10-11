# Eclipse上でのGit利用ガイドライン

**エス・エー・エス株式会社**
*Eclipse統合開発環境でのEGit完全活用ガイド*
*最終更新: 2025年10月11日*

---

## 📚 目次

1. [🎯 はじめに](#-はじめに)
2. [🔧 環境準備](#-環境準備)
3. [📂 Git Repositoriesビューの使い方](#-git-repositoriesビューの使い方)
4. [📝 Git Stagingビューの使い方](#-git-stagingビューの使い方)
5. [🚀 基本操作](#-基本操作)
6. [🌿 ブランチ操作](#-ブランチ操作)
7. [🔍 Historyビュー活用](#-historyビュー活用)
8. [⚡ コンフリクト解決](#-コンフリクト解決)
9. [🌐 リモートリポジトリ管理](#-リモートリポジトリ管理)
10. [🔌 推奨プラグイン](#-推奨プラグイン)
11. [🛠️ トラブルシューティング](#️-トラブルシューティング)
12. [📋 チェックリスト](#-チェックリスト)

---

## 🎯 はじめに

### 📌 本ガイドの目的

EclipseのEGit統合機能を使用して、効率的にGitバージョン管理を行うための完全ガイドです。コマンドライン操作なしで、Eclipse内で全てのGit操作を完結させることができます。

### 🎯 対象者

- EclipseでJava開発を行うエンジニア
- コマンドライン操作に不慣れな開発者
- GUIベースでGit操作を行いたい方
- WSL2環境との連携が必要な開発者

### ⚠️ 前提条件

- Eclipse IDE (2024-06以降推奨)
- EGitプラグインインストール済み（通常はEclipse標準装備）
- GitHubアカウント設定完了（2FA有効）
- SSH鍵設定完了またはHTTPS認証設定済み

---

## 🔧 環境準備

### 2.1 EGitプラグインの確認とインストール

#### EGit存在確認

1. **Eclipseメニューバー → Help → About Eclipse IDE**
2. **Installation Details をクリック**
3. **Installed Software タブで「EGit」を検索**
   - バージョン6.0以降が推奨
   - 見つからない場合は以下の手順でインストール

#### EGitインストール手順（必要な場合）

1. **Help → Install New Software...**
2. **Work with: プルダウンから「--All Available Sites--」を選択**
3. **フィルターに「EGit」と入力**
4. **以下の項目にチェック:**
   - Eclipse Git Team Provider
   - Eclipse GitHub integration with task focused interface
   - Git integration for Eclipse - Gitflow support
5. **Next → Next → I accept → Finish**
6. **Eclipse再起動**

### 2.2 Git設定（Eclipse内）

#### グローバル設定

1. **Window → Preferences（Mac: Eclipse → Preferences）**
2. **Team → Git → Configuration を選択**
3. **User Settings タブで Add Entry をクリック**

設定すべき項目:

| Key | Value | 説明 |
|-----|-------|------|
| user.name | taro-yamada | GitHubユーザー名と同じ形式 |
| user.email | yamada@sas-com.com | 会社メールアドレス |
| core.autocrlf | input | 改行コード自動変換 |
| core.quotepath | false | 日本語ファイル名対応 |
| push.default | current | プッシュ戦略 |
| pull.rebase | false | プル時の動作 |

#### SSH鍵の設定（Eclipse内）

1. **Window → Preferences → General → Network Connections → SSH2**
2. **General タブ:**
   - SSH2 home: `${user.home}/.ssh`
   - Private keys: `id_ed25519` を追加
3. **Key Management タブ:**
   - Load Existing Key... で既存のSSH鍵を読み込み
   - またはGenerate RSA Key... で新規作成

#### SSH鍵のGitHub登録時のタイトル形式

GitHubにSSH鍵を登録する際は、以下の命名規則に従ってください：

- **Title**: SAS-PC-R-XXX-Eclipse（PC識別ID-Eclipse）
  - 例: `SAS-PC-R-001-Eclipse`（PC識別IDがR-001の場合）
  - 例: `SAS-PC-R-123-Eclipse`（PC識別IDがR-123の場合）
  - **注意**: XXXの部分は実際のPC識別IDに置き換えてください

### 2.3 WSL2環境との連携設定（Windows環境の場合）

#### WSL2内のプロジェクトをEclipseで開く

1. **File → Import → Git → Projects from Git**
2. **Clone URI を選択**
3. **URI設定:**
   ```
   Location: \\wsl$\Ubuntu\home\yourname\projects\repository-name
   ```
4. **既存のWSL2環境Git設定を活用**

#### 注意事項

- WSL2ファイルシステム直接編集は推奨されない
- Windows側にクローンして開発することを推奨
- パフォーマンスを重視する場合はWindows側で作業

---

## 📂 Git Repositoriesビューの使い方

### 3.1 ビューの表示

1. **Window → Show View → Other...**
2. **Git → Git Repositories を選択**
3. **Open をクリック**

### 3.2 リポジトリの追加

#### 既存リポジトリの追加

1. **Git Repositoriesビュー内で右クリック**
2. **Add a Git Repository... を選択**
3. **Directory: でローカルリポジトリを選択**
4. **Finish**

#### リポジトリのクローン

1. **Git Repositoriesビュー内で「Clone a Git repository」アイコンをクリック**
2. **Clone URI を選択 → Next**
3. **URIフィールドにGitHubリポジトリURLを入力:**
   ```
   https://github.com/sas-com/repository-name.git
   ```
4. **認証情報を入力:**
   - User: GitHubユーザー名
   - Password: Personal Access Token（パスワードではない）
5. **Branch Selection: 必要なブランチを選択**
6. **Local Destination: ローカル保存先を指定**
7. **Finish**

### 3.3 リポジトリビューの構造理解

```
Repository Name [master] - C:\workspace\repo
├── Branches
│   ├── Local
│   │   ├── master
│   │   ├── dev
│   │   └── feature/new-feature
│   └── Remote Tracking
│       ├── origin/master
│       ├── origin/dev
│       └── origin/staging
├── Tags
│   └── v1.0.0
├── References
├── Remotes
│   └── origin
│       └── https://github.com/sas-com/repo.git
└── Working Tree
    └── プロジェクトファイル一覧
```

### 3.4 リポジトリ操作

#### よく使う右クリックメニュー

| 操作 | 説明 | 使用場面 |
|------|------|----------|
| Pull... | リモートから最新を取得 | 作業開始時 |
| Fetch from Upstream | メタデータのみ取得 | 変更確認時 |
| Push... | リモートへ送信 | コミット後 |
| Switch To | ブランチ切り替え | 作業切り替え |
| Reset... | 特定コミットへ戻る | 取り消し時 |
| Show In → History | 履歴表示 | 変更追跡 |

---

## 📝 Git Stagingビューの使い方

### 4.1 ビューの表示と構成

1. **Window → Show View → Other...**
2. **Git → Git Staging を選択**

### 4.2 ビューの構成要素

```
Git Staging ビュー
├── Unstaged Changes（未ステージング変更）
│   ├── Modified: ファイル名
│   ├── Added: 新規ファイル
│   └── Deleted: 削除ファイル
├── Staged Changes（ステージング済み変更）
│   └── ステージング済みファイル一覧
├── Commit Message（コミットメッセージ）
│   ├── Subject line（1行目）
│   └── Message body（詳細）
└── コミット情報
    ├── Author: 名前 <メール>
    ├── Committer: 名前 <メール>
    └── Amend previous commit（チェックボックス）
```

### 4.3 ステージング操作

#### ファイルのステージング

1. **Unstaged Changes から Staged Changes へ移動:**
   - ファイルを選択 → ドラッグ&ドロップ
   - または右クリック → Add to Index
   - または「+」アイコンをクリック

2. **部分的なステージング（行単位）:**
   - ファイルをダブルクリック → Compare Editor開く
   - 変更行を選択 → 右クリック → Add to Index

#### ステージング解除

1. **Staged Changes から Unstaged Changes へ:**
   - ファイルを選択 → ドラッグ&ドロップ
   - または右クリック → Remove from Index
   - または「-」アイコンをクリック

### 4.4 コミットメッセージ作成

#### SAS社コミット規約準拠

```
Subject line（72文字以内）:
<type>(<scope>): <description>

例:
feat(auth): OAuth2.0ログイン機能を追加
fix(api): ユーザー検索時のバリデーションエラーを修正
docs(readme): インストール手順を更新
```

#### メッセージテンプレート設定

1. **Preferences → Team → Git → Commit Message**
2. **Template を設定:**
```
<type>(<scope>):

# type: feat, fix, docs, style, refactor, test, chore
# scope: auth, api, ui, db等

# 詳細説明（必要に応じて）:

# Issue番号（該当する場合）:
# Closes #
```

### 4.5 コミット実行

1. **ステージング済みファイルを確認**
2. **コミットメッセージを入力**
3. **Commit ボタンをクリック**
   - Commit: ローカルリポジトリへコミット
   - Commit and Push: コミット後即座にプッシュ

---

## 🚀 基本操作

### 5.1 プロジェクトのGit管理開始

#### 新規プロジェクトをGit管理下に置く

1. **Project Explorer でプロジェクトを右クリック**
2. **Team → Share Project...**
3. **Git を選択 → Next**
4. **Create Repository または Use or create repository を選択**
5. **Finish**

#### .gitignore設定

1. **プロジェクトルートで右クリック → New → File**
2. **ファイル名: .gitignore**
3. **Eclipse/Java用標準設定:**
```gitignore
# Eclipse
.classpath
.project
.settings/
bin/
tmp/
*.tmp
*.bak
*.swp
*~.nib
local.properties

# Java
*.class
*.jar
*.war
*.ear
*.zip
*.tar.gz
*.rar
target/
build/

# Maven
pom.xml.tag
pom.xml.releaseBackup
pom.xml.versionsBackup
pom.xml.next
release.properties

# Gradle
.gradle/
gradle-app.setting
!gradle-wrapper.jar

# IDE
*.iml
.idea/
*.ipr
*.iws
out/

# OS
.DS_Store
Thumbs.db
desktop.ini

# Logs
*.log
logs/

# SAS社固有
*.env
secrets/
credentials/
```

### 5.2 日常的な作業フロー

#### 作業開始時

1. **Git Repositories ビューでリポジトリ右クリック**
2. **Pull... を選択**
3. **Remote: origin、Reference: refs/heads/dev を確認**
4. **Pull をクリック**
5. **結果確認（Pull Result ダイアログ）**

#### コーディング作業

1. **通常通りEclipse上で開発**
2. **Package Explorer の変更アイコンを確認:**
   - `>` : 変更あり
   - `+` : 新規追加
   - `-` : 削除
   - `?` : 未追跡
3. **定期的にローカルコミット**

#### 作業終了時

1. **Git Staging ビューで変更確認**
2. **ファイルをステージング**
3. **コミットメッセージ入力**
4. **Commit and Push**

### 5.3 変更の取り消し

#### 未コミットの変更を破棄

1. **Project Explorer で変更ファイルを右クリック**
2. **Replace With → HEAD Revision**
3. **確認ダイアログで OK**

#### 直前のコミットを修正（Amend）

1. **Git Staging ビューで変更をステージング**
2. **Amend previous commit にチェック**
3. **前回のコミットメッセージが表示される**
4. **必要に応じて修正**
5. **Commit**

---

## 🌿 ブランチ操作

### 6.1 ブランチの作成

#### GUIからの新規ブランチ作成

1. **Git Repositories ビュー → Branches → Local で右クリック**
2. **Create Branch...**
3. **設定項目:**
   - Source: 基となるブランチ（通常はdev）
   - Branch name: SAS命名規則に従う
     ```
     feature/auth/add-oauth-login
     bugfix/api/fix-validation-error
     hotfix/critical/security/fix-sql-injection
     ```
   - Configure upstream for push and pull: チェック
   - Check out new branch: チェック（作成後切り替え）
4. **Finish**

#### Quick Access経由

1. **Ctrl + 3（Quick Access）**
2. **「create branch」と入力**
3. **Git Create Branch を選択**

### 6.2 ブランチの切り替え

#### Checkout操作

1. **Git Repositories ビュー → Branches**
2. **切り替えたいブランチを右クリック**
3. **Checkout を選択**
4. **現在のブランチに「✓」マークが表示される**

#### ツールバーから切り替え

1. **Eclipseツールバーの Git アイコン横のプルダウン**
2. **Switch to → ブランチ名を選択**

### 6.3 ブランチのマージ

#### 基本的なマージ手順

1. **マージ先ブランチにチェックアウト**
2. **Git Repositories ビューでマージ先ブランチを右クリック**
3. **Merge...**
4. **マージ元ブランチを選択**
5. **Merge options:**
   - Commit: マージコミットを作成
   - Fast-forward when possible: 可能な場合FF
   - Squash: スカッシュマージ
6. **Merge**

#### マージ結果の確認

```
Merge Result ダイアログ
├── Status: Merged / Fast-forwarded / Conflicting
├── Merged commits: マージされたコミット一覧
└── Result: 成功/失敗メッセージ
```

### 6.4 ブランチの削除

#### ローカルブランチ削除

1. **Git Repositories → Branches → Local**
2. **削除したいブランチを右クリック**
3. **Delete... を選択**
4. **確認ダイアログで OK**
   - Force delete required: 未マージ変更がある場合

#### リモートブランチ削除

1. **Git Repositories → Remotes → origin**
2. **削除したいブランチを右クリック**
3. **Delete Remote Branch を選択**
4. **確認後、リモートから削除**

### 6.5 リベース操作

#### インタラクティブリベース

1. **History ビューで基準コミットを選択**
2. **右クリック → Rebase → Interactive Rebase**
3. **Rebase Interactive View が開く:**
   - Pick: コミットを採用
   - Edit: コミットを編集
   - Squash: 前のコミットと結合
   - Fixup: Squashと同じだがメッセージ破棄
   - Skip: コミットをスキップ
4. **Start をクリック**
5. **コンフリクトがあれば解決**
6. **Continue Rebase**

---

## 🔍 Historyビュー活用

### 7.1 Historyビューの表示

1. **ファイルまたはプロジェクトを右クリック**
2. **Team → Show in History**
3. **または Window → Show View → Other... → Team → History**

### 7.2 ビューの機能説明

#### 表示カスタマイズ

ツールバーアイコン:
- **Show All Branches**: 全ブランチの履歴表示
- **Show First Parent Only**: マージコミットの第一親のみ
- **Follow Renames**: ファイル名変更を追跡
- **Show Additional Refs**: タグ等の参照表示
- **Filter Settings**: 表示フィルター設定

#### コミット情報表示

```
History View レイアウト
├── グラフ表示エリア（ブランチの分岐・マージを視覚化）
├── コミット一覧
│   ├── Graph: ビジュアル表示
│   ├── Description: コミットメッセージ
│   ├── Date: コミット日時
│   ├── Author: 作成者
│   └── Committer: コミット実行者
└── 詳細パネル
    ├── Commit: SHA-1ハッシュ
    ├── Parents: 親コミット
    ├── Message: 完全なコミットメッセージ
    └── Diff: 変更内容
```

### 7.3 Annotate（Blame）機能

#### ファイルの変更履歴追跡

1. **エディタでファイルを開く**
2. **右クリック → Team → Show Annotations**
3. **左マージンに履歴情報表示:**
   - コミットID（短縮形）
   - 作成者名
   - 変更日時
4. **履歴上でホバー: 詳細情報ポップアップ**
5. **履歴をクリック: History ビューでコミット選択**

#### Quick Diff機能

1. **Preferences → General → Editors → Text Editors → Quick Diff**
2. **Enable quick diff: チェック**
3. **Use this reference source: Git HEAD**
4. **エディタ左マージンに変更表示:**
   - 緑: 追加行
   - 黄: 変更行
   - 赤（三角）: 削除位置

### 7.4 コミット間の比較

#### 2つのコミット比較

1. **History ビューで最初のコミットを選択**
2. **Ctrl押しながら2つ目のコミットを選択**
3. **右クリック → Compare with Each Other**
4. **Compare Editor が開く**

#### 作業ツリーとの比較

1. **History ビューでコミットを選択**
2. **右クリック → Compare with Workspace**
3. **現在の作業内容との差分表示**

---

## ⚡ コンフリクト解決

### 8.1 コンフリクトの検出

#### Pull/Merge時のコンフリクト表示

```
Merge Result ダイアログ
Status: Conflicting
Conflicting files:
├── src/main/java/UserService.java
├── src/test/java/UserServiceTest.java
└── README.md
```

#### Project Explorerでの表示

- コンフリクトファイルに赤い菱形アイコン
- ファイル名に「Conflicting」ラベル

### 8.2 Merge Toolの使用

#### 3-wayマージエディタ

1. **コンフリクトファイルを右クリック**
2. **Team → Merge Tool**
3. **3つのペインが表示:**
   ```
   左ペイン: ローカル変更（yours）
   中央ペイン: マージ結果（編集可能）
   右ペイン: リモート変更（theirs）
   ```

#### マージ操作

マージツールバーボタン:
- **Copy Current Change from Left to Right**: 左の変更を採用
- **Copy Current Change from Right to Left**: 右の変更を採用
- **Copy All from Left to Right**: 全て左を採用
- **Copy All from Right to Left**: 全て右を採用
- **Next Difference**: 次の差分へ
- **Previous Difference**: 前の差分へ

### 8.3 手動でのコンフリクト解決

#### コンフリクトマーカーの理解

```java
<<<<<<< HEAD
    // ローカルの変更内容
    public String getUserName() {
        return this.name;
    }
=======
    // リモートの変更内容
    public String getUsername() {
        return this.username;
    }
>>>>>>> branch-name
```

#### 解決手順

1. **エディタでファイルを開く**
2. **コンフリクトマーカーを探す（<<<<<<<）**
3. **必要な変更を残し、不要部分とマーカーを削除**
4. **ファイルを保存**
5. **Git Staging ビューでAdd to Index**
6. **全コンフリクト解決後、Continue または Commit**

### 8.4 コンフリクト解決のベストプラクティス

#### 予防策

1. **定期的にpull/fetch実行**
2. **作業前に最新化**
3. **小さい単位でコミット**
4. **長期間のブランチ分離を避ける**

#### 解決時の注意点

1. **両方の変更意図を理解**
2. **テストコードも含めて確認**
3. **解決後は必ずビルド・テスト実行**
4. **チームメンバーと相談（必要時）**

---

## 🌐 リモートリポジトリ管理

### 9.1 リモート設定

#### リモートの追加

1. **Git Repositories → Remotes で右クリック**
2. **Create Remote...**
3. **Remote name: upstream（フォーク元等）**
4. **Configure push/fetch: チェック**
5. **URIを設定**

#### 複数リモートの管理

```
Remotes
├── origin (自分のフォーク)
│   ├── Fetch: https://github.com/yourname/repo.git
│   └── Push: https://github.com/yourname/repo.git
└── upstream (オリジナルリポジトリ)
    └── Fetch: https://github.com/sas-com/repo.git
```

### 9.2 Push操作

#### 標準Push

1. **Git Repositories → リポジトリ右クリック**
2. **Push to Origin... または Push...**
3. **Push設定:**
   - Remote: origin
   - Branch: 現在のブランチ
   - Force overwrite: 通常はチェックしない（危険）
4. **Preview で確認**
5. **Push**

#### Push結果の確認

```
Push Results ダイアログ
├── Repository: プッシュ先URL
├── Result: 成功/失敗
├── Updates:
│   ├── master: abc123..def456
│   └── feature/new: [new branch]
└── Messages: エラーや警告
```

### 9.3 Fetch/Pull操作

#### Fetchの実行

1. **Git Repositories → Fetch from Origin**
2. **リモートの更新情報のみ取得（ローカル変更なし）**
3. **Fetch Result で確認:**
   ```
   [new branch] feature/other -> origin/feature/other
   [update] master -> origin/master
   ```

#### Pullの実行と設定

1. **Git Repositories → Pull...**
2. **Pull設定:**
   - Remote: origin
   - Reference: refs/heads/dev
   - Merge/Rebase: Merge（推奨）
3. **Pull**

### 9.4 認証設定

#### HTTPS認証（Personal Access Token）

1. **初回Push/Pull時に認証ダイアログ表示**
2. **User: GitHubユーザー名**
3. **Password: Personal Access Token（注意: パスワードではない）**
4. **Store in Secure Store: チェック（保存）**

#### SSH認証

1. **Preferences → General → Network Connections → SSH2**
2. **SSH鍵が正しく設定されていることを確認**
3. **Known Hosts タブでgithub.comが登録されていることを確認**

#### Personal Access Token作成手順

1. **GitHub → Settings → Developer settings**
2. **Personal access tokens → Tokens (classic)**
3. **Generate new token**
4. **スコープ選択:**
   - repo（全権限）
   - workflow（Actions使用時）
5. **Generate token**
6. **トークンをコピー（一度しか表示されない）**

---

## 🔌 推奨プラグイン

### 10.1 必須プラグイン

#### EGit - Git Integration for Eclipse

- **機能**: Git基本機能統合
- **インストール**: Eclipse標準装備
- **バージョン**: 6.0以降推奨

#### Eclipse GitHub integration

- **機能**: GitHub特化機能（Gist、PR等）
- **インストール方法**:
  1. Help → Install New Software
  2. EGit update site追加
  3. GitHub integrationを選択

### 10.2 生産性向上プラグイン

#### Gitflow for Eclipse

- **機能**: Git Flow ワークフロー対応
- **利点**: SAS Flow準拠の開発フロー実装
- **使い方**:
  1. プロジェクト右クリック → Team → Git Flow
  2. Initialize で初期化
  3. Start Feature/Release/Hotfix で作業開始

#### EGit Synchronize

- **機能**: 変更の同期ビュー提供
- **利点**: チーム作業時の変更追跡
- **表示**: Window → Show View → Team → Synchronize

#### Mylyn GitHub Connector

- **機能**: GitHub Issues統合
- **利点**: Issue管理とコミット連携
- **設定**:
  1. Task Repositories追加
  2. GitHub選択
  3. リポジトリURL設定

### 10.3 コード品質プラグイン

#### SpotBugs Eclipse Plugin

- **機能**: バグパターン検出
- **Git連携**: コミット前チェック
- **設定**: プロジェクトプロパティ → SpotBugs

#### Checkstyle Plugin

- **機能**: コーディング規約チェック
- **Git連携**: pre-commitフック連携
- **設定**: sas-checkstyle.xmlインポート

#### SonarLint

- **機能**: リアルタイムコード品質分析
- **Git連携**: 変更部分のみ分析
- **設定**: SonarQubeサーバー接続

### 10.4 プラグイン管理のベストプラクティス

#### チーム共通設定

1. **Eclipse設定エクスポート**:
   - File → Export → General → Preferences
   - チーム共有リポジトリに保存

2. **プラグインリスト管理**:
   ```xml
   <!-- .eclipse/plugins.xml -->
   <plugins>
     <plugin>
       <id>org.eclipse.egit</id>
       <version>6.0.0</version>
       <required>true</required>
     </plugin>
   </plugins>
   ```

3. **自動インストールスクリプト**:
   ```bash
   # install-plugins.sh
   eclipse -nosplash -application org.eclipse.equinox.p2.director \
     -repository http://download.eclipse.org/releases/latest \
     -installIU org.eclipse.egit.feature.group
   ```

---

## 🛠️ トラブルシューティング

### 11.1 よくある問題と解決方法

#### 問題: Gitリポジトリが認識されない

**症状**: Team メニューにGit操作が表示されない

**解決方法**:
1. プロジェクト右クリック → Configure → Add to Version Control
2. または Team → Share Project → Git
3. .gitフォルダの存在確認
4. Eclipse再起動

#### 問題: Push時に認証エラー

**症状**: `Authentication failed` エラー

**解決方法**:
1. Personal Access Token の再生成
2. Secure Storage クリア:
   - Preferences → General → Security → Secure Storage
   - Contents タブ → Delete
3. SSH鍵の確認:
   ```bash
   ssh -T git@github.com
   ```

#### 問題: 日本語ファイル名が文字化け

**症状**: Git操作で日本語が「?」表示

**解決方法**:
1. Preferences → General → Workspace
2. Text file encoding: UTF-8
3. Git設定確認:
   ```
   core.quotepath = false
   ```

#### 問題: OutOfMemoryError

**症状**: 大規模リポジトリでメモリ不足

**解決方法**:
1. eclipse.ini 編集:
   ```
   -Xms512m
   -Xmx2048m
   ```
2. Git設定最適化:
   ```
   core.packedGitLimit = 128m
   core.packedGitWindowSize = 128m
   ```

### 11.2 パフォーマンス最適化

#### Eclipse設定最適化

1. **不要なバリデーション無効化**:
   - Preferences → Validation
   - 使用しないバリデータのチェックを外す

2. **自動ビルド最適化**:
   - Project → Build Automatically
   - 大規模プロジェクトでは手動ビルドを検討

3. **Git操作の最適化**:
   - Preferences → Team → Git → Projects
   - Auto share projects: オフ（手動制御）

#### リポジトリ最適化

```bash
# Git GC実行（Eclipse Terminal内）
git gc --aggressive --prune=now

# 大容量ファイル履歴削除
git filter-branch --index-filter 'git rm -r --cached --ignore-unmatch large-file'
```

### 11.3 WSL2特有の問題

#### ファイルシステム速度問題

**問題**: WSL2内ファイルへのアクセスが遅い

**解決策**:
1. Windows側にクローン
2. WSL2からは /mnt/c/ 経由でアクセス
3. または Docker Desktop + VS Code Remote

#### 改行コード問題

**問題**: CRLF/LF混在

**解決策**:
1. .gitattributes設定:
   ```
   * text=auto eol=lf
   *.bat text eol=crlf
   ```
2. Eclipse設定統一

### 11.4 緊急時の対処

#### リポジトリ破損時

1. **バックアップ作成**:
   ```bash
   cp -r project project.backup
   ```

2. **リポジトリ修復**:
   ```bash
   git fsck --full
   git reflog
   ```

3. **最悪の場合、再クローン**:
   - 変更をパッチとして保存
   - 新規クローン
   - パッチ適用

#### Eclipse設定リセット

1. **ワークスペース設定リセット**:
   - .metadata フォルダ削除
   - Eclipse再起動
   - プロジェクト再インポート

2. **プラグイン再インストール**:
   - Help → About → Installation Details
   - Uninstall
   - 再インストール

---

## 📋 チェックリスト

### 12.1 初期セットアップチェックリスト

#### 環境準備

- [ ] Eclipse IDE 2024-06以降インストール
- [ ] EGit 6.0以降インストール確認
- [ ] JDK適切なバージョン設定
- [ ] メモリ設定最適化（eclipse.ini）

#### Git設定

- [ ] user.name設定（英語名、ハイフン形式）
- [ ] user.email設定（@sas-com.com）
- [ ] core.autocrlf設定（input）
- [ ] core.quotepath設定（false）

#### 認証設定

- [ ] SSH鍵生成・登録完了
- [ ] またはPersonal Access Token作成
- [ ] GitHub 2FA有効化確認
- [ ] Secure Store設定

#### プロジェクト設定

- [ ] .gitignore適切に設定
- [ ] 文字コードUTF-8統一
- [ ] 改行コードLF統一
- [ ] CODEOWNERSファイル確認

### 12.2 日次作業チェックリスト

#### 作業開始時

- [ ] リモートから最新をpull
- [ ] ブランチが正しいことを確認
- [ ] ビルド成功確認
- [ ] テスト実行確認

#### コミット時

- [ ] 変更内容の確認（差分チェック）
- [ ] 不要ファイルが含まれていないか
- [ ] コミットメッセージがSAS規約準拠
- [ ] 意味のある単位でコミット

#### プッシュ前

- [ ] ローカルテスト実行
- [ ] コンフリクトなし確認
- [ ] リモートの最新取得
- [ ] プッシュ先ブランチ確認

#### 作業終了時

- [ ] 全変更がコミット済み
- [ ] リモートにプッシュ済み
- [ ] 作業ブランチの整理
- [ ] Issueステータス更新

### 12.3 週次メンテナンスチェックリスト

- [ ] 不要ブランチの削除
- [ ] Git GC実行
- [ ] Eclipse更新確認
- [ ] プラグイン更新確認
- [ ] セキュリティパッチ適用

---

## 📚 参考資料

### 社内ドキュメント

- [GitHub環境構築ガイド](../onboarding/GITHUB_ENVIRONMENT_SETUP.md) - GitHub環境構築
- [コミット規約ガイドライン](../workflow/COMMIT_CONVENTION_GUIDE.md) - コミット規約
- [ブランチ管理ルール](../workflow/BRANCH_MANAGEMENT_RULES.md) - ブランチ管理
- [新規参画者向けオンボーディング](../onboarding/ONBOARDING.md) - オンボーディング

### 外部リソース

- [Eclipse EGit Documentation](https://wiki.eclipse.org/EGit/User_Guide)
- [GitHub Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [Git Documentation](https://git-scm.com/doc)

### サポート

- **社内サポート**: github@sas-com.com
- **緊急時**: github@sas-com.com（24時間対応）

---

## 🔄 更新履歴

- **2025-10-11**: 初版作成
- **作成者**: SAS GitHub管理チーム

---

**© 2025 エス・エー・エス株式会社 - Eclipse Git利用ガイドライン**