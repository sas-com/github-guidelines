# PR自動テストガイド

**エス・エー・エス株式会社**  
*包括的なPR自動テスト基盤の運用ガイド*

## 📋 概要

このドキュメントは、エス・エー・エス株式会社のPR（プルリクエスト）自動テストシステムの使用方法、設定、運用について説明します。本システムは、コード品質、セキュリティ、パフォーマンスを包括的にチェックし、効率的な開発フローをサポートします。

## 🎯 自動テストシステムの目的

### 品質保証
- コード品質の自動チェック
- テストカバレッジの継続監視  
- 回帰テストの自動実行
- パフォーマンス劣化の早期発見

### セキュリティ強化
- セキュリティ脆弱性の自動検出
- 機密情報漏洩の防止
- OWASP準拠のセキュリティチェック
- 依存関係の脆弱性スキャン

### 効率化
- 手動テストの削減
- レビュー時間の短縮
- 統一された品質基準の適用
- 継続的フィードバックの提供

## 🏗️ システム構成

### GitHub Actions ワークフロー

#### 1. メインテストパイプライン (`pr-tests.yml`)
段階的なテスト実行により効率的なフィードバックを提供：

```yaml
Stage 1: 基本品質チェック（～10分）
├── リンティング・フォーマット
├── 型チェック
├── ユニットテスト
└── 基本セキュリティスキャン

Stage 2: 統合テスト（～20分）
├── API統合テスト
├── データベーステスト
└── E2Eテスト

Stage 3: 詳細検証（～30分）
├── パフォーマンステスト
├── 互換性テスト
├── アクセシビリティテスト
└── 視覚的回帰テスト
```

#### 2. セキュリティ特化パイプライン (`pr-security.yml`)
専門的なセキュリティ検証を実行：

- **SAST（静的アプリケーションセキュリティテスト）**
- **依存関係脆弱性スキャン**
- **シークレット検出**
- **コンテナセキュリティスキャン**

#### 3. パフォーマンステスト (`pr-performance.yml`)
包括的なパフォーマンス評価：

- **Web Performance（Lighthouse）**
- **API負荷テスト（K6）**
- **バンドルサイズ分析**
- **メモリ使用量監視**

## 🚀 使用方法

### PR作成時の自動実行

1. **PRを作成する**
   ```bash
   git checkout -b feature/new-feature
   # 開発作業
   git push origin feature/new-feature
   # GitHubでPR作成
   ```

2. **自動テスト開始**
   - PR作成時に自動でテストパイプラインが開始
   - PRのタイトルに基づいてテスト戦略を自動選択
   - 変更されたファイルに基づいてテスト範囲を最適化

3. **結果の確認**
   - PR画面のChecksタブで進行状況を確認
   - 自動生成されるテストレポートコメントを確認
   - 失敗時は詳細なエラー情報を確認

### PR種別による最適化

#### Feature PR
```
feat(scope): 新機能の実装

自動実行される内容：
✅ 全テストスイート実行
✅ パフォーマンス影響評価
✅ セキュリティ影響評価
✅ E2Eテスト
```

#### Bugfix PR
```
fix(scope): バグ修正

自動実行される内容：
✅ 回帰テスト重点実行
✅ 修正対象機能の詳細テスト
✅ 影響範囲の限定的テスト
```

#### Hotfix PR
```
hotfix(scope): 緊急修正

自動実行される内容：
⚡ 緊急用最小限テストセット
⚡ 修正対象機能のピンポイントテスト
⚡ 本番影響評価テスト
```

## 🔧 設定とカスタマイズ

### 環境変数設定

#### 必須環境変数
```bash
# GitHub Secrets設定
SEMGREP_APP_TOKEN=your_semgrep_token
SNYK_TOKEN=your_snyk_token
LHCI_GITHUB_APP_TOKEN=your_lighthouse_token
```

#### オプション環境変数
```bash
# パフォーマンステスト設定
PERFORMANCE_PROFILE=comprehensive  # quick/standard/comprehensive
MONITOR_RESOURCES=true

# データベーステスト設定
TEST_DATABASE_URL=postgresql://user:pass@localhost/testdb
TEST_REDIS_URL=redis://localhost:6379/1
```

