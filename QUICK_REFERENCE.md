# GitHub クイックリファレンスガイド

**エス・エー・エス株式会社**  
*開発者向け簡易マニュアル*

## 🚀 日常作業フロー

### 1️⃣ 作業開始（朝一番）

```bash
# 最新情報を取得
git checkout develop
git pull origin develop

# 作業ブランチを作成
git checkout -b feature/123-new-feature

# または既存ブランチで作業継続
git checkout feature/existing-feature
git merge develop  # 最新のdevelopを取り込む
```

### 2️⃣ コーディング作業

```bash
# 作業状況確認
git status

# 変更を確認
git diff

# ステージング（個別ファイル）
git add path/to/file

# ステージング（全ファイル）※注意深く
git add .

# コミット
git commit -m "feat(module): 機能説明"
```

### 3️⃣ プッシュ & PR作成

```bash
# リモートにプッシュ
git push origin feature/123-new-feature

# GitHubでPR作成
# 1. リポジトリページへアクセス
# 2. "Compare & pull request" ボタンをクリック
# 3. テンプレートに従って記入
# 4. レビュアーをアサイン
```

### 4️⃣ レビュー対応

```bash
# レビューコメントに基づいて修正
git add .
git commit -m "fix: レビュー指摘事項を修正"
git push origin feature/123-new-feature
```

### 5️⃣ マージ後の処理

```bash
# developに戻る
git checkout develop
git pull origin develop

# 作業ブランチを削除
git branch -d feature/123-new-feature
git push origin --delete feature/123-new-feature
```

---

## 📝 コミットメッセージ早見表

| やったこと | Type | 例 |
|-----------|------|-----|
| 新機能追加 | `feat:` | feat: ログイン機能を追加 |
| バグ修正 | `fix:` | fix: ログインエラーを修正 |
| ドキュメント | `docs:` | docs: READMEを更新 |
| 見た目・フォーマット | `style:` | style: インデントを統一 |
| リファクタリング | `refactor:` | refactor: 関数を分割 |
| テスト | `test:` | test: ユニットテストを追加 |
| 雑務・その他 | `chore:` | chore: パッケージを更新 |

**基本フォーマット**:
```
タイプ: 機能名
詳細説明（任意）
Issue: #番号
```

---

## 🏷️ Issue/PR ラベル使い方

### 必ず付けるラベル（優先度）

- 🔴 `priority: critical` - 今すぐ対応
- 🟠 `priority: high` - 今日中に対応  
- 🟡 `priority: medium` - 今週中に対応
- 🟢 `priority: low` - 時間があるときに

### 必ず付けるラベル（種別）

- `bug` - バグ
- `enhancement` - 新機能
- `documentation` - ドキュメント
- `question` - 質問

### 状態を示すラベル

- `status: in progress` - 作業中
- `status: review` - レビュー中
- `status: blocked` - 何かを待っている
- `status: pending` - 保留中

### 工数ラベル

- `size: XS` - 1時間以内
- `size: S` - 半日
- `size: M` - 1-2日
- `size: L` - 3-5日
- `size: XL` - 1週間以上

---

## 🔥 緊急時の対応

### Hotfixの作り方

```bash
# mainから直接ブランチを作成
git checkout main
git pull origin main
git checkout -b hotfix/999-urgent-fix

# 修正作業
# ...

# コミット & プッシュ
git add .
git commit -m "hotfix: 緊急バグを修正"
git push origin hotfix/999-urgent-fix

# PR作成（mainへ）
# レビュー最優先で依頼

# マージ後、developにも反映
git checkout develop
git pull origin develop
git merge main
git push origin develop
```

### 間違えたときの対処

#### コミットメッセージを間違えた（プッシュ前）
```bash
git commit --amend -m "正しいメッセージ"
```

#### 間違えてコミットした（プッシュ前）
```bash
# 直前のコミットを取り消し（変更は残る）
git reset --soft HEAD^

# 直前のコミットを取り消し（変更も消える）
git reset --hard HEAD^
```

#### 機密情報をコミットしてしまった
```bash
# 1. すぐに報告！
# 2. 該当ファイルを履歴から削除
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch [ファイル名]' \
  --prune-empty --tag-name-filter cat -- --all

# 3. 強制プッシュ
git push origin --force --all
```

---

## 👀 コードレビュー時のチェックポイント

### レビュアーとして

```markdown
最低限確認すること：
□ 動作するか
□ テストはあるか
□ セキュリティ的に問題ないか
□ パフォーマンスは大丈夫か
□ 読みやすいか
```

### 良いレビューコメントの例

