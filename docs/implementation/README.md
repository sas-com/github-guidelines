# IDE統合ガイド INDEX

**エス・エー・エス株式会社 GitHub運用ガイドライン**
*IDE統合関連ドキュメント一覧*

---

## 📁 ディレクトリ概要

このディレクトリ(`docs/implementation/`)には、開発環境のIDEとGitを統合するための詳細なガイドが格納されています。

---

## 🛠️ 開発ツールガイド

### Windows Terminal（任意）

**[WINDOWS_TERMINAL_GUIDE.md](./WINDOWS_TERMINAL_GUIDE.md)**

| 項目 | 内容 |
|------|------|
| **目的** | Windows TerminalでWSL2とGit作業を効率化 |
| **概要** | Windows Terminalのインストール、基本設定、WSL2連携、ショートカット、テーマカスタマイズ、トラブルシューティング |
| **対象者** | Windows環境のWSL2利用者 |
| **所要時間** | 15-30分（インストール・設定） |
| **利用** | **任意**（標準のコマンドプロンプト/PowerShellでも作業可能） |

**主な内容:**

1. **Windows Terminalの概要**
   - 従来のツールとの比較
   - 開発効率への影響
   - 利用が任意である理由

2. **インストール方法**
   - Microsoft Store（推奨）
   - GitHub直接ダウンロード
   - Wingetパッケージマネージャー

3. **基本設定とWSL2連携**
   - 設定ファイル（settings.json）の編集
   - 推奨設定項目
   - WSL2プロファイルの最適化

4. **効率的な使い方**
   - ショートカット一覧
   - タブとペインの活用
   - 実践的な活用例

5. **カスタマイズ**
   - テーマ設定
   - フォント選択
   - 見た目の調整

6. **トラブルシューティング**
   - WSL2が表示されない
   - 日本語の文字化け
   - コピー＆ペーストの問題
   - その他のよくある問題

---

### Visual Studio Code

**[IDE_VSCODE_GIT_GUIDE.md](./IDE_VSCODE_GIT_GUIDE.md)**

| 項目 | 内容 |
|------|------|
| **目的** | VS CodeでのGit統合完全活用ガイド |
| **概要** | VS Code Git機能の初期設定、WSL2連携、ソース管理ビュー、GitLens/GitHub Pull Requests拡張機能、コミット作成、ブランチ操作、コンフリクト解決 |
| **対象者** | VS Code利用者、全開発者 |
| **所要時間** | 30-45分 |
| **前提条件** | VS Code基本インストール完了、Git環境構築完了 |

**主な内容:**

1. **VS Code Git機能の基本設定**
   - Git統合の有効化
   - ソース管理ビューの基本操作
   - コミット作成とプッシュ

2. **WSL2連携設定（Windows環境）**
   - Remote-WSL拡張機能の設定
   - WSL2内のリポジトリ操作
   - パフォーマンス最適化

3. **拡張機能の活用**
   - GitLens: Git履歴の可視化
   - GitHub Pull Requests: PR管理
   - Git Graph: ブランチ視覚化

4. **実践的な操作**
   - ブランチ作成とチェックアウト
   - マージとリベース
   - コンフリクト解決
   - スタッシュ管理

5. **settings.jsonの推奨設定**
   - Git関連の設定項目
   - パフォーマンス最適化
   - UI/UXカスタマイズ

---

### Eclipse

**[IDE_ECLIPSE_GIT_GUIDE.md](./IDE_ECLIPSE_GIT_GUIDE.md)**

| 項目 | 内容 |
|------|------|
| **目的** | EclipseでのGit統合完全活用ガイド |
| **概要** | EGitプラグイン設定、Git Repositories/Stagingビュー、ブランチ操作、マージ、Historyビュー活用、推奨プラグイン |
| **対象者** | Eclipse利用者、Java開発者 |
| **所要時間** | 30-45分 |
| **前提条件** | Eclipse基本インストール完了、Git環境構築完了 |

