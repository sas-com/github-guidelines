# GitHub アカウント作成・設定ガイド

**エス・エー・エス株式会社**  
*GitHubアカウントの作成から業務利用開始までの詳細手順*  
*最終更新: 2025年9月5日*

## 📌 はじめに

このガイドは、エス・エー・エス株式会社の業務でGitHubを利用するために必要なアカウント作成と初期設定の手順を説明します。
セキュリティを重視した設定を含みますので、**必ず全ての手順を完了**してください。

---

## 📋 作業チェックリスト

### 必須項目
- [ ] GitHubアカウント作成
- [ ] プロフィール設定
- [ ] 2要素認証（2FA）設定
- [ ] メール通知設定
- [ ] SSH鍵の生成と登録
- [ ] 組織への参加

### 推奨項目
- [ ] プロフィール画像設定
- [ ] READMEプロフィール作成
- [ ] GPG鍵の設定（コミット署名用）

---

## 1️⃣ GitHubアカウントの作成

### 1.1 アカウント作成手順

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

### 1.2 既存アカウントを業務利用する場合

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

## 2️⃣ プロフィール設定

### 2.1 基本プロフィール設定

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

### 2.2 プロフィールREADME作成（任意）

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

## 3️⃣ セキュリティ設定【重要】

### 3.1 2要素認証（2FA）の設定 ※必須

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

### 3.2 セキュリティログの確認

定期的にセキュリティログを確認：
```
Settings → Security → Security log
```

異常なアクセスがないか確認してください。

---

## 4️⃣ SSH鍵の設定

### 4.1 SSH鍵の生成

**Windows (WSL2) / Mac / Linux共通：**

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

### 4.2 GitHubへのSSH鍵登録

```bash
# 1. 公開鍵の内容をコピー
# Mac:
pbcopy < ~/.ssh/id_ed25519.pub

# Linux/WSL2:
cat ~/.ssh/id_ed25519.pub
# 表示された内容を手動でコピー

# Windows (Git Bash):
cat ~/.ssh/id_ed25519.pub | clip
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

### 4.3 接続テスト

```bash
# SSH接続テスト
ssh -T git@github.com

# 初回接続時の確認メッセージ
# The authenticity of host 'github.com (xxx.xxx.xxx.xxx)' can't be established.
# Are you sure you want to continue connecting (yes/no/[fingerprint])? yes

# 成功時のメッセージ
# Hi username! You've successfully authenticated, but GitHub does not provide shell access.
```

### 4.4 複数アカウントを使い分ける場合

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

## 5️⃣ Git設定

### 5.1 グローバル設定

```bash
# ユーザー情報設定
git config --global user.name "山田 太郎"
git config --global user.email "yamada@sas-com.co.jp"

# エディタ設定
git config --global core.editor "code --wait"  # VS Code
# git config --global core.editor "vim"         # Vim
# git config --global core.editor "nano"        # Nano

# 日本語ファイル名の文字化け防止
git config --global core.quotepath false

# 改行コード設定
# Windows
git config --global core.autocrlf true
# Mac/Linux
git config --global core.autocrlf input

# プッシュ設定
git config --global push.default current

# プル設定
git config --global pull.rebase false

# 設定確認
git config --global --list
```

### 5.2 認証情報の管理

**認証ヘルパーの設定：**

```bash
# Mac
git config --global credential.helper osxkeychain

# Windows
git config --global credential.helper manager

# Linux
git config --global credential.helper store  # 平文保存（非推奨）
# または
git config --global credential.helper cache  # 一時的にメモリに保存
```

---

## 6️⃣ 組織への参加

### 6.1 招待の受け取り

1. **招待メールを確認**
   - 件名：`[GitHub] You've been invited to join sas-com organization`
   
2. **招待リンクをクリック**
   - メール内の「View invitation」ボタンをクリック

3. **招待を承認**
   - 「Join sas-com」ボタンをクリック

### 6.2 組織の設定確認

**プロフィールの公開設定：**
```
組織ページ → People → 自分のアカウント → Public/Private選択
```

- **Public**: 組織メンバーであることを公開
- **Private**: 組織メンバーであることを非公開

---

## 7️⃣ 通知設定

### 7.1 メール通知設定

```
Settings → Notifications → Email notification preferences
```

**推奨設定：**
- ✅ Comments on Issues and Pull Requests
- ✅ Pull Request reviews
- ✅ Pull Request pushes
- ⬜ Include your own updates（自分の更新は除外）

### 7.2 Web通知設定

```
Settings → Notifications → Web and mobile notifications
```

重要な通知のみ受け取るように設定することを推奨。

---

## 8️⃣ トラブルシューティング

### よくある問題と解決方法

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

## 9️⃣ セキュリティベストプラクティス

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

**© 2025 エス・エー・エス株式会社 - GitHubアカウント作成・設定ガイド**