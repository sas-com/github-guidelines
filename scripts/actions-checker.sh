#!/bin/bash

# GitHub Actions 自動チェックスクリプト
# エス・エー・エス株式会社
# バージョン: 1.0.0

set -e

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# アイコン定義
CHECK="✓"
CROSS="✗"
WARNING="⚠"
INFO="ℹ"

# グローバル変数
REPO_PATH=""
ISSUES_FOUND=0
WARNINGS_FOUND=0
CHECKS_PASSED=0
TOTAL_CHECKS=0

# ヘルプ表示
show_help() {
    cat << EOF
GitHub Actions チェックスクリプト

使用法:
    $0 [OPTIONS] [REPOSITORY_PATH]

オプション:
    -h, --help          このヘルプを表示
    -v, --verbose       詳細な出力を表示
    -q, --quiet         エラーのみ表示
    -f, --format FORMAT 出力形式 (text|json|junit)
    -o, --output FILE   結果をファイルに出力
    -c, --config FILE   カスタム設定ファイルを使用
    --fix               自動修正可能な問題を修正

例:
    $0 /path/to/repository
    $0 --verbose --format json --output results.json .
    $0 --fix /path/to/repo

EOF
}

# ログ関数
log_error() {
    echo -e "${RED}${CROSS}${NC} $1" >&2
    ((ISSUES_FOUND++))
    ((TOTAL_CHECKS++))
}

log_warning() {
    echo -e "${YELLOW}${WARNING}${NC} $1" >&2
    ((WARNINGS_FOUND++))
    ((TOTAL_CHECKS++))
}

log_success() {
    echo -e "${GREEN}${CHECK}${NC} $1"
    ((CHECKS_PASSED++))
    ((TOTAL_CHECKS++))
}

log_info() {
    echo -e "${BLUE}${INFO}${NC} $1"
}

# 設定チェック
check_repository_structure() {
    log_info "リポジトリ構造をチェック中..."
    
    # .github/workflows ディレクトリの存在確認
    if [ ! -d "$REPO_PATH/.github/workflows" ]; then
        log_warning ".github/workflows ディレクトリが存在しません"
    else
        log_success ".github/workflows ディレクトリが存在します"
        
        # ワークフローファイルの存在確認
        workflow_count=$(find "$REPO_PATH/.github/workflows" -name "*.yml" -o -name "*.yaml" | wc -l)
        if [ "$workflow_count" -eq 0 ]; then
            log_warning "ワークフローファイルが存在しません"
        else
            log_success "$workflow_count 個のワークフローファイルを検出"
        fi
    fi
    
    # GitHub設定ファイルの確認
    if [ ! -f "$REPO_PATH/.github/CODEOWNERS" ]; then
        log_warning "CODEOWNERS ファイルが存在しません"
    else
        log_success "CODEOWNERS ファイルが存在します"
    fi
}

