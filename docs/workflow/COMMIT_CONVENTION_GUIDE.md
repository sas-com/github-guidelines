# コミット規約ガイドライン

**エス・エー・エス株式会社**  
*Conventional Commitsベースのコミットメッセージ規約*

## 📋 概要

このドキュメントは、エス・エー・エス株式会社のすべてのプロジェクトで使用するコミットメッセージの規約を定義します。[Conventional Commits 1.0.0](https://www.conventionalcommits.org/)仕様をベースとし、組織の特性に合わせてカスタマイズしています。

## 🎯 規約の目的

- **一貫性**: チーム全体で統一されたコミット履歴
- **可読性**: 変更内容の迅速な理解
- **自動化**: CI/CDパイプラインとの連携
- **追跡性**: 変更履歴の効率的な検索・分析
- **品質向上**: レビュー効率の向上

## 📝 基本フォーマット

### 標準形式
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### 実例
```
feat(auth): ログイン機能にOAuth2.0サポートを追加

- Google、GitHub認証に対応
- 既存のパスワード認証と併用可能
- セッション管理を改善

Closes #123
Co-authored-by: tanaka@sas-com.com
```

## 🏷️ Type（変更タイプ）

### 必須タイプ
| Type | 説明 | 例 |
|------|------|-----|
| `feat` | 新機能の追加 | `feat(api): ユーザー検索APIを追加` |
| `fix` | バグ修正 | `fix(auth): ログイン時のバリデーションエラーを修正` |
| `docs` | ドキュメント変更のみ | `docs(readme): セットアップ手順を更新` |
| `style` | コードの動作に影響しないフォーマット変更 | `style(css): インデントを統一` |
| `refactor` | バグ修正や機能追加を含まないコード変更 | `refactor(utils): 日付処理関数を整理` |
| `test` | テストの追加・修正 | `test(auth): ログイン機能のテストケースを追加` |
| `chore` | ビルドプロセスや補助ツールの変更 | `chore(deps): ESLintをv8.0.0に更新` |

### 追加タイプ（SAS固有）
| Type | 説明 | 例 |
|------|------|-----|
| `security` | セキュリティ関連の修正 | `security(auth): SQLインジェクション脆弱性を修正` |
| `perf` | パフォーマンス改善 | `perf(db): クエリ実行速度を30%向上` |
| `build` | ビルドシステム変更 | `build(docker): マルチステージビルドを導入` |
| `ci` | CI設定変更 | `ci(github): テスト並列実行を有効化` |
| `revert` | コミットの取り消し | `revert: feat(api): ユーザー検索APIを削除` |
| `hotfix` | 緊急修正 | `hotfix(api): 本番障害の緊急修正` |

## 🎯 Scope（影響範囲）

### 推奨スコープ
| カテゴリ | Scope例 | 説明 |
|----------|---------|------|
| **機能領域** | `auth`, `api`, `ui`, `db`, `payment` | システムの機能領域 |
| **コンポーネント** | `header`, `sidebar`, `modal`, `form` | UIコンポーネント |
| **モジュール** | `user`, `product`, `order`, `notification` | ビジネスドメイン |
| **ツール** | `webpack`, `eslint`, `jest`, `docker` | 開発ツール |
| **環境** | `dev`, `staging`, `prod` | 環境固有 |
| **ドキュメント** | `readme`, `api-docs`, `changelog` | ドキュメント種類 |

### スコープなしの場合
以下の場合はスコープを省略できます：
- プロジェクト全体に影響する変更
- 初期コミット
- マイナーな修正

```
feat: プロジェクト初期セットアップ
fix: タイポを修正
docs: コントリビューションガイドを追加
```

## 📖 Description（説明文）

### 基本ルール
- **最大文字数**: 72文字以内（日本語の場合は50文字程度推奨）
- **語調**: 命令形（「追加する」ではなく「追加」）
- **大文字**: 最初は小文字で開始
- **句読点**: 末尾にピリオド不要
- **言語**: 日本語推奨（国際プロジェクトは英語）

### 良い例
```
✅ feat(auth): OAuth2.0ログイン機能を追加
✅ fix(api): ユーザー作成時の重複チェック処理を修正  
✅ docs(setup): 開発環境構築手順を更新
✅ refactor(utils): 日付フォーマット関数を共通化
```

### 悪い例
```
❌ feat: 機能を追加した。
❌ Fix: Bug fix
❌ update stuff
❌ feat(auth): OAuth2.0ログイン機能を追加しました（丁寧語）
```

## 📄 Body（詳細説明）

### 使用場面
- 変更の背景・理由の説明が必要な場合
- 複数の変更を含む場合
- 影響範囲が広い場合
- 設計判断の根拠を残したい場合

### フォーマット
```
feat(payment): クレジットカード決済機能を追加

以下の要件に対応：
- Stripe API連携
- 複数カード登録機能
- 定期支払い対応
- PCI DSS準拠のトークン化

既存の銀行振込機能はそのまま維持
```

### 書き方のコツ
- **箇条書き活用**: 複数の変更は箇条書きで整理
- **理由説明**: 「なぜ」その変更が必要だったかを記載
- **影響範囲**: どの機能に影響するかを明記
- **注意事項**: 既存機能への影響や注意点があれば記載

## 🏷️ Footer（フッター）

### Breaking Changes（破壊的変更）
```
BREAKING CHANGE: APIのレスポンス形式を変更

v1: { "data": {...} }
v2: { "result": {...}, "metadata": {...} }

マイグレーションガイド: docs/migration-v2.md
```

### Issue/PR参照
```
Closes #123
Closes #456, #789
Fixes #101
Resolves #202
Refs #303
```

### Co-authored-by
```
Co-authored-by: 田中太郎 <tanaka@sas-com.com>
Co-authored-by: 佐藤花子 <sato@sas-com.com>
```

### その他のフッター
```
Reviewed-by: 山田次郎 <yamada@sas-com.com>
Tested-by: QA Team <qa@sas-com.com>
Security-review: セキュリティチーム <security@sas-com.com>
```

## 🚨 Breaking Changes（破壊的変更）

### 表記方法
```
feat(api)!: ユーザーAPI v2.0を導入

BREAKING CHANGE: レスポンス形式を変更
- userInfo → profile に名称変更  
- 新フィールド: profile.lastLoginAt 追加
- 削除フィールド: profile.legacyId 廃止
```

### 必須情報
- 何が変更されたか
- 既存コードへの影響
- マイグレーション手順
- 影響するバージョン

## 💡 実践的な例

### 新機能開発
```
feat(notification): リアルタイム通知機能を追加

WebSocket接続によるリアルタイム通知システム：
- 新規メッセージ通知
- システムアラート通知  
- ユーザープレゼンス表示
- オフライン時の通知蓄積

技術スタック：
- Socket.io (サーバーサイド)
- WebSocket API (クライアントサイド)  
- Redis (通知キュー)

Closes #234
Co-authored-by: frontend-team@sas-com.com
```

### バグ修正
```
fix(auth): セッション期限切れ時の無限リダイレクトを修正

問題：
- ログイン期限切れ時に/loginと/dashboardの間で無限リダイレクト
- ブラウザがフリーズする問題

解決：
- セッション状態チェック処理を改善
- リダイレクトループ検出機能を追加
- エラーハンドリングを強化

Fixes #456
Tested-by: QA Team <qa@sas-com.com>
```

### ドキュメント更新
```
docs(api): REST API v2.0仕様書を追加

新しいAPIエンドポイントのドキュメント：
- OpenAPI 3.0形式で記述
- 認証方式の詳細説明追加
- エラーレスポンス例を充実
- Postmanコレクション同梱

Refs #789
```

### セキュリティ修正
```
security(auth): パスワードハッシュ化アルゴリズムを強化

変更内容：
- MD5 → bcrypt + salt (cost=12) に変更
- 既存パスワードの段階的マイグレーション
- パスワード強度チェック追加

BREAKING CHANGE: 最小パスワード長を8文字に変更

Security-review: セキュリティチーム <security@sas-com.com>
Closes #security-001
```

## 🎯 プロジェクト別カスタマイズ

### フロントエンド
```
feat(ui): モバイル対応レスポンシブデザインを追加
fix(css): IE11でのレイアウト崩れを修正
perf(js): バンドルサイズを25%削減
```

### バックエンド
```
feat(api): GraphQL APIエンドポイントを追加
fix(db): N+1クエリ問題を解決
perf(cache): Redis分散キャッシュを導入
```

### DevOps
```
ci(github): 自動デプロイパイプラインを追加
build(docker): マルチステージビルドでサイズ削減
chore(k8s): リソース制限値を最適化
```

## 🔍 よくある間違いと修正例

### ❌ 間違い例と ✅ 正しい例

#### 1. タイプの誤用
```
❌ update(api): API修正
✅ fix(api): レスポンス形式エラーを修正
```

#### 2. 説明が不十分
```
❌ feat: 機能追加
✅ feat(search): 高度検索機能を追加
```

#### 3. スコープの不適切な使用
```
❌ feat(src/components/user): ユーザー管理画面を追加
✅ feat(user): ユーザー管理画面を追加
```

#### 4. 複数の変更を1コミットに
```
❌ feat: ログイン機能追加とバグ修正とドキュメント更新

✅ 3つのコミットに分割:
   feat(auth): ログイン機能を追加
   fix(ui): レイアウトの表示崩れを修正  
   docs(readme): セットアップ手順を更新
```

## 📋 コミット前チェックリスト

### 基本チェック
- [ ] タイプは適切か（feat/fix/docs など）
- [ ] スコープは明確か（必要に応じて）
- [ ] 説明は72文字以内か
- [ ] 命令形で記述されているか
- [ ] 変更内容を正確に表現しているか

### 内容チェック  
- [ ] 論理的に1つの変更としてまとめられているか
- [ ] 機密情報（パスワード、APIキーなど）は含まれていないか
- [ ] テストは通るか
- [ ] 関連するIssueやPRの参照は正しいか

### 品質チェック
- [ ] コード品質は基準を満たしているか
- [ ] 破壊的変更がある場合、BREAKING CHANGEを記載したか
- [ ] 必要に応じてレビュアーを指定したか
- [ ] ドキュメントの更新は必要ないか

## 🛠️ ツール連携

### Git Hooks
```bash
# commit-msgフックでバリデーション
#!/bin/sh
./scripts/validate-commit-msg.sh "$1"
```

### IDE拡張
- **VS Code**: Conventional Commits拡張
- **JetBrains**: Git Commit Template プラグイン
- **Vim**: git-commit プラグイン

### CI/CD連携
```yaml
# GitHub Actions
- name: Validate commit messages
  uses: wagoid/commitlint-github-action@v5
  with:
    configFile: .commitlintrc.json
```

## 📊 メトリクス・分析

### 自動生成可能な情報
- **CHANGELOG**: タイプ別の変更履歴
- **リリースノート**: feat/fix の自動分類
- **貢献度分析**: 開発者別のコミット統計
- **品質指標**: fix/feat比率、コミット頻度

### 分析例
```bash
# 機能追加の数をカウント
git log --oneline --grep="^feat" --since="1 month ago" | wc -l

# バグ修正の統計
git log --oneline --grep="^fix" --since="1 month ago" --pretty=format:"%h %s" 
```

## 🔄 継続的改善

### 定期レビュー（月次）
- コミットメッセージ品質の確認
- よくある間違いの傾向分析
- ツール・プロセスの改善検討
- チームフィードバックの収集

### 教育・トレーニング
- 新入社員向けコミット規約研修
- 定期的なベストプラクティス共有
- コードレビュー時のガイダンス
- ツール使用方法の勉強会

## 📚 参考資料

### 外部リソース
- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [Angular Commit Message Guidelines](https://github.com/angular/angular/blob/main/CONTRIBUTING.md#commit)
- [Semantic Versioning](https://semver.org/)

### 社内リソース
- [CLAUDE.md](/CLAUDE.md) - Claude Code設定
- [GUIDELINES_DETAIL.md](/GUIDELINES_DETAIL.md) - 詳細運用ガイドライン
- [SAS_FLOW_SPECIFICATION.md](/SAS_FLOW_SPECIFICATION.md) - ブランチ戦略

## 🔄 更新履歴

- **2025-09-10**: 初版作成（Conventional Commits 1.0.0ベース）
- **2025-09-10**: SAS固有タイプ追加（security、hotfix など）
- **2025-09-10**: 日本語対応とプロジェクト別カスタマイズ追加

---

**注意**: このドキュメントは定期的に見直し・更新されます。最新版は常にこのファイルを参照してください。

**問い合わせ**: github@sas-com.com