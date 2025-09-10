# PR自動テスト トラブルシューティングガイド

**エス・エー・エス株式会社**  
*PR自動テストシステムのトラブルシューティング手順書*

## 📋 概要

このドキュメントは、PR自動テストシステムで発生する可能性のある問題とその解決方法を包括的にまとめています。問題の分類、診断方法、解決手順を段階的に説明します。

## 🚨 緊急度レベル

### L1 (Critical) - 即座対応必要
- システム全体が動作不可
- セキュリティインシデント
- 本番環境への影響

### L2 (High) - 4時間以内対応
- テストパイプライン完全停止
- 重要機能のテスト失敗
- 大量のfalse positive

### L3 (Medium) - 1営業日以内対応
- 一部テストの不安定性
- パフォーマンス低下
- 設定変更が必要

### L4 (Low) - 3営業日以内対応
- 軽微な設定問題
- ドキュメント不備
- 改善提案

## 🔍 問題診断フロー

### STEP 1: 初期診断
```bash
# 基本的な状況確認
git status
git log --oneline -5
npm --version
node --version

# GitHub Actions ログ確認
# 1. GitHubのPRページを開く
# 2. "Checks" タブをクリック
# 3. 失敗したワークフローを選択
# 4. 失敗したジョブの詳細ログを確認
```

### STEP 2: ローカル環境での再現
```bash
# ローカルでのテスト実行
npm install
npm test
npm run lint
npm run type-check

# Docker環境での再現
docker-compose -f docker-compose.test.yml up test-runner
```

### STEP 3: 問題分類
- **環境問題**: 依存関係、設定、権限
- **コード問題**: テストコード、本体コード
- **インフラ問題**: GitHub Actions、外部サービス
- **データ問題**: テストデータ、フィクスチャ

## 🔧 一般的な問題と解決方法

### 1. テスト実行エラー

#### 問題: npm test が失敗する
```bash
Error: Cannot find module 'some-package'
```

**診断手順**:
```bash
# package.jsonの確認
cat package.json | grep some-package

# node_modules の確認
ls node_modules/ | grep some-package

# 依存関係の再インストール
rm -rf node_modules package-lock.json
npm install
```

**解決方法**:
```bash
# 方法1: 依存関係の追加
npm install some-package

# 方法2: devDependenciesに追加
npm install --save-dev some-package

# 方法3: バージョン指定インストール
npm install some-package@1.2.3
```

#### 問題: テスト実行時のメモリ不足
```bash
FATAL ERROR: Reached heap limit Allocation failed - JavaScript heap out of memory
```

**解決方法**:
```bash
# package.json のテストスクリプト修正
{
  "scripts": {
    "test": "NODE_OPTIONS='--max_old_space_size=4096' jest",
    "test:ci": "NODE_OPTIONS='--max_old_space_size=8192' jest --ci"
  }
}
```

#### 問題: テストタイムアウト
```bash
Timeout - Async callback was not invoked within the 5000ms timeout
```

**解決方法**:
```javascript
// テストファイル内でタイムアウト時間を延長
describe('Slow tests', () => {
  beforeEach(() => {
    jest.setTimeout(30000); // 30秒に延長
  });

  test('slow async operation', async () => {
    const result = await slowOperation();
    expect(result).toBeDefined();
  });
});

// jest.config.js での全体設定
module.exports = {
  testTimeout: 30000, // 全テストに適用
};
```

### 2. TypeScript関連エラー

#### 問題: 型チェックエラー
```typescript
Error: Property 'someMethod' does not exist on type 'SomeType'
```

**診断手順**:
```bash
# TypeScript設定確認
cat tsconfig.json

# 型定義ファイルの確認
find . -name "*.d.ts" | head -10

# TypeScript バージョン確認
npx tsc --version
```

**解決方法**:
```typescript
// 方法1: 型定義の追加
interface SomeType {
  someMethod(): void;
  existingProperty: string;
}

// 方法2: 型アサーション（一時的対処）
const typedObject = unknownObject as SomeType;

// 方法3: 型ガード
function isSomeType(obj: unknown): obj is SomeType {
  return typeof obj === 'object' && obj !== null && 'someMethod' in obj;
}
```

