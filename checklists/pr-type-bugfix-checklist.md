# Bugfix PR チェックリスト

**エス・エー・エス株式会社**  
*バグ修正PR専用チェックリスト*

## 🐛 概要

バグ修正PRは、既存の問題を解決し、システムの安定性を向上させる重要な作業です。このチェックリストは、根本原因の特定、適切な修正、再発防止を確実にするために設計されています。

## 🔍 バグ分析チェックリスト

### 1. 問題の特定と理解
```markdown
## 問題分析
- [ ] **バグの再現**
  - [ ] 再現手順が明確に文書化されている
  - [ ] 再現率（100%、断続的、特定条件下）が記載されている
  - [ ] 影響を受ける環境（本番、ステージング、開発）が特定されている

- [ ] **影響範囲の評価**
  - [ ] 影響を受けるユーザー数/割合
  - [ ] ビジネスへの影響度（Critical/High/Medium/Low）
  - [ ] データの不整合や損失の可能性
  - [ ] セキュリティへの影響

- [ ] **根本原因分析（RCA）**
  - [ ] なぜバグが発生したか（5 Whys分析）
  - [ ] いつからバグが存在していたか
  - [ ] どのコミット/PRで導入されたか
  - [ ] なぜテストで検出されなかったか
```

### 2. 症状 vs 原因
```markdown
## 根本原因の特定
- [ ] **症状の理解**
  ```
  症状: ユーザーがログインできない
  表面的な原因: セッションタイムアウトエラー
  根本原因: Redis接続プールの枯渇
  真の原因: 接続のクローズ漏れ
  ```

- [ ] **原因の検証**
  - [ ] ログ分析による裏付け
  - [ ] デバッグによる確認
  - [ ] 再現テストでの検証
```

## 🔧 修正実装チェックリスト

### 1. 修正方針
```markdown
## 修正アプローチ
- [ ] **最小限の変更**
  - [ ] 問題を解決する最小限のコード変更
  - [ ] 不要なリファクタリングを含まない
  - [ ] 影響範囲を最小化

- [ ] **修正の妥当性**
  - [ ] 根本原因に対処している（対症療法でない）
  - [ ] 新たな問題を引き起こさない
  - [ ] パフォーマンスへの悪影響がない

- [ ] **代替案の検討**
  - [ ] 複数の修正方法を検討したか
  - [ ] 選択した方法の理由が明確か
  - [ ] トレードオフが文書化されているか
```

### 2. コード修正例
```markdown
## 修正パターン
- [ ] **Null/Undefined チェック**
  ```javascript
  // ❌ バグのあるコード
  function processUser(user) {
    return user.name.toUpperCase();  // user or user.name might be null
  }

  // ✅ 修正後
  function processUser(user) {
    if (!user || !user.name) {
      throw new Error('Invalid user object');
    }
    return user.name.toUpperCase();
  }
  ```

- [ ] **境界値処理**
  ```javascript
  // ❌ バグのあるコード
  function getArrayElement(arr, index) {
    return arr[index];  // index might be out of bounds
  }

  // ✅ 修正後
  function getArrayElement(arr, index) {
    if (index < 0 || index >= arr.length) {
      throw new RangeError(`Index ${index} out of bounds`);
    }
    return arr[index];
  }
  ```

- [ ] **リソース管理**
  ```javascript
  // ❌ バグのあるコード
  async function queryDatabase() {
    const connection = await db.connect();
    const result = await connection.query('SELECT *');
    return result;  // connection leak!
  }

  // ✅ 修正後
  async function queryDatabase() {
    const connection = await db.connect();
    try {
      const result = await connection.query('SELECT *');
      return result;
    } finally {
      await connection.close();  // ensure cleanup
    }
  }
  ```
```

## 🧪 テスト要件

### 1. バグ再現テスト
```markdown
## 再現テスト
- [ ] **失敗するテストの作成**
  ```javascript
  // まず、バグを再現する失敗するテストを作成
  describe('Bug #1234', () => {
    it('should handle null user gracefully', () => {
      // This test should fail before the fix
      expect(() => processUser(null)).toThrow('Invalid user object');
    });
  });
  ```

- [ ] **修正後のテスト成功**
  - [ ] 作成したテストが修正後に成功する
  - [ ] 既存のテストも全て成功する
  - [ ] 回帰テストが追加されている
```

### 2. 回帰テスト
```markdown
## 回帰防止
- [ ] **エッジケーステスト**
  - [ ] null/undefined の場合
  - [ ] 空配列/空文字列の場合
  - [ ] 境界値の場合
  - [ ] 異常に大きな/小さな値の場合

- [ ] **関連機能のテスト**
  - [ ] 修正箇所を使用する他の機能
  - [ ] 同様のパターンを持つコード
  - [ ] 統合テストでの確認

- [ ] **パフォーマンステスト**
  - [ ] 修正によるパフォーマンス劣化なし
  - [ ] メモリリークの確認
  - [ ] 負荷テストの実施（必要に応じて）
```