**主な内容:**

1. **EGitプラグインの設定**
   - EGitのインストールと初期設定
   - Git設定の確認
   - SSH鍵の登録

2. **Git Repositoriesビュー**
   - リポジトリのクローン
   - リポジトリの追加
   - ブランチ管理

3. **Git Stagingビュー**
   - 変更のステージング
   - コミット作成
   - プッシュとプル操作

4. **実践的な操作**
   - ブランチの作成とチェックアウト
   - マージとリベース
   - コンフリクト解決ツール
   - Historyビューでの履歴確認

5. **推奨プラグイン**
   - EGit連携プラグイン
   - コードレビュー支援ツール
   - パフォーマンス最適化

---

## 📖 使い方

### 新規参画者の方

1. **環境構築を完了する**
   - [GitHub環境構築ガイド](../onboarding/GITHUB_ENVIRONMENT_SETUP.md)を参照
   - WSL2、Git、GitHubアカウントの設定を完了

2. **Windows Terminal の検討（任意・Windows環境のみ）**
   - より快適な開発体験を求める場合 → [WINDOWS_TERMINAL_GUIDE.md](./WINDOWS_TERMINAL_GUIDE.md)
   - 標準のコマンドプロンプト/PowerShellで十分な場合 → スキップ可能

3. **使用するIDEを選択**
   - VS Code利用者 → [IDE_VSCODE_GIT_GUIDE.md](./IDE_VSCODE_GIT_GUIDE.md)
   - Eclipse利用者 → [IDE_ECLIPSE_GIT_GUIDE.md](./IDE_ECLIPSE_GIT_GUIDE.md)

4. **ガイドに従って設定**
   - 各ガイドの手順に従ってIDE統合設定を実施
   - 推奨拡張機能/プラグインをインストール
   - 動作確認を実施

### 既存メンバーの方

**設定の見直しや最適化を行いたい場合:**
- 各ガイドの推奨設定セクションを参照
- 拡張機能/プラグインの活用方法を確認
- トラブルシューティングセクションで問題解決

---

## 🔗 関連ドキュメント

### 環境構築ガイド
- [GitHub環境構築ガイド](../onboarding/GITHUB_ENVIRONMENT_SETUP.md) - 基本的な開発環境のセットアップ
- [新規参画者向けオンボーディング](../onboarding/ONBOARDING.md) - 全体の流れ

### ワークフロー関連
- [コミット規約ガイドライン](../workflow/COMMIT_CONVENTION_GUIDE.md) - コミットメッセージの書き方
- [ブランチ管理ルール](../workflow/BRANCH_MANAGEMENT_RULES.md) - ブランチ戦略と命名規則

### リファレンス
- [クイックリファレンス](../../QUICK_REFERENCE.md) - よく使うコマンド一覧
- [緊急時対応マニュアル](../../EMERGENCY_RESPONSE.md) - トラブル発生時の対処法

---

## 📝 メンテナンス情報

- **最終更新**: 2025-10-13
- **メンテナー**: SAS GitHub管理チーム
- **レビューサイクル**: 四半期ごと
- **フィードバック**: github@sas-com.com

---

## ❓ よくある質問

### Q1: VS CodeとEclipse、どちらを使うべきですか？

**A:** プロジェクトの性質と個人の好みによります：

- **VS Code推奨**: 軽量で高速、幅広い言語対応、モダンなUI
- **Eclipse推奨**: Java開発に特化、強力なデバッグ機能、大規模プロジェクト向け

### Q2: 両方のIDEを使い分けることはできますか？

**A:** 可能です。ただし、以下の点に注意してください：

- SSH鍵の設定は共通で使用可能
- Git設定（user.name、user.email）も共通
- 各IDEのワークスペース設定は独立して管理

### Q3: IDEの設定を後から変更できますか？

**A:** はい、いつでも変更可能です。各ガイドの該当セクションを参照してください。

---

**© 2025 エス・エー・エス株式会社**