### テスト設定のカスタマイズ

#### Jest設定 (`jest.config.js`)
```javascript
// カバレッジ閾値の調整
coverageThreshold: {
  global: {
    branches: 80,    // 分岐カバレッジ
    functions: 80,   // 関数カバレッジ  
    lines: 80,       // 行カバレッジ
    statements: 80   // 文カバレッジ
  },
  // クリティカルモジュールはより高い閾値
  './src/services/': {
    branches: 90,
    functions: 90,
    lines: 90,
    statements: 90
  }
}
```

#### ESLint設定 (`.eslintrc.js`)
```javascript
// セキュリティ特化ルール
rules: {
  'security/detect-unsafe-regex': 'error',
  'security/detect-eval-with-expression': 'error',
  'no-secrets/no-secrets': ['error', {
    tolerance: 4.2,
    additionalRegexes: {
      'JWT Token': 'eyJ[A-Za-z0-9-_=]+\\.[A-Za-z0-9-_=]+\\.?[A-Za-z0-9-_.+/=]*'
    }
  }]
}
```

## 📊 テスト結果の読み方

### 自動生成されるレポート

#### 1. テスト結果サマリー
```markdown
# 🧪 PR テスト結果サマリー

## ✅ テスト結果
- 基本品質チェック: ✅ PASS
- セキュリティスキャン: ✅ PASS  
- 単体テスト: ✅ PASS
- 統合テスト: ✅ PASS
- E2Eテスト: ✅ PASS

## 📈 品質メトリクス
- テストカバレッジ: 85% (前回: 82%)
- セキュリティスコア: A+ 
- パフォーマンススコア: 95/100
```

#### 2. セキュリティレポート
```markdown
# 🔒 PRセキュリティスキャン結果

## 🛡️ セキュリティチェック結果
- GitLeaks (シークレット検出): ✅ PASS
- Semgrep (SAST): ✅ PASS
- 依存関係脆弱性: ✅ PASS

## 🚨 Critical Issues
(問題が検出された場合のみ表示)
```

### パフォーマンスメトリクス

#### Web Performance (Lighthouse)
| メトリック | 値 | 閾値 | 判定 |
|------------|-------|------|------|
| Performance Score | 95 | 80+ | ✅ PASS |
| First Contentful Paint | 1.2s | <2.0s | ✅ PASS |
| Largest Contentful Paint | 2.1s | <2.5s | ✅ PASS |
| Cumulative Layout Shift | 0.05 | <0.1 | ✅ PASS |

#### API Performance (K6)
| メトリック | 現在値 | ベースライン | 変化 |
|------------|--------|--------------|------|
| Requests/sec | 180.5 | 175.2 | +3.0% |
| Avg Response Time | 85ms | 90ms | -5.6% |
| P95 Response Time | 180ms | 195ms | -7.7% |
| Error Rate | 0.1% | <5% | ✅ PASS |

## 🔍 トラブルシューティング

### よくある問題と解決方法

#### 1. テスト失敗時の対処

**問題**: ユニットテストが失敗する
```bash
❌ Tests failed: 2 failed, 15 passed, 17 total
```

**解決手順**:
1. ローカルでテストを実行して再現確認
2. テストログを確認してエラー原因を特定  
3. 修正後にコミット・プッシュで再実行

**ローカルテスト実行**:
```bash
# 全テスト実行
npm test

# 特定のテストファイル実行
npm test -- --testPathPattern=component.test.js

# カバレッジ付きテスト
npm test -- --coverage
```

#### 2. セキュリティ問題の対処

**問題**: セキュリティスキャンで脆弱性検出
```bash
❌ High severity vulnerability detected in dependency
```

**解決手順**:
1. 検出された脆弱性の詳細を確認
2. 依存関係を安全なバージョンに更新
3. 更新が不可能な場合は代替ライブラリを検討

**依存関係更新**:
```bash
# 脆弱性のある依存関係を確認
npm audit

# 自動修正の実行
npm audit fix

# 手動での依存関係更新
npm install library@latest
```

#### 3. パフォーマンス低下の対処