### 3. セキュリティスキャンエラー

#### 問題: Semgrepで誤検知
```bash
semgrep --config=auto found 15 findings
```

**診断手順**:
```bash
# Semgrep 詳細結果の確認
semgrep --config=auto --json > semgrep-results.json
cat semgrep-results.json | jq '.results[] | {message: .message, path: .path, line: .start.line}'

# 特定ルールの確認
semgrep --config=p/security-audit --json
```

**解決方法**:
```yaml
# .semgrepignore ファイルで除外設定
tests/
*.test.js
*.spec.ts
node_modules/

# 特定行での無視（コメントで追加）
const password = getPasswordFromConfig(); // nosemgrep: hardcoded-password

# semgrep.yml で無視ルール設定
rules:
  - id: ignore-test-files
    pattern: |
      const password = "test123"
    paths:
      exclude:
        - "**/*test*"
        - "**/tests/**"
```

#### 問題: GitLeaksで機密情報検出
```bash
GitLeaks found potential secrets
```

**診断手順**:
```bash
# GitLeaks詳細実行
gitleaks detect --source . --verbose

# 履歴での検索
gitleaks detect --source . --log-opts="--all"

# 特定ファイルの確認
git log -p -- path/to/file.js | grep -i "password\|secret\|key"
```

**解決方法**:
```bash
# 方法1: .gitleaksignore で除外
echo "path/to/test/file.js:1" >> .gitleaksignore

# 方法2: 履歴からの削除（注意: 履歴が変更されます）
git filter-branch --force --index-filter \
'git rm --cached --ignore-unmatch path/to/secret-file' \
--prune-empty --tag-name-filter cat -- --all

# 方法3: BFGツールによる除去
java -jar bfg.jar --delete-files secret-file.txt
```

### 4. パフォーマンステストエラー

#### 問題: Lighthouse スコアが低い
```bash
Performance score: 45/100 (threshold: 80)
```

**診断手順**:
```bash
# Lighthouse詳細レポート確認
lhci autorun --outputDir=./lighthouse-results

# Critical rendering pathの分析
cat lighthouse-results/manifest.json | jq '.[] | .jsonPath'
```

**解決方法**:
```javascript
// 画像最適化
<img 
  src="image.webp" 
  loading="lazy" 
  alt="description"
  width="300" 
  height="200"
/>

// コード分割
const LazyComponent = React.lazy(() => import('./LazyComponent'));

// フォント最適化
<link rel="preload" href="/fonts/main.woff2" as="font" type="font/woff2" crossorigin>

// リソースヒント
<link rel="dns-prefetch" href="//api.example.com">
<link rel="preconnect" href="https://fonts.googleapis.com" crossorigin>
```

#### 問題: K6負荷テストで高レスポンス時間
```bash
http_req_duration: avg=2.5s p95=5.2s (threshold: p95<500ms)
```

**診断手順**:
```bash
# K6詳細ログの確認
k6 run --out json=results.json load-test.js

# 結果分析
cat results.json | jq 'select(.type=="Point" and .metric=="http_req_duration")' | head -20
```

**解決方法**:
```javascript
// データベースクエリ最適化
const users = await User.findAll({
  attributes: ['id', 'name'], // 必要な列のみ選択
  limit: 20,
  include: [{
    model: Profile,
    attributes: ['avatar'] // JOIN時も必要な列のみ
  }]
});

// キャッシュ活用
const cachedResult = await redis.get(`user:${userId}`);
if (cachedResult) {
  return JSON.parse(cachedResult);
}
const result = await fetchUserData(userId);
await redis.setex(`user:${userId}`, 300, JSON.stringify(result)); // 5分キャッシュ

// 接続プール最適化
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20, // 最大接続数
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});
```

### 5. Docker関連エラー

#### 問題: Docker buildエラー
```bash
ERROR: failed to solve: process "/bin/sh -c npm install" did not complete successfully: exit code 1
```

**診断手順**:
```bash
# Docker build詳細ログ
docker build --progress=plain --no-cache -t test-image .

# 中間コンテナでの確認
docker run -it --rm node:20-alpine sh
npm --version
```

