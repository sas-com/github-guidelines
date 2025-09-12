# GitHub 環境構築ガイド

**エス・エー・エス株式会社**  
*開発環境のセットアップから GitHubアカウント設定まで完全ガイド*  
*最終更新: 2025年9月12日*

## 📌 はじめに

このガイドは、エス・エー・エス株式会社で GitHub を使った開発を始めるために必要な環境構築を、ゼロから完全にサポートします。
Windows 環境での WSL2 セットアップから、Git の初期設定、GitHub アカウントの作成・設定まで、全ての手順を網羅しています。

## ⏱️ 所要時間

**環境構築全体: 約1-2時間**

| ステップ | 所要時間 | 備考 |
|---------|----------|------|
| WSL2のインストール | 15-30分 | Windows必須、再起動含む |
| Gitのインストールと初期設定 | 10-15分 | WSL2内で実施 |
| GitHubアカウント作成と2FA設定 | 20-30分 | 既存アカウント利用可 |
| SSH鍵の生成と登録 | 10-15分 | WSL2内で実施 |
| 接続テスト | 5分 | 動作確認 |

---

## 📋 作業チェックリスト

### 環境構築（Windows必須）
- [ ] WSL2のインストールと初期設定
- [ ] Ubuntu（推奨）のセットアップ
- [ ] VS Codeとの連携設定

### Git環境設定
- [ ] Gitのインストール（WSL2内）
- [ ] Git初期設定（user.name, user.email等）
- [ ] 日本語環境の設定

### GitHubアカウント設定
- [ ] GitHubアカウント作成（または既存アカウントの利用）
- [ ] プロフィール設定
- [ ] 2要素認証（2FA）設定 ※必須
- [ ] メール通知設定

### SSH接続設定
- [ ] SSH鍵の生成（ed25519推奨）
- [ ] GitHubへのSSH鍵登録
- [ ] 接続テストと動作確認
- [ ] 組織への参加

### 推奨項目
- [ ] プロフィール画像設定
- [ ] READMEプロフィール作成
- [ ] GPG鍵の設定（コミット署名用）

---

## 1️⃣ WSL2のインストール（Windows環境必須）