**問題**: パフォーマンステストで閾値を下回る
```bash
⚠️ Performance score dropped below threshold: 75/100
```

**解決手順**:
1. Lighthouse詳細レポートを確認
2. 主要なパフォーマンス問題を特定
3. 最適化を実施

**一般的な最適化**:
```javascript
// 画像最適化
<img src="image.webp" loading="lazy" alt="description" />

// コード分割
const LazyComponent = React.lazy(() => import('./LazyComponent'));

// バンドルサイズ最適化
import { specificFunction } from 'library/specificFunction';
```

### 4. Docker環境での実行

**ローカルでの完全テスト実行**:
```bash
# 基本テスト実行
docker-compose -f docker-compose.test.yml up test-runner

# セキュリティスキャンのみ実行  
docker-compose -f docker-compose.test.yml up security-scanner

# パフォーマンステストのみ実行
docker-compose -f docker-compose.test.yml --profile performance up performance-tester

# 全サービス実行（フル環境）
docker-compose -f docker-compose.test.yml --profile advanced up
```

**コンテナ内でのデバッグ**:
```bash
# テスト用コンテナに入る
docker run -it --rm -v $(pwd):/app sas-test-runner bash

# セキュリティスキャンを手動実行
docker run -it --rm -v $(pwd):/app sas-security-scanner run-security-scan.sh
```

## 🔧 高度な設定

### CI/CDパイプラインのカスタマイズ

#### 条件付きテスト実行
```yaml
# 特定の条件下でのみテスト実行
performance-tests:
  if: |
    contains(github.event.pull_request.labels.*.name, 'performance') ||
    contains(github.event.pull_request.changed_files, 'src/performance/') ||
    github.event.pull_request.title contains 'performance'
```

#### 並列実行の最適化
```yaml
strategy:
  matrix:
    test-type: [unit, integration, security]
    node-version: [18, 20]
  fail-fast: false  # 一つ失敗しても他を継続
  max-parallel: 3   # 同時実行数制限
```

### テストデータ管理

#### フィクスチャの活用
```javascript
// tests/fixtures/userData.json
{
  "validUser": {
    "name": "Test User",
    "email": "test@example.com",
    "role": "user"
  },
  "adminUser": {
    "name": "Admin User", 
    "email": "admin@example.com",
    "role": "admin"
  }
}
```

#### 動的テストデータ生成
```javascript
import { generateTestUser } from '../utils/testHelpers';

describe('User API', () => {
  test('should create user', async () => {
    const testUser = generateTestUser({ role: 'premium' });
    const result = await createUser(testUser);
    expect(result.id).toBeDefined();
  });
});
```

### パフォーマンステストの詳細設定

#### Lighthouse設定のカスタマイズ
```javascript
// lighthouserc.js
module.exports = {
  ci: {
    collect: {
      numberOfRuns: 5,  // より安定した結果のため実行回数を増加
      url: [
        'http://localhost:3000',
        'http://localhost:3000/dashboard',
        'http://localhost:3000/profile'
      ]
    },
    assert: {
      assertions: {
        'categories:performance': ['warn', {minScore: 0.85}],
        'categories:accessibility': ['error', {minScore: 0.95}],
        'first-contentful-paint': ['warn', {maxNumericValue: 1500}],
        'largest-contentful-paint': ['warn', {maxNumericValue: 2000}]
      }
    }
  }
};
```

#### K6負荷テストのカスタマイズ
```javascript
// tests/performance/custom-load-test.js
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '1m', target: 20 },   // 20ユーザーまで段階的に増加
    { duration: '3m', target: 20 },   // 20ユーザーで3分間維持
    { duration: '1m', target: 100 },  // 100ユーザーまで急増（スパイクテスト）
    { duration: '2m', target: 100 },  // 100ユーザーで2分間維持
    { duration: '1m', target: 0 },    // 段階的に減少
  ],
  thresholds: {
    'http_req_duration': ['p(95)<500'],  // 95%のリクエストが500ms以内
    'http_req_failed': ['rate<0.02'],    // エラー率2%未満
  },
};

export default function() {
  const response = http.get('http://localhost:3001/api/health');
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
  });
}
```