```markdown
✅ 「この部分は〇〇関数を使うとシンプルになります」
✅ 「セキュリティ的に△△の処理が必要です」
✅ 「このロジックの意図を教えてください」

❌ 「なんでこうしたの？」
❌ 「ダメ」
❌ 「私ならこうする」
```

---

## 🔗 よく使うコマンド集

### ブランチ関連

```bash
# ブランチ一覧
git branch -a

# ブランチ切り替え
git checkout branch-name

# ブランチ作成して切り替え
git checkout -b new-branch

# ブランチ削除（ローカル）
git branch -d branch-name

# ブランチ削除（リモート）
git push origin --delete branch-name

# ブランチ名変更
git branch -m old-name new-name
```

### 変更の取り消し

```bash
# ファイルの変更を取り消し
git checkout -- file-name

# ステージングを取り消し
git reset HEAD file-name

# すべての変更を破棄
git reset --hard HEAD
```

### 履歴確認

```bash
# コミット履歴（簡潔）
git log --oneline -10

# コミット履歴（グラフ付き）
git log --graph --oneline --all

# 特定ファイルの履歴
git log -p file-name

# 誰が変更したか確認
git blame file-name
```

### リモート操作

```bash
# リモート情報確認
git remote -v

# 最新情報取得（マージなし）
git fetch origin

# 特定ブランチをプル
git pull origin branch-name

# 強制プッシュ（危険！）
git push --force origin branch-name
```

### 一時退避（stash）

```bash
# 現在の変更を一時退避
git stash

# 退避した変更を戻す
git stash pop

# 退避リストを確認
git stash list

# 特定の退避を適用
git stash apply stash@{0}

# 退避をクリア
git stash clear
```

---

## 📱 GitHub CLI を使った操作

### インストール
```bash
# Mac
brew install gh

# Ubuntu/Debian
apt install gh

# Windows (winget)
winget install --id GitHub.cli

# 認証
gh auth login
```

### よく使うコマンド

```bash
# PR作成
gh pr create --title "Title" --body "Description"

# PR一覧
gh pr list

# PRをチェックアウト
gh pr checkout 123

# PRの状態確認
gh pr status

# Issue作成
gh issue create --title "Title" --body "Description"

# Issue一覧
gh issue list --assignee @me

# リポジトリをクローン
gh repo clone owner/repo
```

---

## 🆘 トラブルシューティング

### よくある問題

#### 「Permission denied」エラー
```bash
# SSH鍵が設定されているか確認
ssh -T git@github.com

# SSH鍵を追加
ssh-add ~/.ssh/id_ed25519
```

#### マージコンフリクトが発生
```bash
# 1. 競合ファイルを確認
git status

# 2. ファイルを編集して競合を解決
# <<<<<<<, =======, >>>>>>> を削除

# 3. 解決したらコミット
git add .
git commit -m "resolve: コンフリクトを解決"
```

#### プッシュが拒否される
```bash
# リモートの最新を取得してマージ
git pull origin branch-name

# それでもダメなら強制プッシュ（注意！）
git push --force-with-lease origin branch-name
```

---

## 📞 困ったときの連絡先

| 内容 | 連絡先 | 対応時間 |
|------|--------|----------|
| **技術的な質問** | SAS Github管理チーム (github@sas-com.com) | 平日 9:00-18:00 |
| **権限・アクセス** | SAS Github管理チーム (github@sas-com.com) | 平日 9:00-18:00 |
| **緊急トラブル** | 担当プロジェクトマネージャー | 24時間 |

---

## 📚 もっと詳しく知りたいとき

- [詳細な運用ガイドライン](./README.md)
- [GitHub公式ドキュメント](https://docs.github.com)
- [Git チートシート](https://training.github.com/downloads/ja/github-git-cheat-sheet.pdf)
- [Pro Git Book（日本語）](https://git-scm.com/book/ja/v2)

---

## 💡 Tips & ベストプラクティス

### 作業を効率化するコツ

1. **エイリアスを設定する**
```bash
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status
```

2. **コミットは細かく、頻繁に**
   - 1つのコミット = 1つの変更
   - レビューしやすい単位で

3. **ブランチ名は分かりやすく**
   - 良い例: `feature/123-user-authentication`
   - 悪い例: `my-work`, `test`, `fix`

4. **プルリクエストは小さく**
   - 大きなPR = レビューが遅れる
   - 200行以内が理想

5. **定期的にpullする**
   - 毎朝必ず最新を取得
   - コンフリクトを最小限に

---

**迷ったら聞く！一人で悩まない！**

---

**© 2025 エス・エー・エス株式会社**