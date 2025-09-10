#!/bin/bash

# SAS Commit Message Validation Test Suite
# Tests various commit message patterns to ensure validator works correctly

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALIDATOR="$SCRIPT_DIR/validate-commit-message.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Test function
run_test() {
    local test_name="$1"
    local commit_message="$2"
    local expected_result="$3"  # "pass" or "fail"
    
    ((TOTAL_TESTS++))
    
    echo -e "${BLUE}Test $TOTAL_TESTS: $test_name${NC}"
    
    # Create temp file with commit message
    local temp_file="/tmp/test-commit-$$-$TOTAL_TESTS"
    echo "$commit_message" > "$temp_file"
    
    # Run validator
    local result="pass"
    if ! "$VALIDATOR" "$temp_file" >/dev/null 2>&1; then
        result="fail"
    fi
    
    # Check result
    if [[ "$result" == "$expected_result" ]]; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED_TESTS++))
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo -e "${YELLOW}Expected: $expected_result, Got: $result${NC}"
        echo -e "${YELLOW}Message: $commit_message${NC}"
        ((FAILED_TESTS++))
    fi
    
    rm -f "$temp_file"
    echo
}

echo -e "${BLUE}SAS コミットメッセージバリデーションテストスイート${NC}"
echo -e "${BLUE}=================================================${NC}"
echo

# Valid commit messages (should pass)
echo -e "${BLUE}=== 有効なコミットメッセージのテスト ===${NC}"

run_test "基本的なfeatコミット" \
    "feat(auth): OAuth2.0ログイン機能を追加" \
    "pass"

run_test "基本的なfixコミット" \
    "fix(api): ユーザー検索時のエラーハンドリングを修正" \
    "pass"

run_test "スコープなしのdocsコミット" \
    "docs: README.mdにセットアップ手順を追加" \
    "pass"

run_test "複数行のコミット（本文付き）" \
    "feat(payment): クレジットカード決済機能を追加

Stripe APIを使用した決済処理を実装
- カード情報の暗号化
- 決済履歴の保存
- エラーハンドリング強化

Closes #123" \
    "pass"

run_test "破壊的変更のコミット" \
    "feat(api)!: ユーザーAPI v2.0を導入

BREAKING CHANGE: レスポンス形式を変更
- userInfo → profile に名称変更
- 新フィールド: profile.lastLoginAt 追加" \
    "pass"

run_test "セキュリティ修正コミット" \
    "security(auth): パスワードハッシュ化アルゴリズムを強化

MD5からbcryptに変更してセキュリティを向上
既存パスワードの段階的マイグレーションも実装

Security-review: security@sas-com.com" \
    "pass"

run_test "緊急修正コミット" \
    "hotfix(api): 本番環境でのメモリリーク問題を緊急修正

本番環境で発生したメモリリークを修正
影響範囲: 全ユーザー
修正内容: 不要なオブジェクト参照を削除" \
    "pass"

# Invalid commit messages (should fail)
echo -e "${BLUE}=== 無効なコミットメッセージのテスト ===${NC}"

run_test "タイプなし" \
    "OAuth2.0ログイン機能を追加" \
    "fail"

run_test "無効なタイプ" \
    "update(auth): ログイン機能を更新" \
    "fail"

run_test "説明なし" \
    "feat(auth):" \
    "fail"

run_test "説明が短すぎる" \
    "feat: 追加" \
    "fail"

run_test "説明が長すぎる" \
    "feat(auth): OAuth2.0を使用したソーシャルログイン機能を追加し、Google、Facebook、Twitter、GitHubのアカウントでログインできるようになりました" \
    "fail"

run_test "大文字で始まる説明" \
    "feat(auth): OAuth2.0ログイン機能を追加" \
    "pass"  # 実際は日本語なのでpass

run_test "ピリオドで終わる説明" \
    "feat(auth): OAuth2.0ログイン機能を追加." \
    "fail"

run_test "丁寧語の使用" \
    "feat(auth): OAuth2.0ログイン機能を追加しました" \
    "fail"

run_test "です調の使用" \
    "feat(auth): OAuth2.0ログイン機能です" \
    "fail"

run_test "無効なスコープ文字" \
    "feat(Auth_Login): OAuth2.0ログイン機能を追加" \
    "fail"