## 📚 ベストプラクティス

### テスト作成のガイドライン

#### 1. テストの命名規則
```javascript
// Good: 具体的で理解しやすい
test('should return user profile when valid token is provided', () => {
  // テスト実装
});

// Bad: あいまいで理解しにくい
test('test user function', () => {
  // テスト実装  
});
```

#### 2. テストの構造化
```javascript
describe('UserService', () => {
  describe('getUserProfile', () => {
    beforeEach(() => {
      // テストごとの初期化
    });

    test('should return user profile for valid user ID', async () => {
      // Arrange
      const userId = 'user123';
      const mockUser = generateTestUser({ id: userId });
      
      // Act
      const result = await getUserProfile(userId);
      
      // Assert
      expect(result).toEqual(mockUser);
    });
  });
});
```

#### 3. セキュリティテストの統合
```javascript
import { generateXSSPayloads, testCSRFProtection } from '../utils/testHelpers';

describe('Comment API Security', () => {
  test('should prevent XSS attacks', async () => {
    const xssPayloads = generateXSSPayloads();
    
    for (const payload of xssPayloads) {
      const result = await createComment({ content: payload });
      expect(result.content).toBeSafe(); // カスタムマッチャー
    }
  });

  test('should enforce CSRF protection', async () => {
    const results = await testCSRFProtection(
      createComment,
      'valid-csrf-token',
      ['invalid-token', '', 'expired-token']
    );
    
    expect(results.every(r => r.passed)).toBe(true);
  });
});
```

### CI/CDパイプラインのベストプラクティス

#### 1. 効率的なテスト実行順序
```yaml
# 高速なテストを先に実行（Fail Fast）
jobs:
  quick-checks:     # 1-2分で完了
    - lint
    - type-check
    - unit-tests (critical paths only)
  
  standard-tests:   # 5-10分で完了
    needs: quick-checks
    - full-unit-tests
    - integration-tests
    - security-basic
  
  comprehensive:    # 15-30分で完了
    needs: standard-tests  
    - e2e-tests
    - performance-tests
    - security-deep-scan
```

#### 2. リソース使用量の最適化
```yaml
# 適切なワーカー数とメモリ制限
test-runner:
  runs-on: ubuntu-latest
  strategy:
    matrix:
      node-version: [20]
      test-shard: [1, 2, 3, 4]  # テストを4分割
  env:
    NODE_OPTIONS: --max_old_space_size=4096
    JEST_WORKERS: 2
```

#### 3. キャッシュ戦略
```yaml
- name: Cache Node Modules
  uses: actions/cache@v3
  with:
    path: ~/.npm
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-node-

- name: Cache Test Results
  uses: actions/cache@v3
  with:
    path: |
      coverage/
      test-results/
    key: test-${{ github.sha }}
    restore-keys: |
      test-${{ github.ref }}-
```

## 📞 サポート・問い合わせ

### 技術サポート
- **一般的な質問**: github@sas-com.com
- **セキュリティ関連**: security@sas-com.com  
- **パフォーマンス問題**: performance@sas-com.com
- **緊急時対応**: github@sas-com.com（件名に【緊急】を記載）

### エスカレーション手順
1. **L1 (Critical)**: システム障害・セキュリティインシデント → 即座に連絡
2. **L2 (High)**: テスト実行不可・重要機能の問題 → 4時間以内
3. **L3 (Medium)**: 設定変更・新機能要望 → 1営業日以内
4. **L4 (Low)**: 一般的な質問・改善提案 → 3営業日以内

### 関連リソース
- [PRレビューガイドライン](./PR_REVIEW_GUIDELINES.md)
- [セキュリティチェックリスト](./PR_SECURITY_CHECKLIST.md)
- [緊急時対応マニュアル](./EMERGENCY_RESPONSE.md)
- [GitHub運用ガイドライン](./GUIDELINES_DETAIL.md)

## 🔄 更新履歴

- **2025-09-10**: 初版作成
- **2025-09-10**: Docker環境設定追加
- **2025-09-10**: パフォーマンステスト設定追加

---

**© 2025 エス・エー・エス株式会社 - PR自動テストガイド**