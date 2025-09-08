# 新規参画者向け GitHub オンボーディングガイド

**エス・エー・エス株式会社へようこそ！**  
*最終更新: 2025年9月5日*

## 📌 はじめに

このガイドは、エス・エー・エス株式会社のプロジェクトに新しく参画される方向けのGitHub利用開始ガイドです。
順番に進めることで、スムーズに開発業務を開始できます。

---

## 🗺️ オンボーディング全体の流れ

### 📅 完了目安: 2-3日

```mermaid
graph TD
    A[Day 1: 環境構築] --> B[Day 2: GitHub基礎学習]
    B --> C[Day 3: 実践演習]
    C --> D[プロジェクト参加]
    
    A --> A1[WSL2インストール<br/>15-30分]
    A --> A2[Gitインストール<br/>10分]
    A --> A3[GitHubアカウント作成<br/>20分]
    A --> A4[SSH鍵設定<br/>15分]
    
    B --> B1[Git基本操作<br/>1-2時間]
    B --> B2[GitHub機能理解<br/>1時間]
    B --> B3[社内ルール確認<br/>30分]
    
    C --> C1[練習リポジトリ<br/>2時間]
    C --> C2[PR作成練習<br/>1時間]
    C --> C3[コンフリクト解決<br/>1時間]
    
    D --> D1[プロジェクト招待]
    D --> D2[開発開始]
```

### ✅ チェックリスト

#### **Day 1: 環境構築**（所要時間: 約1-2時間）
- [ ] WSL2のインストール（Windows環境の場合）
- [ ] Gitのインストールと初期設定
- [ ] GitHubアカウント作成と2FA設定
- [ ] SSH鍵の生成と登録
- [ ] 接続テスト

#### **Day 2: GitHub基礎学習**（所要時間: 約3-4時間）
- [ ] Git基本コマンドの理解
- [ ] ブランチの概念理解
- [ ] コミットメッセージ規約の確認
- [ ] PR（プルリクエスト）の仕組み理解
- [ ] 社内ガイドライン熟読

#### **Day 3: 実践演習**（所要時間: 約4時間）
- [ ] 練習リポジトリでの作業
- [ ] feature ブランチの作成
- [ ] コミットとプッシュ
- [ ] PRの作成とレビュー依頼
- [ ] コンフリクト解決の練習

#### **プロジェクト参加準備**
- [ ] プロジェクトへの招待承認
- [ ] プロジェクトリポジトリのクローン
- [ ] 開発環境の構築
- [ ] 初回タスクの確認

### 🎯 ゴール

このオンボーディングを完了すると、以下ができるようになります：

1. **Git/GitHubの基本操作** - クローン、コミット、プッシュ、PR作成
2. **社内ルールの理解** - コミットメッセージ規約、ブランチ戦略
3. **トラブル対応** - コンフリクト解決、よくあるエラーの対処
4. **セキュアな開発** - SSH接続、2FA設定、機密情報の取り扱い

---

## 🖥️ 事前準備: WSL2のインストール（Windows環境の場合）

### WSL2とは
Windows Subsystem for Linux 2（WSL2）は、Windows上でLinux環境を動作させる仕組みです。
開発においてBashコマンドを使用するため、Windows環境では必須となります。

### インストール手順

#### 1. システム要件の確認
```markdown
✅ Windows 10 バージョン 2004以降（ビルド 19041以降）
✅ Windows 11
```

#### 2. WSL2のインストール

**方法1: 簡単インストール（推奨）**

PowerShellを管理者として実行し、以下のコマンドを入力：

```powershell
# WSL2とUbuntuをインストール
wsl --install

# PCを再起動
# 再起動後、自動的にUbuntuのセットアップが開始されます
```

**方法2: 手動インストール**

1. Windows機能の有効化（PowerShell管理者で実行）：
```powershell
# WSL機能を有効化
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# 仮想マシン機能を有効化
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# PCを再起動
```

2. WSL2を既定バージョンに設定：
```powershell
wsl --set-default-version 2
```

