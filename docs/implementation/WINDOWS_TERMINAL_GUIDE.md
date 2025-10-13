# Windows Terminal 活用ガイド

**エス・エー・エス株式会社**
*WSL2とGit作業を効率化するWindows Terminal完全ガイド*
*最終更新: 2025年10月13日*

---

## 📚 目次

1. **[🎯 はじめに](#-はじめに)**
   - Windows Terminalとは
   - 本ガイドの対象者
   - 利用は任意です

2. **[💡 なぜWindows Terminalを使うのか](#-なぜwindows-terminalを使うのか)**
   - Windows Terminalの利点
   - 開発効率の向上
   - Git作業の最適化

3. **[📥 インストール方法](#-インストール方法)**
   - 方法A: Microsoft Store（推奨）
   - 方法B: GitHub から直接ダウンロード
   - 方法C: Winget

4. **[⚙️ 基本設定](#️-基本設定)**
   - 設定ファイルの場所
   - 推奨設定項目
   - WSL2連携設定

5. **[🚀 効率的な使い方](#-効率的な使い方)**
   - ショートカット一覧
   - 実践的な活用例
   - タブとペイン管理

6. **[🎨 テーマとカスタマイズ](#-テーマとカスタマイズ)**
   - 人気のテーマ
   - フォント推奨
   - 見た目のカスタマイズ

7. **[🔧 トラブルシューティング](#-トラブルシューティング)**
   - よくある問題と解決方法

8. **[💡 活用のメリット](#-活用のメリット)**
   - 開発作業での実感
   - チーム作業での利点

---

## 🎯 はじめに

### 📌 Windows Terminalとは

Windows Terminal は Microsoft が開発した新しいターミナルアプリケーションで、PowerShell と WSL2 の両方で優れた体験を提供します。

従来のコマンドプロンプトやPowerShell ISEと比較して、以下のような特徴があります：

- **モダンなUI**: タブ機能、分割ペイン、フォントレンダリング
- **統合環境**: PowerShell、WSL2、Git Bashを1つのウィンドウで管理
- **高いカスタマイズ性**: テーマ、フォント、キーバインドの自由な設定
- **Unicode完全サポート**: 日本語を含むあらゆる文字の正しい表示

### 👥 対象者

このガイドは以下の方を対象としています：

- WSL2でGit開発を行うエンジニア
- ターミナル作業の効率化を図りたい方
- より快適な開発環境を構築したい方

### ⚠️ 利用は任意です

> 💡 **重要な注意事項**
> Windows Terminalの利用は**任意**です。標準のコマンドプロンプトやPowerShellでも全ての作業を行うことができます。
> このガイドは、より快適な開発体験を求める方のための参考情報として提供しています。

---

## 💡 なぜWindows Terminalを使うのか

### 📊 Windows Terminal の利点

| 従来のツール | Windows Terminal |
|--------------|------------------|
| コマンドプロンプト | ✅ **タブ機能**で複数セッション管理 |
| PowerShell ISE | ✅ **Unicode完全サポート**（日本語表示） |
| 個別ウィンドウ | ✅ **統合環境**（PowerShell + WSL2） |
| 限定的なカスタマイズ | ✅ **豊富なテーマ**とフォント設定 |
| コピペが不便 | ✅ **Ctrl+C/V**で直感的操作 |

### 🎯 開発効率の向上

**タブ管理の利点：**
- PowerShell、Ubuntu（WSL2）、Git Bashを1つのウィンドウで切り替え
- 複数のプロジェクトを並行して作業可能
- ウィンドウの切り替えによる時間ロスの削減

**分割ペインの活用：**
- 画面を分割してコマンドとログを同時表示
- エディタとターミナルを同一画面で管理
- 作業の流れが中断されない

**フォントの改善：**
- Cascadia Code フォントで読みやすいコード表示
- リガチャ（合字）対応で記号が見やすい
- 目の疲労を軽減

### 🚀 Git作業の最適化

**WSL2との統合：**
- WSL2とPowerShellを瞬時に切り替え
- LinuxコマンドとWindowsツールの併用が容易
- ファイルパスの行き来がスムーズ

**複数リポジトリの管理：**
- タブごとに異なるリポジトリを開く
- 並行作業時の切り替えが高速
- コミット、プッシュ作業の効率化

**ログ出力の見やすさ：**
- Git logの色分けが美しく表示
- 長いコマンド出力もスクロールバックで確認
- 検索機能でログから必要な情報を素早く抽出

---

## 📥 インストール方法

> 📌 **インストール方法について**
> Windows Terminal のインストールには **3つの方法** があります。お使いの環境に応じて、いずれか1つを選択してください。

### 方法A: Microsoft Store（推奨）

1. **Microsoft Store を開く**
2. **「Windows Terminal」** で検索
3. **入手/インストール** をクリック

**メリット：**
- 自動更新が有効
- インストールが最も簡単
- 公式サポート

### 方法B: GitHub から直接ダウンロード

```powershell
# PowerShellで直接ダウンロード（最新版）
# 1. GitHubリリースページにアクセス
# https://github.com/microsoft/terminal/releases

# 2. Assets から .msixbundle をダウンロード
# Microsoft.WindowsTerminal_Win10_1.18.xxx.0_8wekyb3d8bbwe.msixbundle

# 3. ダブルクリックでインストール
```

**メリット：**
- 最新のプレビュー版を試せる
- Microsoft Storeにアクセスできない環境でも利用可能

### 方法C: Winget（パッケージマネージャ）

```powershell
# PowerShellで実行
winget install --id Microsoft.WindowsTerminal -e
```

**メリット：**
- コマンドラインで完結
- スクリプト化が可能
- 他のツールと一括インストール可能

---

## ⚙️ 基本設定

> ⚠️ **重要な注意事項**
> 以下の設定はあくまで **参考例** です。実際の設定は、お使いのPC環境や個人の好みによって異なります。
> 特にファイルパスやユーザー名の部分は、ご自身の環境に合わせて変更してください。

### 設定ファイルの場所

Windows Terminalの設定は、JSON形式のファイルで管理されています。

**設定画面を開く方法：**
```
Ctrl + , で設定画面を開く
または
メニュー → 設定 → 左下の「JSONファイルを開く」
```

**設定ファイルのパス：**
```
%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json
```

### 推奨設定項目（参考例）

**Git/WSL2最適化設定：**

```json
{
  "defaultProfile": "{2c4de342-38b7-51cf-b940-2309a097f518}",
  "profiles": {
    "defaults": {
      "fontFace": "Cascadia Code",
      "fontSize": 11,
      "cursorShape": "bar",
      "colorScheme": "One Half Dark"
    },
    "list": [
      {
        "guid": "{2c4de342-38b7-51cf-b940-2309a097f518}",
        "name": "Ubuntu",
        "source": "Windows.Terminal.Wsl",
        "startingDirectory": "//wsl$/Ubuntu/home/yourname"
      }
    ]
  },
  "actions": [
    {
      "command": { "action": "copy", "singleLine": false },
      "keys": "ctrl+c"
    },
    {
      "command": "paste",
      "keys": "ctrl+v"
    }
  ]
}
```

**設定項目の説明：**

| 項目 | 説明 | 推奨値 |
|------|------|--------|
| `defaultProfile` | 起動時に開くプロファイル | Ubuntuのguid |
| `fontFace` | 使用するフォント | Cascadia Code |
| `fontSize` | フォントサイズ | 11 |
| `cursorShape` | カーソルの形状 | bar（縦線） |
| `colorScheme` | カラーテーマ | One Half Dark |
| `startingDirectory` | 起動時のディレクトリ | WSL2ホームディレクトリ |

---

## 🚀 効率的な使い方

### ショートカット一覧

**基本操作：**

| 操作 | ショートカット | 用途 |
|------|---------------|------|
| **新しいタブ** | `Ctrl + Shift + T` | 新しいシェルセッション |
| **タブを閉じる** | `Ctrl + Shift + W` | 現在のタブを閉じる |
| **タブ切り替え** | `Ctrl + Tab` | 次のタブへ移動 |
| **タブ切り替え（逆）** | `Ctrl + Shift + Tab` | 前のタブへ移動 |
| **タブを指定** | `Ctrl + Alt + 数字` | N番目のタブへ移動 |

**ペイン操作：**

| 操作 | ショートカット | 用途 |
|------|---------------|------|
| **ペイン分割（横）** | `Alt + Shift + -` | 画面を横に分割 |
| **ペイン分割（縦）** | `Alt + Shift + +` | 画面を縦に分割 |
| **ペイン移動** | `Alt + 矢印キー` | フォーカスを移動 |
| **ペインを閉じる** | `Ctrl + Shift + W` | 現在のペインを閉じる |
| **ペインサイズ変更** | `Alt + Shift + 矢印キー` | ペインサイズを調整 |

**編集操作：**

| 操作 | ショートカット | 用途 |
|------|---------------|------|
| **コピー** | `Ctrl + C` | 選択したテキストをコピー |
| **ペースト** | `Ctrl + V` | クリップボードから貼り付け |
| **検索** | `Ctrl + Shift + F` | 出力内容を検索 |
| **スクロール** | `Ctrl + Shift + ↑/↓` | 1行ずつスクロール |

### 実践的な活用例

**シナリオ1: Git開発作業**

```bash
# タブ1: メインの作業用WSL2
cd ~/projects/my-repo
git status
git log --oneline

# タブ2: ログ監視用
tail -f /var/log/application.log

# タブ3: PowerShellでWindowsツール実行
# Windows側のファイル管理、VSCodeの起動など
```

**シナリオ2: 分割ペインでの作業**

```bash
# 左ペイン: Git操作
cd ~/projects/my-repo
git log --oneline --graph --all

# 右ペイン: ファイル編集やテスト実行
code ./README.md
npm test
```

**シナリオ3: 複数プロジェクトの並行作業**

```bash
# タブ1: プロジェクトA
cd ~/projects/project-a
git checkout feature/new-feature

# タブ2: プロジェクトB
cd ~/projects/project-b
git checkout hotfix/bug-123

# タブ3: プロジェクトC（レビュー用）
cd ~/projects/project-c
git diff main..feature/pr-456
```

---

## 🎨 テーマとカスタマイズ

### 人気のテーマ

**暗いテーマ：**
- **One Half Dark**: 暗いテーマ、目に優しい（推奨）
- **Solarized Dark**: コーディング向けの定番テーマ
- **Dracula**: 鮮やかな色使いの人気テーマ
- **Monokai**: エディタでお馴染みのテーマ

**明るいテーマ：**
- **One Half Light**: One Half Darkの明るい版
- **Solarized Light**: Solarized Darkの明るい版
- **Campbell**: PowerShell標準テーマ

### フォント推奨

**プログラミング用フォント：**

| フォント名 | 特徴 | 入手方法 |
|-----------|------|----------|
| **Cascadia Code** | Microsoft製、プログラミング最適化、リガチャ対応 | Windows Terminal標準搭載 |
| **JetBrains Mono** | 読みやすさ重視、リガチャ対応 | https://www.jetbrains.com/lp/mono/ |
| **Fira Code** | リガチャ対応の定番フォント | https://github.com/tonsky/FiraCode |
| **Source Code Pro** | Adobe製、シンプルで読みやすい | https://adobe-fonts.github.io/source-code-pro/ |

**フォントのインストール方法：**
1. フォントファイル（.ttf または .otf）をダウンロード
2. ファイルを右クリック → 「インストール」
3. Windows Terminalの設定で`fontFace`を変更

### 見た目のカスタマイズ

**背景の透明化：**

```json
{
  "profiles": {
    "defaults": {
      "opacity": 90,
      "useAcrylic": true
    }
  }
}
```

**タブの位置変更：**

```json
{
  "tabWidthMode": "equal",
  "showTabsInTitlebar": true
}
```

---

## 🔧 トラブルシューティング

### WSL2が表示されない

**問題：**
Windows Terminalのプロファイル一覧にWSL2（Ubuntu）が表示されない

**解決方法：**
1. Windows Terminal を再起動
2. WSL2が正しくインストールされているか確認
   ```powershell
   wsl --list --verbose
   ```
3. 設定 → プロファイルを追加 → WSL を選択
4. それでも表示されない場合は、手動でプロファイルを追加

**手動プロファイル追加：**

```json
{
  "profiles": {
    "list": [
      {
        "guid": "{新しいGUID}",
        "name": "Ubuntu",
        "source": "Windows.Terminal.Wsl",
        "commandline": "wsl.exe -d Ubuntu"
      }
    ]
  }
}
```

### 日本語が文字化けする

**問題：**
日本語文字が正しく表示されない、または□（豆腐）になる

**解決方法：**

```json
{
  "profiles": {
    "defaults": {
      "fontFace": "Cascadia Code",
      "experimental.retroTerminalEffect": false
    }
  }
}
```

**追加の対策：**
- WSL2内のロケール設定を確認
  ```bash
  locale
  # LANG=en_US.UTF-8 であることを確認
  ```
- 日本語フォントをインストール
  ```bash
  sudo apt install fonts-noto-cjk
  ```

### コピー＆ペーストができない

**問題：**
Ctrl+C、Ctrl+Vでコピー＆ペーストができない

**解決方法：**

1. **設定でキーバインドを確認**
   - 設定 → アクション でキーバインドを確認
   - コピー：`Ctrl+C`、ペースト：`Ctrl+V`が設定されているか確認

2. **右クリックメニューを使用**
   - テキストを選択して右クリック → コピー
   - 右クリック → 貼り付け

3. **キーバインドを手動で設定**

```json
{
  "actions": [
    {
      "command": { "action": "copy", "singleLine": false },
      "keys": "ctrl+c"
    },
    {
      "command": "paste",
      "keys": "ctrl+v"
    }
  ]
}
```

### 起動が遅い

**問題：**
Windows Terminalの起動に時間がかかる

**解決方法：**

1. **不要なプロファイルを無効化**
   - 使用しないプロファイルを`"hidden": true`に設定

2. **起動時のディレクトリをローカルに変更**
   ```json
   {
     "profiles": {
       "list": [
         {
           "startingDirectory": "C:\\Users\\yourname"
         }
       ]
     }
   }
   ```

3. **バックグラウンドアクリル効果を無効化**
   ```json
   {
     "profiles": {
       "defaults": {
         "useAcrylic": false
       }
     }
   }
   ```

### フォントが表示されない

**問題：**
設定したフォントが適用されない

**解決方法：**

1. **フォント名を正確に確認**
   - Windowsの設定 → フォント でインストール済みフォントを確認
   - フォント名は大文字小文字、スペースも含めて正確に入力

2. **Windows Terminalを再起動**
   - フォントインストール後は必ず再起動

3. **フォールバックフォントを指定**
   ```json
   {
     "profiles": {
       "defaults": {
         "fontFace": "Cascadia Code, Consolas"
       }
     }
   }
   ```

---

## 💡 活用のメリット

### 開発作業での実感

**作業効率の向上：**
- Git操作の快適性が格段に向上
- コマンド履歴の検索が高速
- 複数プロジェクトの並行作業が簡単
- ログの確認とコマンド実行を同時に可能

**ストレスの軽減：**
- ウィンドウ切り替えの手間が削減
- 美しい表示で目の疲労が軽減
- キーボードショートカットで作業がスムーズ
- カスタマイズにより自分好みの環境を構築

**学習曲線：**
- 初期設定は少し時間がかかるが、一度設定すれば快適
- ショートカットは徐々に覚えていけばOK
- 設定ファイルをバックアップすれば、他のPCでも同じ環境を再現可能

### チーム作業での利点

**統一された作業環境：**
- チーム内で同じ設定を共有することで、サポートが容易
- 画面共有時の見やすさ向上
- トラブルシューティング効率の向上

**ナレッジ共有：**
- 便利なショートカットや設定をチーム内で共有
- 効率的な作業フローの標準化
- 新メンバーのオンボーディングが簡単

---

## 📝 参考資料

**公式ドキュメント：**
- [Windows Terminal 公式ドキュメント](https://docs.microsoft.com/ja-jp/windows/terminal/)
- [GitHub リポジトリ](https://github.com/microsoft/terminal)

**関連ガイド：**
- [GitHub 環境構築ガイド](../onboarding/GITHUB_ENVIRONMENT_SETUP.md) - 基本的な環境構築手順
- [VS Code Git統合ガイド](./IDE_VSCODE_GIT_GUIDE.md) - VS CodeとGitの統合
- [Eclipse Git統合ガイド](./IDE_ECLIPSE_GIT_GUIDE.md) - EclipseとGitの統合

---

**© 2025 エス・エー・エス株式会社 - Windows Terminal 活用ガイド**