run_test "本文の行が長すぎる" \
    "feat(auth): OAuth2.0ログイン機能を追加

この機能により、ユーザーはGoogle、Facebook、Twitter、GitHubアカウントを使用してログインできるようになり、従来のパスワード認証よりも安全で便利な認証方式を提供することができるようになりました。" \
    "fail"

run_test "件名の後に空行がない" \
    "feat(auth): OAuth2.0ログイン機能を追加
本文がすぐに続いている" \
    "fail"

# Security tests (should fail)
echo -e "${BLUE}=== セキュリティチェックのテスト ===${NC}"

run_test "パスワード含有" \
    "feat(auth): ログイン機能を追加

password=secretpassword123 を設定" \
    "fail"

run_test "APIキー含有" \
    "feat(api): API機能を追加

api_key=abc123def456ghi789 でテスト実行" \
    "fail"

run_test "トークン含有" \
    "feat(auth): 認証機能を追加

Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9 を使用" \
    "fail"

run_test "データベースURL含有" \
    "feat(db): データベース接続を追加

mysql://user:password@localhost/db を使用" \
    "fail"

run_test "Stripeシークレットキー含有" \
    "feat(payment): 決済機能を追加

sk_test_abc123def456 でテスト実行" \
    "fail"

# Edge cases
echo -e "${BLUE}=== エッジケースのテスト ===${NC}"

run_test "空のコミットメッセージ" \
    "" \
    "fail"

run_test "スペースのみ" \
    "   " \
    "fail"

run_test "改行のみ" \
    "
    
    " \
    "fail"

run_test "コメント行のみ" \
    "# コメント行
# 別のコメント行" \
    "fail"

run_test "有効なコミット＋コメント行" \
    "feat(auth): OAuth2.0ログイン機能を追加

# コメント行
# 別のコメント行" \
    "pass"

# Co-authored-by tests (should pass)
echo -e "${BLUE}=== Co-authored-by テスト ===${NC}"

run_test "Co-authored-byがあるメール" \
    "feat(auth): OAuth2.0ログイン機能を追加

Co-authored-by: tanaka@sas-com.com" \
    "pass"

# Japanese specific tests
echo -e "${BLUE}=== 日本語固有のテスト ===${NC}"

run_test "ひらがな・カタカナ混在" \
    "feat(ui): ユーザーインターフェースをリニューアル" \
    "pass"

run_test "英日混在" \
    "feat(api): REST APIエンドポイントを追加" \
    "pass"

run_test "する で終わる（命令形ではない）" \
    "feat(auth): ログイン機能を実装する" \
    "fail"

run_test "適切な命令形" \
    "feat(auth): ログイン機能を実装" \
    "pass"

# Type-specific validation tests
echo -e "${BLUE}=== タイプ固有バリデーションテスト ===${NC}"

run_test "featなのに修正という説明" \
    "feat(auth): ログインバグを修正" \
    "pass"  # 警告だが通す

run_test "fixなのに追加という説明" \
    "fix(auth): 新機能を追加" \
    "pass"  # 警告だが通す

run_test "docsタイプでドキュメント以外" \
    "docs(auth): ログイン機能を追加" \
    "pass"  # 警告だが通す

run_test "securityタイプで詳細説明あり" \
    "security(auth): SQLインジェクション脆弱性を修正

CVE-2023-12345の対応
影響範囲: 全ユーザー
修正内容: パラメータの適切なエスケープ処理

Security-review: security@sas-com.com" \
    "pass"

run_test "hotfixタイプで緊急性説明あり" \
    "hotfix(api): 本番環境の緊急メモリリーク修正

Critical: 本番環境でメモリリークが発生
影響: 全ユーザーの応答速度低下
修正: 不要なオブジェクト参照を削除" \
    "pass"

# Display results
echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}テスト結果サマリー${NC}"
echo -e "${GREEN}合格: $PASSED_TESTS/$TOTAL_TESTS${NC}"
echo -e "${RED}不合格: $FAILED_TESTS/$TOTAL_TESTS${NC}"

if [[ $FAILED_TESTS -eq 0 ]]; then
    echo -e "${GREEN}✓ すべてのテストが合格しました！${NC}"
    exit 0
else
    echo -e "${RED}✗ $FAILED_TESTS 個のテストが失敗しました${NC}"
    exit 1
fi