> 💡 **Mac/Linux ユーザーの方**: このセクションはスキップして「[2️⃣ Gitのインストールと初期設定](#2️⃣-gitのインストールと初期設定)」へ進んでください。

### WSL2とは

Windows Subsystem for Linux 2（WSL2）は、Windows上でLinux環境を動作させる仕組みです。
開発において Bash コマンドや Linux ツールを使用するため、Windows 環境では必須となります。

---

### 🔍 事前確認（重要）

**WSL2のインストールを開始する前に、以下の項目を必ず確認してください。**
これらの確認を怠ると、エラー 0x80370114 などのインストールエラーが発生する可能性があります。

#### 1. システム要件の確認

PowerShell を**管理者として実行**し、以下のコマンドで確認：

```powershell
# Windows バージョンの確認
[System.Environment]::OSVersion.Version

# 出力例（Windows 10 version 2004以降が必要）：
# Major  Minor  Build  Revision
# -----  -----  -----  --------
# 10     0      19041  0

# または、より詳細な情報を確認
winver
# ポップアップウィンドウで「バージョン 2004」以降であることを確認
```

**必要要件：**
- ✅ Windows 10 バージョン 2004以降（ビルド 19041以降）
- ✅ Windows 11（全バージョン対応）
- ✅ x64 システム（64ビット版Windows）

#### 2. 仮想化機能の確認（最重要）

```powershell
# タスクマネージャーで確認（最も簡単）
# 1. Ctrl + Shift + Esc でタスクマネージャーを開く
# 2. 「パフォーマンス」タブ → 「CPU」を選択
# 3. 右下に「仮想化: 有効」と表示されていることを確認

# PowerShellコマンドで確認
Get-ComputerInfo | Select-Object HyperV*

# 出力例（仮想化が有効な場合）：
# HyperVRequirementDataExecutionPreventionAvailable       : True
# HyperVRequirementSecondLevelAddressTranslation          : True
# HyperVRequirementVirtualizationFirmwareEnabled          : True  ← これがTrueである必要
# HyperVRequirementVMMonitorModeExtensions                : True
```

**⚠️ 仮想化が無効の場合：**
1. PCを再起動し、起動時にBIOS/UEFI設定に入る（通常F2、F10、DelキーなどでBIOS画面へ）
2. 以下の設定を探して有効化：
   - Intel CPU: "Intel Virtualization Technology (VT-x)" を Enabled に
   - AMD CPU: "SVM Mode" または "AMD-V" を Enabled に
3. 設定を保存してPCを再起動

#### 3. Windows機能の状態確認

```powershell
# 必要なWindows機能の状態を確認
Get-WindowsOptionalFeature -Online | Where-Object {$_.FeatureName -like "*Linux*" -or $_.FeatureName -like "*Virtual*"} | Select-Object FeatureName, State

# 出力例：
# FeatureName                           State
# -----------                           -----
# VirtualMachinePlatform                Disabled  ← これらをEnabledにする必要
# Microsoft-Windows-Subsystem-Linux     Disabled  ← これらをEnabledにする必要
```

#### 4. WSLの現在の状態確認

```powershell
# WSLがインストール済みか確認
wsl --status

# エラーが出る場合はWSL未インストール
# 正常な場合は現在のWSL情報が表示される
```

---

### 📦 インストール手順

#### 方法1: 簡単インストール（推奨）

**前提条件を全て満たしている場合**、PowerShell を**管理者として実行**し、以下のコマンドを入力：

```powershell
# WSL2と既定のディストリビューション（Ubuntu）を一括インストール
wsl --install

# 特定のディストリビューションを指定する場合：
# wsl --install -d <ディストリビューション名>
# 例: wsl --install -d Debian

# インストール完了後、以下のメッセージが表示されます：
# "The requested operation is successful. Changes will not be effective until the system is rebooted."

# PCを再起動（必須）
Restart-Computer

# 再起動後、自動的に選択したディストリビューションのセットアップが開始されます
```

> 💡 **ヒント**: `wsl --install`のみ実行した場合、既定でUbuntuがインストールされます。プロジェクトで別のディストリビューションが必要な場合は、`-d`オプションで明示的に指定してください。

#### 方法2: 手動インストール（方法1でエラーが発生する場合）

**ステップ1: 必要なWindows機能を個別に有効化**

PowerShell を**管理者として実行**：

```powershell
# 1. Windows Subsystem for Linux機能を有効化
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# 2. 仮想マシンプラットフォーム機能を有効化（重要）
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# 3. 有効化を確認
Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux
Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform

# 両方が "State: Enabled" になっていることを確認

# 4. PCを再起動（必須 - 機能を有効にするため）
Restart-Computer
```

**ステップ2: WSL2カーネルの更新**

再起動後、PowerShell を**管理者として実行**：

```powershell
# WSLカーネルを最新版に更新
wsl --update

# WSL2を既定バージョンに設定
wsl --set-default-version 2
```

**ステップ3: Linuxディストリビューションのインストール**

> ⚠️ **重要**: 本ガイドではUbuntuを例として使用していますが、実際に使用するLinuxディストリビューションは各プロジェクトの要件に応じて選択してください。

**利用可能なディストリビューション一覧を確認：**
```powershell
# インストール可能なディストリビューション一覧
wsl --list --online
```

**一般的な選択肢：**
- **Ubuntu** (22.04/20.04 LTS) - 最も一般的、サポートが充実
- **Debian** - 安定性重視のプロジェクト向け
- **openSUSE** - エンタープライズ環境向け
- **AlmaLinux** / **Rocky Linux** - RHEL互換が必要な場合
- **Alpine** - 軽量環境が必要な場合

**インストール方法（Ubuntuを例として）：**

```powershell
# コマンドラインでインストールする場合
wsl --install -d Ubuntu-22.04

# 他のディストリビューションの例：
# wsl --install -d Debian
# wsl --install -d openSUSE-Leap-15.5
# wsl --install -d AlmaLinux-9

# または Microsoft Store経由：
# 1. Microsoft Storeを開く
# 2. 希望のディストリビューション名で検索
# 3. インストールボタンをクリック
```

> 📝 **プロジェクトでの決定事項**:
> 各プロジェクトでは以下を明確にしてください：
> - 使用するディストリビューションとバージョン
> - 選定理由（パッケージ要件、ライブラリ互換性など）
> - プロジェクト固有の追加設定があれば文書化

#### 方法3: コントロールパネルから手動で有効化

GUIで設定したい場合：

1. **Windowsの機能の有効化または無効化**を開く
   - コントロールパネル → プログラムと機能 → Windowsの機能の有効化または無効化
   - または「Win + R」→「optionalfeatures」と入力

2. **以下の項目にチェックを入れる（必須）**：
   - ✅ Linux 用 Windows サブシステム（Windows Subsystem for Linux）
   - ✅ 仮想マシン プラットフォーム（Virtual Machine Platform）
   - ✅ Hyper-V（利用可能な場合）

3. **OK**をクリックし、**PCを再起動**

---

### ⚠️ よくあるエラーと対処法

#### エラー 0x80370114: 最も一般的なエラー

**エラーメッセージ：**
```
WslRegisterDistribution failed with error: 0x80370114
Error: 0x80370114 The operation could not be started because a required feature is not installed.
```

**根本原因と解決手順：**

##### 原因1: 仮想化が無効（最も多い原因）

**確認方法：**
```powershell
# タスクマネージャーで確認
# パフォーマンスタブ → CPU → 「仮想化: 無効」と表示されている
```

**解決手順：**
1. PCメーカーのサポートサイトでBIOS/UEFI設定方法を確認
2. PCを再起動し、起動時にBIOS設定に入る（F2、F10、Delキーなど）
3. 以下の設定を探して有効化：
   - **Intel CPU**: 
     - Advanced → CPU Configuration → Intel Virtualization Technology → Enabled
   - **AMD CPU**: 
     - Advanced → CPU Configuration → SVM Mode → Enabled
4. 設定を保存（通常F10キー）して再起動
5. タスクマネージャーで「仮想化: 有効」を確認

##### 原因2: Virtual Machine Platform機能が無効

**解決手順：**
```powershell
# PowerShell（管理者）で実行
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# 機能の有効化を確認
Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform

# PCを再起動
Restart-Computer
```

##### 原因3: WSLカーネルが古いまたは破損

**解決手順：**
```powershell
# WSLカーネルを手動で更新
wsl --update --web-download

# WSLを完全にリセット（最終手段）
wsl --unregister Ubuntu
wsl --install -d Ubuntu-22.04
```

#### その他のよくあるエラー

##### エラー: 0x800701bc
```powershell
# WSL2カーネルが未インストール
# 解決方法：
wsl --update
```

##### エラー: 0x80370102
```powershell
# 仮想マシンが起動できない
# 解決方法：
bcdedit /set hypervisorlaunchtype auto
# PCを再起動
```

##### エラー: 0x80040326
```powershell
# WSL機能が無効
# 解決方法：
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all
# PCを再起動
```

---

### 🔧 トラブルシューティングチェックリスト

WSL2インストールで問題が発生した場合、以下の順番で確認してください：

#### ステップ1: 基本確認
- [ ] Windows 10 version 2004以降またはWindows 11を使用している
- [ ] 64ビット版Windowsを使用している
- [ ] 管理者権限でPowerShellを実行している

#### ステップ2: 仮想化確認
- [ ] タスクマネージャーで「仮想化: 有効」と表示されている
- [ ] BIOS/UEFIでVT-x（Intel）またはAMD-V（AMD）が有効

#### ステップ3: Windows機能確認
- [ ] 「Linux用Windowsサブシステム」が有効
- [ ] 「仮想マシンプラットフォーム」が有効
- [ ] 各機能を有効化後にPCを再起動した

#### ステップ4: WSL確認
- [ ] `wsl --status`が正常に動作する
- [ ] `wsl --update`で最新版に更新済み
- [ ] `wsl --set-default-version 2`を実行済み

#### ステップ5: 最終手段
問題が解決しない場合：
1. WSLを完全にアンインストール
   ```powershell
   wsl --shutdown
   wsl --unregister Ubuntu
   ```
2. Windows機能を無効化してPC再起動
3. Windows機能を再度有効化してPC再起動
4. WSL2を最初からインストール

---

### Ubuntu初期設定

Ubuntuを初めて起動すると、ユーザー名とパスワードの設定を求められます：

```bash
# ユーザー名を入力（英数字小文字、スペース不可）
Enter new UNIX username: yourname

# パスワードを設定（入力時は表示されません）
New password: 
Retype new password: 

# 設定完了メッセージ
Installation successful!
```

### 基本パッケージの更新

```bash
# パッケージリストを最新に更新
sudo apt update && sudo apt upgrade -y

# 開発に必要な基本ツールをインストール
sudo apt install -y git curl wget build-essential

# 日本語環境の設定（任意）
sudo apt install -y language-pack-ja
sudo update-locale LANG=ja_JP.UTF-8
```

### VS CodeとWSL2の連携設定

1. **VS Codeのインストール**（まだの場合）
   - [公式サイト](https://code.visualstudio.com/)からダウンロード
   - Windowsにインストール（WSL2内ではなく）

2. **WSL拡張機能のインストール**
   - VS Codeを起動
   - 拡張機能（Ctrl+Shift+X）を開く
   - 「WSL」で検索してインストール

3. **WSL内のプロジェクトを開く**
   ```bash
   # WSL2（Ubuntu）内で実行
   cd ~/projects/your-project
   code .
   ```

### パフォーマンス最適化（推奨）

#### Git操作が遅い場合の対処

```bash
# Windows側のファイル（/mnt/c/）ではなくWSL2内のファイルシステムを使用
cd ~  # WSL2のホームディレクトリ
mkdir -p projects
cd projects
# ここにプロジェクトを配置

# 速度比較
# 遅い: /mnt/c/Users/yourname/projects/
# 速い: ~/projects/
```

---

## 2️⃣ Gitのインストールと初期設定

### Gitのインストール

#### Windows (WSL2内)
```bash
# WSL2（Ubuntu）内で実行
sudo apt update
sudo apt install -y git

# インストール確認
git --version
# git version 2.34.1 のように表示されればOK
```

#### Mac
```bash
# Homebrewを使用（推奨）
brew install git

# または Xcodeコマンドラインツールをインストール
xcode-select --install
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install -y git
```

### Git初期設定

**必須設定**を行います：

```bash
# ユーザー情報設定（必須）
git config --global user.name "山田 太郎"  # あなたの名前
git config --global user.email "yamada@sas-com.co.jp"  # 会社メールアドレス

# エディタ設定
git config --global core.editor "code --wait"  # VS Code
# git config --global core.editor "vim"        # Vim
# git config --global core.editor "nano"       # Nano

# 日本語ファイル名の文字化け防止（必須）
git config --global core.quotepath false

# 改行コード設定
# Windows (WSL2内)
git config --global core.autocrlf input
git config --global core.eol lf

# Mac/Linux
git config --global core.autocrlf input

# プッシュ設定
git config --global push.default current

# プル設定（マージコミットを作成）
git config --global pull.rebase false

# カラー表示を有効化
git config --global color.ui auto

# 設定確認
git config --global --list
```

### よく使うエイリアスの設定（任意）

```bash
# 短縮コマンドを設定
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.lg "log --graph --oneline --all"
```

---

## 3️⃣ GitHubアカウントの作成

### 3.1 アカウント作成手順

1. **GitHubサイトにアクセス**
   ```
   https://github.com
   ```

2. **Sign upをクリック**
   - トップページ右上の「Sign up」ボタンをクリック

3. **必要情報を入力**

   | 項目 | 入力内容 | 注意点 |
   |------|---------|--------|
   | **Username** | 英数字とハイフン | 会社で使う場合は本名ベースを推奨（例: taro-yamada） |
   | **Email** | 会社メールアドレス | 個人メールではなく会社メールを使用 |
   | **Password** | 15文字以上推奨 | 大小英数字記号を含む強力なパスワード |

4. **メールアドレスの確認**
   - 確認コード入力画面が表示される
   - メールに届いた6桁のコードを入力

5. **アカウントのカスタマイズ**（スキップ可能）
   - チームで使うか：Yes, with my team
   - 学生か教師か：No
   - 興味のある分野：該当するものを選択

### 3.2 既存アカウントを業務利用する場合

既に個人アカウントを持っている場合の選択肢：

#### オプション1: 個人アカウントを業務でも使用（推奨）
```markdown
メリット：
- 既存のコントリビューション履歴を維持
- アカウント管理が簡単
- OSSコントリビューションがしやすい

設定変更：
1. Settings → Emails → Add email address
2. 会社メールアドレスを追加
3. 会社メールアドレスをPrimaryに設定（任意）
```

#### オプション2: 業務用アカウントを新規作成
```markdown
メリット：
- 個人と業務を完全分離
- 退職時の処理が簡単

デメリット：
- アカウント切り替えが必要
- SSH鍵の管理が複雑
```

---

## 4️⃣ プロフィール設定

### 4.1 基本プロフィール設定

1. **プロフィールページにアクセス**
   - 右上のアバター → Settings → Profile

2. **必須項目の入力**

   | 項目 | 設定内容 | 例 |
   |------|---------|-----|
   | **Name** | 本名（日本語可） | 山田 太郎 |
   | **Bio** | 簡単な自己紹介 | Software Engineer at SAS Inc. |
   | **Company** | 会社名 | @sas-com または エス・エー・エス株式会社 |
   | **Location** | 勤務地 | Tokyo, Japan |
   | **Email** | 公開メール | 表示する場合は会社メール |

3. **プロフィール画像の設定**（推奨）
   - 顔写真またはアバター画像をアップロード
   - 推奨サイズ：400×400px以上
   - ファイル形式：JPG、PNG

### 4.2 プロフィールREADME作成（任意）

```markdown
1. 新規リポジトリを作成
   - リポジトリ名：自分のユーザー名と同じ
   - Public設定
   - "Add a README file"にチェック

2. README.md を編集
```

**README.md テンプレート例：**

```markdown
### Hi there 👋

#### I'm Taro Yamada
- 🏢 Software Engineer at S.A.S Corporation
- 💻 Specializing in Web Development
- 🌱 Currently learning Cloud Architecture
- 📫 How to reach me: yamada@sas-com.co.jp

#### Technologies & Tools
![](https://img.shields.io/badge/Code-JavaScript-informational?style=flat&logo=javascript)
![](https://img.shields.io/badge/Code-Python-informational?style=flat&logo=python)
![](https://img.shields.io/badge/Tools-Docker-informational?style=flat&logo=docker)
```

---

## 5️⃣ セキュリティ設定【重要】

### 5.1 2要素認証（2FA）の設定 ※必須

**2FAを設定しないと組織へ参加できません**

1. **設定画面にアクセス**
   ```
   Settings → Password and authentication → Two-factor authentication
   ```

2. **Enable two-factor authenticationをクリック**

3. **認証方法の選択**

   | 方法 | 推奨度 | 説明 |
   |------|--------|------|
   | **認証アプリ** | ⭐⭐⭐ | 最も安全（推奨） |
   | **SMS** | ⭐⭐ | 電話番号が必要 |
   | **セキュリティキー** | ⭐⭐⭐ | 物理キーが必要 |

4. **認証アプリの設定（推奨）**

   **推奨アプリ：**
   - Google Authenticator（iOS/Android）
   - Microsoft Authenticator（iOS/Android）
   - Authy（iOS/Android/Desktop）

   **設定手順：**
   ```markdown
   1. スマートフォンで認証アプリをインストール
   2. アプリを開いて「+」または「アカウント追加」
   3. QRコードをスキャン（またはシークレットキーを入力）
   4. 表示された6桁のコードをGitHubに入力
   5. リカバリーコードをダウンロードして安全に保管
   ```

5. **リカバリーコードの保管**
   ```markdown
   ⚠️ 重要：必ず安全な場所に保管してください
   - パスワードマネージャーに保存
   - 印刷して施錠可能な場所に保管
   - 会社の機密情報管理システムに登録
   ```

### 5.2 セキュリティログの確認

定期的にセキュリティログを確認：
```
Settings → Security → Security log
```

異常なアクセスがないか確認してください。

---

## 6️⃣ SSH鍵の設定

### 6.1 SSH鍵の生成

**Windows (WSL2で実行)：**

```bash
# 1. SSH鍵を生成
ssh-keygen -t ed25519 -C "yamada@sas-com.co.jp"

# 以下のプロンプトが表示されたらEnterを押す
# Enter file in which to save the key (/home/user/.ssh/id_ed25519): [Enter]
# Enter passphrase (empty for no passphrase): [パスフレーズを入力 or Enter]
# Enter same passphrase again: [同じパスフレーズを入力 or Enter]

# 2. SSH鍵が生成されたことを確認
ls -la ~/.ssh/
# id_ed25519（秘密鍵）とid_ed25519.pub（公開鍵）が存在することを確認
```

### 6.2 GitHubへのSSH鍵登録

```bash
# 1. 公開鍵の内容をコピー
# WSL2で実行:
cat ~/.ssh/id_ed25519.pub | clip.exe

# または手動でコピー:
cat ~/.ssh/id_ed25519.pub
# 表示された内容を選択してコピー
```

**GitHub側の設定：**

1. **SSH鍵設定画面にアクセス**
   ```
   Settings → SSH and GPG keys → New SSH key
   ```

2. **鍵情報を入力**
   - **Title**: 識別しやすい名前（例：会社PC-WSL2）
   - **Key type**: Authentication Key
   - **Key**: コピーした公開鍵をペースト

3. **Add SSH keyをクリック**

### 6.3 接続テスト

```bash
# SSH接続テスト
ssh -T git@github.com

# 初回接続時の確認メッセージ
# The authenticity of host 'github.com (xxx.xxx.xxx.xxx)' can't be established.
# Are you sure you want to continue connecting (yes/no/[fingerprint])? yes

# 成功時のメッセージ
# Hi username! You've successfully authenticated, but GitHub does not provide shell access.
```

### 6.4 複数アカウントを使い分ける場合

**~/.ssh/config の設定：**

```bash
# 個人アカウント
Host github.com-personal
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_personal

# 会社アカウント
Host github.com-work
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_work

# 使用例
# git clone git@github.com-work:sas-com/repository.git
```

---

## 7️⃣ 組織への参加

### 7.1 招待の受け取り

1. **招待メールを確認**
   - 件名：`[GitHub] You've been invited to join sas-com organization`
   
2. **招待リンクをクリック**
   - メール内の「View invitation」ボタンをクリック

3. **招待を承認**
   - 「Join sas-com」ボタンをクリック

### 7.2 組織の設定確認

**プロフィールの公開設定：**
```
組織ページ → People → 自分のアカウント → Public/Private選択
```

- **Public**: 組織メンバーであることを公開
- **Private**: 組織メンバーであることを非公開

---

## 8️⃣ 通知設定

### 8.1 メール通知設定

```
Settings → Notifications → Email notification preferences
```

**推奨設定：**
- ✅ Comments on Issues and Pull Requests
- ✅ Pull Request reviews
- ✅ Pull Request pushes
- ⬜ Include your own updates（自分の更新は除外）

### 8.2 Web通知設定

```
Settings → Notifications → Web and mobile notifications
```

重要な通知のみ受け取るように設定することを推奨。

---

## 9️⃣ トラブルシューティング

### よくある問題と解決方法

#### WSL2関連の問題

##### Git操作が異常に遅い
```markdown
原因：
- Windows側のファイルシステム（/mnt/c/）を使用している
- WSL1を使用している

解決方法：
1. WSL2内のファイルシステムを使用
   cd ~/projects  # /mnt/c/ ではなく
2. WSL2へアップグレード
   wsl --set-version Ubuntu 2
```

##### 改行コードの問題でファイル全体が変更扱いになる
```bash
# .gitattributesファイルを作成（プロジェクトルート）
echo "* text=auto eol=lf" > .gitattributes
git add .gitattributes
git commit -m "chore: 改行コードをLFに統一"

# 既存ファイルの改行コードを統一
git add --renormalize .
git commit -m "chore: 既存ファイルの改行コードを統一"
```

#### 2FA設定後にログインできない
```markdown
解決方法：
1. リカバリーコードを使用してログイン
2. Settings → Password and authentication
3. 2FAを一度無効化して再設定
```

#### SSH接続が失敗する
```bash
# SSHエージェントを起動
eval "$(ssh-agent -s)"

# 鍵を追加
ssh-add ~/.ssh/id_ed25519

# 詳細なデバッグ情報を表示
ssh -vT git@github.com
```

#### Permission denied (publickey)
```bash
# 正しい鍵が使われているか確認
ssh -vT git@github.com

# 鍵の権限を修正
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub
chmod 700 ~/.ssh
```

#### 組織に参加できない
```markdown
原因：
- 2FAが設定されていない
- メールアドレスが未確認
- 招待の有効期限切れ

解決：
1. 2FAを設定
2. メールアドレスを確認（Settings → Emails）
3. 管理者に再招待を依頼
```

---

## 🔐 セキュリティベストプラクティス

### やるべきこと ✅

1. **強力なパスワードを使用**
   - 15文字以上
   - 大小英数字記号を含む
   - パスワードマネージャーの使用推奨

2. **2FAを必ず有効化**
   - 認証アプリの使用推奨
   - リカバリーコードを安全に保管

3. **定期的な確認**
   - アクセスログの確認（月1回）
   - SSH鍵の棚卸し（年2回）
   - 権限の見直し（四半期ごと）

4. **個人用トークンの管理**
   - 最小限の権限のみ付与
   - 有効期限を設定
   - 不要になったら即削除

### やってはいけないこと ❌

1. **パスワードの使い回し**
2. **2FAの無効化**
3. **公共のPCでのログイン**
4. **トークンのハードコード**
5. **秘密鍵の共有**

---

## 📚 参考リンク

### GitHub公式ドキュメント
- [GitHubアカウント作成](https://docs.github.com/ja/get-started/signing-up-for-github)
- [2FA設定ガイド](https://docs.github.com/ja/authentication/securing-your-account-with-two-factor-authentication-2fa)
- [SSH接続ガイド](https://docs.github.com/ja/authentication/connecting-to-github-with-ssh)

### 社内ドキュメント
- [全社GitHub運用ガイドライン](./README.md)
- [新規参画者向けオンボーディング](./ONBOARDING.md)
- [クイックリファレンス](./QUICK_REFERENCE.md)

---

## 📞 サポート

設定で困った場合の連絡先：

| 内容 | 連絡先 | 対応時間 |
|------|--------|----------|
| アカウント作成支援 | SAS Github管理チーム (github@sas-com.com) | 平日 9:00-18:00 |
| 技術的な質問 | SAS Github管理チーム (github@sas-com.com) | 平日 9:00-18:00 |
| 組織への招待 | SAS Github管理チーム (github@sas-com.com) | 営業時間内 |

---

## ✅ 最終チェックリスト

アカウント設定が完了したら、以下を確認：

- [ ] GitHubにログインできる
- [ ] 2FAが有効になっている
- [ ] SSH接続テストが成功する
- [ ] 組織（sas-com）に参加している
- [ ] プロフィール情報が設定されている
- [ ] Git設定が完了している
- [ ] メール通知が適切に設定されている
- [ ] リカバリーコードを安全に保管している

すべてチェックできたら、開発業務を開始できます！

---

**© 2025 エス・エー・エス株式会社 - GitHub環境構築ガイド**