**解決方法**:
```dockerfile
# package.jsonとpackage-lock.jsonを先にコピー
COPY package*.json ./
RUN npm ci --only=production

# Node.jsバージョン固定
FROM node:20.5-alpine

# 権限問題の解決
RUN addgroup -g 1001 -S nodejs && adduser -S appuser -u 1001 -G nodejs
USER appuser

# Alpine Linuxでの依存関係
RUN apk add --no-cache python3 make g++
```

#### 問題: Docker Composeサービス起動エラー
```bash
ERROR: Service 'postgres' failed to build: COPY failed
```

**診断手順**:
```bash
# Docker Compose設定検証
docker-compose config

# サービス別ログ確認
docker-compose logs postgres

# 依存関係確認
docker-compose ps
```

**解決方法**:
```yaml
# docker-compose.test.yml での修正
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-testpass}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres}"]
      interval: 10s
      timeout: 5s
      retries: 5
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./tests/fixtures/sql:/docker-entrypoint-initdb.d:ro
```

## 🔄 GitHub Actions トラブルシューティング

### 1. ワークフロー実行エラー

#### 問題: Actions がキューで詰まる
```yaml
Status: Queued for 30 minutes
```

**診断手順**:
```bash
# GitHub Actionsの使用制限確認
# Settings > Billing > Actions で利用状況を確認

# 同時実行制限の確認
# .github/workflows/*.yml のconcurrency設定確認
```

**解決方法**:
```yaml
# 同時実行制御の追加
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

# リソース使用量の最適化
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [20] # バージョン数を削減
        test-shard: [1, 2] # 分割数を削減
```

#### 問題: シークレット環境変数エラー
```bash
Error: Secret SOME_TOKEN is not defined
```

**診断手順**:
```bash
# GitHub Settings > Secrets and variables > Actions で確認
# リポジトリレベルとOrganizationレベルの確認
```

**解決方法**:
```yaml
# シークレットの条件付き使用
- name: Run with token if available
  if: ${{ secrets.SOME_TOKEN != '' }}
  run: some-command --token ${{ secrets.SOME_TOKEN }}

# デフォルト値の設定
env:
  TOKEN: ${{ secrets.SOME_TOKEN || 'default-value' }}
```

### 2. 外部依存サービスエラー

#### 問題: SonarQubeサーバー接続エラー
```bash
ERROR: Error during SonarScanner execution: Unable to connect to SonarQube server
```

**解決方法**:
```yaml
# リトライ機能付きの実行
- name: SonarQube Scan with retry
  uses: nick-fields/retry@v2
  with:
    timeout_minutes: 10
    max_attempts: 3
    retry_wait_seconds: 30
    command: sonar-scanner
```

#### 問題: Semgrep APIレート制限
```bash
Error: API rate limit exceeded
```

**解決方法**:
```yaml
# レート制限対策
- name: Semgrep scan
  run: |
    sleep $((RANDOM % 60)) # 0-59秒のランダム待機
    semgrep --config=auto .
  env:
    SEMGREP_APP_TOKEN: ${{ secrets.SEMGREP_APP_TOKEN }}
```

## 📊 監視とアラート

### パフォーマンス監視

#### 実行時間の監視
```bash
# 実行時間が30分を超えた場合のアラート設定
# GitHub Actions の timeout-minutes 設定
timeout-minutes: 30
```

#### リソース使用量監視
```yaml
# メモリ使用量監視
- name: Monitor memory usage
  run: |
    free -h
    df -h
    ps aux --sort=-%mem | head -10
```

### 成功率監視
```bash
# 過去30日のテスト成功率を算出するスクリプト
gh api graphql -f query='
query($owner: String!, $repo: String!) {
  repository(owner: $owner, name: $repo) {
    pullRequests(last: 100, states: CLOSED) {
      nodes {
        commits(last: 1) {
          nodes {
            commit {
              checkSuites(last: 10) {
                nodes {
                  conclusion
                }
              }
            }
          }
        }
      }
    }
  }
}' -f owner=sas-com -f repo=github-guidelines
```

## 🚑 緊急時対応手順