3. Microsoft StoreからUbuntuをインストール：
   - Microsoft Storeを開く
   - 「Ubuntu」で検索
   - 「Ubuntu 22.04 LTS」をインストール

#### 3. 初期設定

Ubuntuを起動し、ユーザー名とパスワードを設定：

```bash
# ユーザー名を入力（英数字小文字）
Enter new UNIX username: yourname

# パスワードを設定（入力時は表示されません）
Enter new UNIX password: 
Retype new UNIX password:
```

#### 4. 基本的なセットアップ

```bash
# パッケージを最新に更新
sudo apt update && sudo apt upgrade -y

# 開発に必要な基本ツールをインストール
sudo apt install -y git curl wget build-essential

# 日本語環境の設定
sudo apt install -y language-pack-ja
sudo update-locale LANG=ja_JP.UTF-8
```

### VS CodeとWSL2の連携

1. VS Codeをインストール（まだの場合）
2. VS Codeの拡張機能「WSL」をインストール
3. WSL内のプロジェクトを開く：
```bash
# WSL内で
code .
```

---

## 📅 Day 1-3: 環境構築

### ✅ チェックリスト

#### 1. GitHubアカウント作成
- [ ] GitHubアカウントを作成（既にある場合はスキップ）
- [ ] プロフィール設定（名前、アバター画像）
- [ ] **重要**: 2要素認証（2FA）を有効化

📖 **詳細手順**: [GitHubアカウント作成・設定ガイド](./GITHUB_ACCOUNT_SETUP.md)を参照

#### 2. 組織への参加
- [ ] 招待メールを確認
- [ ] エス・エー・エス株式会社のOrganizationに参加
- [ ] 所属チームの確認

#### 3. 開発環境セットアップ
- [ ] WSL2をインストール（Windows環境）
- [ ] Gitをインストール
- [ ] エディタをセットアップ（VS Code推奨）
- [ ] ターミナル環境を準備

### 🔧 Git初期設定

**WSL2/Linux/Mac環境で実行：**

```bash
# ユーザー情報設定
git config --global user.name "山田 太郎"
git config --global user.email "yamada@sas-com.co.jp"

# エディタ設定（VS Codeの場合）
git config --global core.editor "code --wait"

# 改行コード設定
# Windowsの場合（WSL2内）
git config --global core.autocrlf input
# Mac/Linuxの場合
git config --global core.autocrlf input

# 日本語ファイル名の文字化け防止
git config --global core.quotepath false

# 設定確認
git config --global --list
```

### 🔑 SSH鍵の設定

**WSL2/Linux/Mac環境で実行：**

```bash
# SSH鍵の生成
ssh-keygen -t ed25519 -C "yamada@sas-com.co.jp"
# Enterを3回押してデフォルト設定で作成

# SSH鍵の確認
ls -la ~/.ssh/
# id_ed25519（秘密鍵）とid_ed25519.pub（公開鍵）が作成される

# 公開鍵を表示
cat ~/.ssh/id_ed25519.pub
# 表示された内容を全てコピー（ssh-ed25519から最後まで）

# GitHubに登録
# 1. GitHub Settings → SSH and GPG keys
# 2. New SSH key
# 3. タイトル: "会社PC - WSL2" など識別できる名前
# 4. Key: コピーした公開鍵をペースト
# 5. Add SSH key

# 接続テスト
ssh -T git@github.com
# "Hi username! You've successfully authenticated..." と表示されれば成功
```

**Windows環境でSSHエラーが出る場合：**

```bash
# ssh-agentを起動
eval "$(ssh-agent -s)"

# SSH鍵を追加
ssh-add ~/.ssh/id_ed25519

# 再度接続テスト
ssh -T git@github.com
```

---

## 📅 Day 4-7: 基本操作の習得

### 📚 必須学習項目

#### 1. Git基本コマンド

最低限覚えるコマンド：