# ワークフローファイルの基本チェック
check_workflow_syntax() {
    log_info "ワークフロー構文をチェック中..."
    
    if [ ! -d "$REPO_PATH/.github/workflows" ]; then
        return
    fi
    
    for workflow_file in "$REPO_PATH/.github/workflows"/*.{yml,yaml}; do
        if [ ! -f "$workflow_file" ]; then
            continue
        fi
        
        filename=$(basename "$workflow_file")
        log_info "チェック中: $filename"
        
        # YAML構文チェック (python -c を使用)
        if ! python3 -c "
import yaml
import sys
try:
    with open('$workflow_file', 'r') as f:
        yaml.safe_load(f)
except yaml.YAMLError as e:
    print('YAML syntax error:', e)
    sys.exit(1)
except FileNotFoundError:
    sys.exit(1)
" 2>/dev/null; then
            log_error "$filename: YAML構文エラーがあります"
        else
            log_success "$filename: YAML構文は正常です"
        fi
        
        # 基本的な必須フィールドチェック
        if ! grep -q "^name:" "$workflow_file"; then
            log_warning "$filename: name フィールドが指定されていません"
        fi
        
        if ! grep -q "^on:" "$workflow_file"; then
            log_error "$filename: on フィールドが指定されていません"
        fi
        
        if ! grep -q "^jobs:" "$workflow_file"; then
            log_error "$filename: jobs フィールドが指定されていません"
        fi
        
        # セキュリティチェック
        check_workflow_security "$workflow_file" "$filename"
        
        # パフォーマンスチェック
        check_workflow_performance "$workflow_file" "$filename"
    done
}

# ワークフローセキュリティチェック
check_workflow_security() {
    local workflow_file="$1"
    local filename="$2"
    
    # ハードコードされたシークレットの検出
    if grep -qE "(password|token|key|secret).*[:=].*['\"][^'\"]*['\"]" "$workflow_file"; then
        log_error "$filename: ハードコードされたシークレットの可能性があります"
    fi
    
    # 固定されていないActionバージョンの検出
    if grep -qE "uses:.*@(main|master|develop)" "$workflow_file"; then
        log_warning "$filename: Actionバージョンが固定されていません (main/master/develop使用)"
    fi
    
    # pull_request_targetの危険な使用
    if grep -q "pull_request_target:" "$workflow_file"; then
        if ! grep -q "if:.*github.event.pull_request.head.repo.full_name.*==.*github.repository" "$workflow_file"; then
            log_error "$filename: pull_request_targetの安全でない使用が検出されました"
        fi
    fi
    
    # GITHUB_TOKENの過剰な権限
    if grep -qE "permissions:.*write-all" "$workflow_file"; then
        log_error "$filename: GITHUB_TOKENに過剰な権限が付与されています"
    fi
    
    # 外部スクリプトの直接実行
    if grep -qE "run:.*curl.*\|.*bash" "$workflow_file"; then
        log_error "$filename: 外部スクリプトの直接実行は危険です"
    fi
}

# ワークフローパフォーマンスチェック
check_workflow_performance() {
    local workflow_file="$1"
    local filename="$2"
    
    # タイムアウト設定の確認
    if ! grep -q "timeout-minutes:" "$workflow_file"; then
        log_warning "$filename: タイムアウトが設定されていません"
    fi
    
    # キャッシュの使用確認
    if grep -qE "(npm|yarn|pip|maven|gradle)" "$workflow_file"; then
        if ! grep -q "actions/cache" "$workflow_file"; then
            log_warning "$filename: 依存関係キャッシュの使用を検討してください"
        fi
    fi
    
    # 不要な checkout の検出
    checkout_count=$(grep -c "actions/checkout" "$workflow_file" || true)
    if [ "$checkout_count" -gt 3 ]; then
        log_warning "$filename: checkout アクションの使用回数が多すぎる可能性があります ($checkout_count回)"
    fi
    
    # 並列実行の機会チェック
    if grep -q "strategy:" "$workflow_file" && ! grep -q "matrix:" "$workflow_file"; then
        log_info "$filename: matrix strategy の使用を検討してください"
    fi
}

# GitHub設定チェック
check_github_settings() {
    log_info "GitHub設定をチェック中..."
    
    # ローカル設定ファイルから推測可能な設定をチェック
    if [ -f "$REPO_PATH/.github/settings.yml" ]; then
        log_success "GitHub設定ファイルが存在します"
    else
        log_warning "GitHub設定ファイル (.github/settings.yml) が存在しません"
    fi
    
    # ブランチ保護設定の推測
    if [ -f "$REPO_PATH/.github/branch-protection.yml" ]; then
        log_success "ブランチ保護設定ファイルが存在します"
    else
        log_warning "ブランチ保護設定の確認をお勧めします"
    fi
}

# セキュリティ設定チェック
check_security_settings() {
    log_info "セキュリティ設定をチェック中..."
    
    # Dependabot設定
    if [ -f "$REPO_PATH/.github/dependabot.yml" ]; then
        log_success "Dependabot設定が存在します"
    else
        log_warning "Dependabot設定 (.github/dependabot.yml) の設定をお勧めします"
    fi
    
    # セキュリティポリシー
    if [ -f "$REPO_PATH/SECURITY.md" ] || [ -f "$REPO_PATH/.github/SECURITY.md" ]; then
        log_success "セキュリティポリシーが存在します"
    else
        log_warning "セキュリティポリシー (SECURITY.md) の設定をお勧めします"
    fi
    
    # .gitignore の確認
    if [ -f "$REPO_PATH/.gitignore" ]; then
        log_success ".gitignore が存在します"
        
        # 機密ファイルパターンの確認
        if grep -qE "(\.env|\.key|\.pem|\.p12|secret)" "$REPO_PATH/.gitignore"; then
            log_success "機密ファイルのパターンが .gitignore に含まれています"
        else
            log_warning "機密ファイルのパターンを .gitignore に追加することをお勧めします"
        fi
    else
        log_error ".gitignore ファイルが存在しません"
    fi
}

# ドキュメント設定チェック
check_documentation() {
    log_info "ドキュメント設定をチェック中..."
    
    # README
    if [ -f "$REPO_PATH/README.md" ]; then
        log_success "README.md が存在します"
    else
        log_warning "README.md の作成をお勧めします"
    fi
    
    # CHANGELOG
    if [ -f "$REPO_PATH/CHANGELOG.md" ] || [ -f "$REPO_PATH/HISTORY.md" ]; then
        log_success "変更履歴ファイルが存在します"
    else
        log_warning "CHANGELOG.md の作成をお勧めします"
    fi
    
    # CONTRIBUTING
    if [ -f "$REPO_PATH/CONTRIBUTING.md" ] || [ -f "$REPO_PATH/.github/CONTRIBUTING.md" ]; then
        log_success "コントリビューションガイドが存在します"
    else
        log_warning "CONTRIBUTING.md の作成をお勧めします"
    fi
}

# レポート生成
generate_report() {
    echo
    echo -e "${PURPLE}==================== チェック結果サマリー ====================${NC}"
    echo -e "${GREEN}パス:${NC}     $CHECKS_PASSED"
    echo -e "${YELLOW}警告:${NC}     $WARNINGS_FOUND"
    echo -e "${RED}エラー:${NC}   $ISSUES_FOUND"
    echo -e "${BLUE}総チェック数:${NC} $TOTAL_CHECKS"
    echo
    
    if [ "$ISSUES_FOUND" -eq 0 ]; then
        echo -e "${GREEN}${CHECK} すべてのクリティカルなチェックが通過しました！${NC}"
        exit_code=0
    else
        echo -e "${RED}${CROSS} $ISSUES_FOUND 個のクリティカルな問題が見つかりました${NC}"
        exit_code=1
    fi
    
    if [ "$WARNINGS_FOUND" -gt 0 ]; then
        echo -e "${YELLOW}${WARNING} $WARNINGS_FOUND 個の改善推奨項目があります${NC}"
    fi
    
    echo
    echo -e "${BLUE}詳細な改善ガイドについては、GITHUB_ACTIONS_CHECKLIST.md を参照してください${NC}"
    
    return $exit_code
}

# メイン実行
main() {
    # 引数解析
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--verbose)
                set -x
                shift
                ;;
            -q|--quiet)
                exec 1>/dev/null
                shift
                ;;
            *)
                REPO_PATH="$1"
                shift
                ;;
        esac
    done
    
    # デフォルトのリポジトリパス
    if [ -z "$REPO_PATH" ]; then
        REPO_PATH="."
    fi
    
    # リポジトリパスの存在確認
    if [ ! -d "$REPO_PATH" ]; then
        log_error "指定されたパスが存在しません: $REPO_PATH"
        exit 1
    fi
    
    # Gitリポジトリかチェック
    if [ ! -d "$REPO_PATH/.git" ]; then
        log_warning "指定されたパスはGitリポジトリではありません"
    fi
    
    echo -e "${BLUE}GitHub Actions チェックスクリプト v1.0.0${NC}"
    echo -e "${BLUE}対象リポジトリ: $REPO_PATH${NC}"
    echo
    
    # 各チェックの実行
    check_repository_structure
    echo
    check_workflow_syntax
    echo
    check_github_settings
    echo
    check_security_settings
    echo
    check_documentation
    echo
    
    # レポート生成
    generate_report
}

# 依存関係チェック
check_dependencies() {
    local missing_deps=()
    
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    if ! python3 -c "import yaml" 2>/dev/null; then
        missing_deps+=("python3-yaml")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo -e "${RED}不足している依存関係:${NC}"
        printf '%s\n' "${missing_deps[@]}"
        echo
        echo "Ubuntuの場合:"
        echo "  sudo apt-get update && sudo apt-get install python3 python3-yaml"
        echo
        exit 1
    fi
}

# スクリプト開始前の依存関係チェック
check_dependencies

# メイン処理実行
main "$@"