### システム全体停止時
1. **ステータス確認** (5分以内)
   - GitHub Status (https://www.githubstatus.com/) 確認
   - 社内システム状況確認
   - 他チーム・プロジェクトの状況確認

2. **影響範囲特定** (10分以内)
   - 影響を受けるPR・プロジェクトの特定
   - ステークホルダーへの初期報告
   - 緊急度レベルの判定

3. **一時的回避策** (30分以内)
   - 手動テストへの切り替え
   - クリティカルなPRの個別対応
   - ローカル環境での検証強化

4. **根本解決** (状況に応じて)
   - 原因調査と対策実施
   - 再発防止策の検討
   - システム復旧の確認

### セキュリティインシデント時
1. **即座実行項目**
   ```bash
   # 影響を受ける可能性のあるシークレットを無効化
   # GitHub Settings > Developer settings > Personal access tokens
   
   # 問題のあるコミットの特定と隔離
   git log --grep="password\|secret\|key" --oneline
   
   # 緊急連絡
   # security@sas-com.com に即座連絡
   ```

2. **調査・対応**
   - インシデント範囲の特定
   - 影響を受けるシステム・データの確認  
   - 必要に応じて外部専門家への相談

## 📋 よくある質問 (FAQ)

### Q1: テストが突然失敗するようになりました
**A**: 以下の順序で確認してください：
1. 最新のコミットで何が変更されたかを確認
2. 依存関係の更新があったかを確認
3. 外部サービス（GitHub, npm など）のステータス確認
4. ローカル環境での再現確認

### Q2: セキュリティスキャンで大量のfalse positiveが出ます
**A**: 以下の対策を実施してください：
1. `.semgrepignore` や `.gitleaksignore` の設定
2. テストファイルやモックデータの除外設定
3. カスタムルールの作成
4. しきい値の調整

### Q3: パフォーマンステストが不安定です
**A**: 以下を確認してください：
1. テスト実行環境のリソース状況
2. 外部APIの応答時間変動
3. テストデータの一貫性
4. 並列実行による影響

### Q4: Dockerビルドが遅いです
**A**: 以下の最適化を実施してください：
1. .dockerignore の設定
2. マルチステージビルドの活用
3. レイヤーキャッシュの最適化
4. 基本イメージの見直し

### Q5: GitHub Actions の実行時間が長すぎます
**A**: 以下の最適化手法を試してください：
1. テストの並列実行
2. キャッシュの活用
3. 条件付きジョブ実行
4. 不要なステップの削除

## 📞 サポート連絡先

### 技術サポート
- **一般的な問題**: github@sas-com.com
- **セキュリティ問題**: security@sas-com.com
- **パフォーマンス問題**: performance@sas-com.com
- **インフラ問題**: infrastructure@sas-com.com

### 緊急時連絡
- **24時間対応**: emergency@sas-com.com
- **電話**: 03-XXXX-XXXX (営業時間内)

### エスカレーション
1. **開発チーム内**: 同僚・チームリード
2. **部門内**: 技術マネージャー
3. **社内**: CTO・技術部門長
4. **社外**: 外部技術コンサルタント

## 🔄 継続的改善

### トラブル報告書テンプレート
```markdown
# インシデント報告書

## 基本情報
- **発生日時**: 2025-XX-XX XX:XX
- **影響範囲**: 特定PR / 全プロジェクト
- **緊急度**: L1/L2/L3/L4
- **報告者**: 名前

## 問題概要
- **症状**: 
- **影響**: 
- **検出方法**: 

## 根本原因
- **原因**: 
- **なぜ発生したか**: 

## 対応内容
- **一時対応**: 
- **根本対策**: 
- **再発防止策**: 

## 学んだこと
- **改善点**: 
- **予防策**: 
```

### 改善提案プロセス
1. **問題パターンの分析**: 月次レビューで傾向確認
2. **改善案の作成**: チームでのブレインストーミング
3. **実装・検証**: テスト環境での確認
4. **本格導入**: 段階的ロールアウト
5. **効果測定**: メトリクス分析

---

**© 2025 エス・エー・エス株式会社 - PR自動テスト トラブルシューティングガイド**