| コマンド | 説明 | 使用頻度 |
|---------|------|----------|
| `git clone` | リポジトリをコピー | ⭐ |
| `git status` | 状態確認 | ⭐⭐⭐ |
| `git add` | ステージング | ⭐⭐⭐ |
| `git commit` | コミット | ⭐⭐⭐ |
| `git push` | アップロード | ⭐⭐⭐ |
| `git pull` | ダウンロード | ⭐⭐⭐ |
| `git checkout` | ブランチ切り替え | ⭐⭐ |
| `git branch` | ブランチ一覧 | ⭐⭐ |
| `git log` | 履歴確認 | ⭐ |

#### 2. 練習用リポジトリで実習

```bash
# WSL2/ターミナルで実行

# 作業ディレクトリを作成
mkdir ~/projects
cd ~/projects

# 練習用リポジトリをクローン
git clone git@github.com:sas-com/training-sandbox.git
cd training-sandbox

# 自分用のブランチを作成
git checkout -b training/yamada-taro

# ファイルを作成
echo "# 自己紹介" > yamada-taro.md
echo "山田太郎です。よろしくお願いします！" >> yamada-taro.md

# 状態確認
git status

# コミット
git add yamada-taro.md
git commit -m "add: 自己紹介を追加"

# プッシュ
git push origin training/yamada-taro

# PRを作成（ブラウザで）
# 表示されるURLをクリックするか、GitHubでリポジトリを開いて作成
```

### 🎯 演習課題

以下の課題を順番に実施：

#### 課題1: 基本操作
```markdown
1. training-sandboxリポジトリをクローン
2. 自分のブランチを作成
3. 自己紹介ファイルを追加
4. コミット＆プッシュ
5. PRを作成
```

#### 課題2: チーム開発シミュレーション
```markdown
1. devブランチから作業ブランチを作成
2. 簡単な機能を実装（例: Hello World）
3. コミットメッセージ規約に従ってコミット
4. PRを作成してレビューを依頼
5. レビューコメントに対応
```

#### 課題3: コンフリクト解決
```markdown
1. わざとコンフリクトを発生させる
2. コンフリクトを解決
3. 正しくマージする
```

---

## 📅 Week 2: プロジェクト参加準備

### 🏢 社内ルールの理解

#### コミットメッセージ規約
```bash
# 形式
<type>(<scope>): <subject>

# 良い例
feat(auth): ログイン機能を実装
fix(api): ユーザー検索のバグを修正
docs(readme): インストール手順を更新

# 悪い例
update      # 何を更新したか不明
修正         # 具体性がない
WIP         # 未完成のコミットは避ける
```

#### ブランチ構成
```bash
main        # 本番環境（今後構築予定）
staging     # ステージング環境（今後構築予定）
dev         # 開発環境（現在運用中）

# 機能ブランチ（必要に応じて）
feature/[機能名]  # 新機能
bugfix/[説明]     # バグ修正
hotfix/[説明]     # 緊急修正
```

**※現在の運用**: dev環境のみ運用中。devブランチで開発作業を実施。強制プッシュは厳禁。

### 🔐 セキュリティ意識

#### 絶対にやってはいけないこと

```markdown
❌ パスワードやAPIキーをコミット
❌ 個人情報や本番データをコミット
❌ クライアント固有の情報を他で使用
❌ Publicリポジトリの作成（許可なく）
❌ 外部サービスとの無断連携
❌ 強制プッシュ（--force）の使用
```

#### やってしまった時の対処

```markdown
1. 即座に上司・先輩に報告
2. 該当の認証情報を無効化
3. SAS Github管理チームに連絡
4. 履歴から削除作業
```

### 📝 ドキュメント確認

必ず読むドキュメント：

- [ ] [GitHub運用ガイドライン サマリー](./README.md)
- [ ] [GitHub運用ガイドライン 詳細版](./GUIDELINES_DETAIL.md)
- [ ] [クイックリファレンス](./QUICK_REFERENCE.md)
- [ ] プロジェクト固有のREADME

---

## 📅 Week 3-4: 実プロジェクト参加

### 🚀 プロジェクト参加フロー

```mermaid
graph LR
    A[プロジェクトアサイン] --> B[権限付与]
    B --> C[リポジトリクローン]
    C --> D[環境構築]
    D --> E[Issue割り当て]
    E --> F[開発開始]
```