## 🛡️ 再発防止策

### 1. 予防措置
```markdown
## 再発防止
- [ ] **コード改善**
  - [ ] 同様のバグが他にないか確認
  - [ ] 共通パターンの抽出と改善
  - [ ] より堅牢なエラーハンドリング

- [ ] **開発プロセス改善**
  - [ ] コードレビューチェックリスト更新
  - [ ] 静的解析ルールの追加
  - [ ] Lintルールの強化

- [ ] **テスト強化**
  - [ ] テストカバレッジの向上
  - [ ] E2Eテストシナリオの追加
  - [ ] CI/CDパイプラインの改善
```

### 2. モニタリング強化
```markdown
## 監視・アラート
- [ ] **ログ改善**
  - [ ] エラーログの詳細化
  - [ ] デバッグ情報の追加
  - [ ] 構造化ログの実装

- [ ] **メトリクス追加**
  - [ ] エラー率の監視
  - [ ] パフォーマンスメトリクス
  - [ ] ビジネスメトリクス

- [ ] **アラート設定**
  - [ ] 閾値の設定
  - [ ] 通知先の設定
  - [ ] エスカレーションルール
```

## 📋 ドキュメント更新

### 必須ドキュメント
```markdown
## ドキュメント
- [ ] **バグレポート**
  - [ ] 問題の詳細な説明
  - [ ] 再現手順
  - [ ] 影響範囲
  - [ ] 根本原因
  - [ ] 修正内容

- [ ] **ナレッジベース**
  - [ ] トラブルシューティングガイド更新
  - [ ] FAQ更新
  - [ ] 既知の問題リスト更新

- [ ] **リリースノート**
  - [ ] 修正内容の記載
  - [ ] 影響を受ける機能
  - [ ] アップデート手順
```

## 🚦 リリース準備

### デプロイメント計画
```markdown
## リリース戦略
- [ ] **リリース優先度**
  - [ ] Critical: 即座にリリース
  - [ ] High: 24時間以内
  - [ ] Medium: 次回定期リリース
  - [ ] Low: バックログ

- [ ] **デプロイ方法**
  - [ ] ホットフィックス
  - [ ] 通常リリース
  - [ ] 段階的ロールアウト
  - [ ] カナリアリリース

- [ ] **ロールバック計画**
  - [ ] ロールバック手順の文書化
  - [ ] ロールバック判断基準
  - [ ] データ復旧手順
```

## 📊 Bugfix PR チェックリストサマリー

```yaml
bugfix_pr_checklist:
  analysis:
    - reproduction_steps: ✓
    - root_cause_identified: ✓
    - impact_assessed: ✓
  
  fix:
    - minimal_changes: ✓
    - addresses_root_cause: ✓
    - no_side_effects: ✓
  
  testing:
    - failing_test_created: ✓
    - test_passes_after_fix: ✓
    - regression_tests_added: ✓
    - existing_tests_pass: ✓
  
  prevention:
    - similar_bugs_checked: ✓
    - monitoring_improved: ✓
    - process_updated: ✓
  
  documentation:
    - bug_report_complete: ✓
    - knowledge_base_updated: ✓
    - release_notes_prepared: ✓
```

## 🎯 レビュー重点項目

### Critical（必須確認）
1. 根本原因への対処
2. テストによる修正の検証
3. 副作用の不在
4. 回帰テストの追加

### High（重要確認）
1. 影響範囲の明確化
2. パフォーマンス影響
3. エラーハンドリング
4. ログ・監視の改善

### Medium（推奨確認）
1. コード品質
2. ドキュメント更新
3. 同様のバグの調査
4. プロセス改善提案

## 📝 Bugfix PR テンプレート

```markdown
## 🐛 バグ概要
[バグの簡潔な説明]

## 🔍 問題分析
### 症状
[ユーザーが経験する問題]

### 根本原因
[技術的な原因の説明]

### 影響範囲
- 影響バージョン: 
- 影響ユーザー数: 
- 重要度: Critical/High/Medium/Low

## 🔧 修正内容
[どのように修正したかの説明]

## 🧪 テスト
### 再現手順
1. [手順1]
2. [手順2]
3. [期待される結果]

### テスト結果
- [ ] バグが再現することを確認
- [ ] 修正後、バグが解消することを確認
- [ ] 既存機能に影響がないことを確認

## 📸 Before/After
[可能であれば、修正前後のスクリーンショットや動作]

## 🛡️ 再発防止
- [ ] 同様のバグをチェック
- [ ] テストケース追加
- [ ] 監視強化

## 📚 関連情報
- Issue: #xxx
- 関連PR: #xxx
- 参考資料: [リンク]
```

---

**注意**: バグ修正は迅速性と品質のバランスが重要です。緊急度に応じて適切なレビュー深度を選択してください。