### 実際のプロジェクト参加手順

```bash
# 1. プロジェクトディレクトリを作成
mkdir ~/projects/client-name
cd ~/projects/client-name

# 2. リポジトリをクローン
git clone git@github.com:sas-com/[repository-name].git
cd [repository-name]

# 3. 環境構築（プロジェクトによって異なる）
# Node.jsプロジェクトの例
npm install

# Pythonプロジェクトの例
python -m venv venv
source venv/bin/activate  # WSL2/Linux/Mac
pip install -r requirements.txt

# 4. 環境変数の設定
cp .env.example .env
# .envファイルを編集して必要な値を設定

# 5. 動作確認
npm start  # または python app.py など
```

### 👥 メンター制度

最初の1ヶ月は先輩がメンターとして付きます：

```markdown
メンターがサポートすること：
- Git/GitHubの操作方法
- コードレビューの方法
- 社内ルールの説明
- 技術的な質問への回答
- PRの作成サポート
```

### 📊 最初のタスク

典型的な最初のタスク：

| 週 | タスク内容 | 目的 |
|----|-----------|------|
| 1週目 | ドキュメント修正 | Git操作に慣れる |
| 2週目 | 簡単なバグ修正 | コードベース理解 |
| 3週目 | 小機能の実装 | 開発フロー習得 |
| 4週目 | 通常タスク開始 | 独立して作業 |

---

## 💪 スキルアップロードマップ

### Level 1: 初心者（1ヶ月目）
```markdown
✅ 基本的なGit操作ができる
✅ PRを作成できる
✅ コミットメッセージ規約を守れる
✅ 簡単なIssueを解決できる
```

### Level 2: 初級（2-3ヶ月目）
```markdown
✅ ブランチ戦略を理解している
✅ コンフリクトを解決できる
✅ コードレビューに参加できる
✅ 独立してタスクを完了できる
```

### Level 3: 中級（4-6ヶ月目）
```markdown
✅ 他人のPRをレビューできる
✅ 複雑な機能を実装できる
✅ Git flowを完全に理解している
✅ CI/CDを理解している
```

### Level 4: 上級（6ヶ月以降）
```markdown
✅ 新人のメンターができる
✅ リリース作業ができる
✅ 緊急対応（hotfix）ができる
✅ プロジェクトのGit戦略を提案できる
```

---

## 🆘 困ったときは

### WSL2特有のトラブルシューティング

#### WSL2が起動しない
```powershell
# PowerShell（管理者）で実行
wsl --shutdown
wsl --update
wsl
```

#### Git操作が遅い
```bash
# WSL2内のファイルシステムを使用する
cd ~/projects  # /mnt/c/ではなくホームディレクトリ以下を使用
```

#### 改行コードの問題
```bash
# .gitattributesファイルをプロジェクトルートに作成
echo "* text=auto eol=lf" > .gitattributes
git add .gitattributes
git commit -m "chore: 改行コードをLFに統一"
```

### よくあるGitトラブルと解決法

#### 1. プッシュできない
```bash
# 原因: リモートが先に進んでいる
git pull origin dev
# コンフリクトがあれば解決
git push origin dev
```

#### 2. 間違えて他のブランチにコミットした
```bash
# コミットを取り消し（ローカルのみ）
git reset --soft HEAD^
# 正しいブランチを作成
git checkout -b feature/correct-branch
# コミットし直し
git commit -m "正しいメッセージ"
```

#### 3. コンフリクトの解決方法
```bash
# コンフリクトしたファイルを確認
git status

# VS Codeで開いて編集
code .

# ファイルを編集して解決
# <<<<<<<, =======, >>>>>>> を削除して正しいコードに

# 解決したらadd & commit
git add [resolved-file]
git commit -m "resolve: コンフリクトを解決"
```

### 📞 サポート窓口

| 相談内容 | 連絡先 | 備考 |
|---------|--------|------|
| Git/GitHub操作 | SAS Github管理チーム (github@sas-com.com) | 技術サポート |
| アクセス権限 | SAS Github管理チーム (github@sas-com.com) | 管理者対応 |
| セキュリティインシデント | SAS Github管理チーム (github@sas-com.com) | 即座に連絡 |
| WSL2の問題 | SAS Github管理チーム (github@sas-com.com) | 環境構築サポート |

---

## 📚 学習リソース

### 社内リソース
- 📖 [GitHub運用ガイドライン サマリー](./README.md) - 概要把握
- 📖 [GitHub運用ガイドライン 詳細版](./GUIDELINES_DETAIL.md) - 必読
- 🚀 [クイックリファレンス](./QUICK_REFERENCE.md) - 手元に置いておく
- 🆘 [緊急時対応マニュアル](./EMERGENCY_RESPONSE.md) - 緊急時に確認
- 🎥 社内勉強会アーカイブ - 過去の勉強会動画

### 外部リソース
- 🌐 [GitHub Skills](https://skills.github.com/) - 公式学習コース
- 📘 [Pro Git Book](https://git-scm.com/book/ja/v2) - Git解説書（日本語）
- 🎮 [Learn Git Branching](https://learngitbranching.js.org/?locale=ja) - インタラクティブ学習
- 📺 [GitHub公式YouTube](https://www.youtube.com/github) - チュートリアル動画
- 📚 [WSL2公式ドキュメント](https://docs.microsoft.com/ja-jp/windows/wsl/) - WSL2の詳細

### 推奨学習順序
```mermaid
graph TD
    A[WSL2セットアップ] --> B[Git基礎]
    B --> C[GitHub基礎]
    C --> D[ブランチ操作]
    D --> E[PR作成]
    E --> F[コードレビュー]
    F --> G[Git Flow]
    G --> H[CI/CD基礎]
```

---

## 📝 オンボーディングチェックリスト

### Day 1-3
- [ ] WSL2インストール（Windows環境）
- [ ] GitHubアカウント作成
- [ ] 2FA有効化
- [ ] Organization参加
- [ ] Git初期設定
- [ ] SSH鍵設定
- [ ] VS Code + WSL拡張機能セットアップ

### Week 1
- [ ] 練習リポジトリで基本操作
- [ ] コミット・プッシュの練習
- [ ] PRの作成練習
- [ ] コンフリクト解決の練習

### Week 2
- [ ] コミットメッセージ規約の理解
- [ ] ブランチ戦略の理解
- [ ] 最初のPR作成
- [ ] コードレビューを受ける
- [ ] セキュリティルールの理解

### Week 3-4
- [ ] 実プロジェクト参加
- [ ] 最初のIssue対応
- [ ] 独立してPR作成
- [ ] 他人のPRにコメント
- [ ] 日常的な開発フローの習得

### 1ヶ月後の目標
```markdown
✅ WSL2環境でスムーズに開発できる
✅ 独立して簡単なタスクを完了できる
✅ PRの作成からマージまでを理解している
✅ チームの開発フローに馴染んでいる
✅ 基本的なトラブルを自己解決できる
```

---

## 💬 先輩からのアドバイス

> 💡 **"環境構築は最初が肝心"**  
> WSL2の設定を正しく行うことで、後々のトラブルを避けることができます。

> 💡 **"わからないことは早めに聞く"**  
> 15分悩んで解決しなかったら聞きましょう。それが一番効率的です。

> 💡 **"コミットは細かく"**  
> 大きな変更を1つのコミットにせず、論理的な単位で分けましょう。

> 💡 **"レビューは学習の機会"**  
> コードレビューでの指摘は成長のチャンス。積極的に受け入れましょう。

> 💡 **"ドキュメントを書く習慣"**  
> 自分が理解したことをドキュメント化すると、次の人の助けになります。

---

## 🎉 Welcome to the Team!

エス・エー・エス株式会社の開発チームへようこそ！
分からないことがあれば、遠慮なく質問してください。
一緒に素晴らしいプロダクトを作っていきましょう！

---

**© 2025 エス・エー・エス株式会社 - 新規参画者向けGitHubオンボーディングガイド**