#!/bin/bash

# SAS Comprehensive Commit Message Validator
# Validates commit messages against Conventional Commits with SAS-specific rules
# Features: Type validation, scope checking, security scanning, and intelligent suggestions

set -e

COMMIT_MSG_FILE="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
MAX_SUBJECT_LENGTH=72
MAX_BODY_LINE_LENGTH=100
MIN_SUBJECT_LENGTH=10

# Valid types (SAS-specific)
VALID_TYPES=(
    "feat"      # 新機能の追加
    "fix"       # バグ修正
    "docs"      # ドキュメント変更のみ
    "style"     # フォーマット変更（動作に影響なし）
    "refactor"  # リファクタリング
    "test"      # テストの追加・修正
    "chore"     # ビルドプロセス・補助ツールの変更
    "security"  # セキュリティ関連の修正
    "perf"      # パフォーマンス改善
    "build"     # ビルドシステム変更
    "ci"        # CI設定変更
    "revert"    # コミットの取り消し
    "hotfix"    # 緊急修正
)

# Recommended scopes
RECOMMENDED_SCOPES=(
    "auth" "api" "ui" "db" "payment" "notification"
    "user" "product" "order" "admin" "config"
    "header" "sidebar" "modal" "form" "table"
    "webpack" "eslint" "jest" "docker" "k8s"
    "dev" "staging" "prod" "test"
    "readme" "docs" "changelog" "setup"
)

# Sensitive information patterns
SENSITIVE_PATTERNS=(
    "password\s*[:=]\s*[\"']?[^\"'\s]+"
    "api[_-]?key\s*[:=]\s*[\"']?[^\"'\s]+"
    "secret\s*[:=]\s*[\"']?[^\"'\s]+"
    "token\s*[:=]\s*[\"']?[^\"'\s]+"
    "private[_-]?key"
    "access[_-]?token"
    "auth[_-]?token"
    "bearer\s+[a-zA-Z0-9\.\-_]+"
    "mysql://.*:[^@]+@"
    "postgresql://.*:[^@]+@"
    "mongodb://.*:[^@]+@"
    "[a-zA-Z0-9]{20,}"  # Long alphanumeric strings (potential tokens)
    "pk_[a-zA-Z0-9]+"   # Stripe public keys
    "sk_[a-zA-Z0-9]+"   # Stripe secret keys
)

# Japanese forbidden ending patterns (should not end with polite forms)
JP_FORBIDDEN_ENDINGS=(
    "ました"
    "です"
    "である"
    "した"
    "する"
    "。"
)

# Error tracking
ERRORS=()
WARNINGS=()
SUGGESTIONS=()

# Functions
log_error() {
    ERRORS+=("$1")
    echo -e "${RED}❌ Error: $1${NC}" >&2
}

log_warning() {
    WARNINGS+=("$1")
    echo -e "${YELLOW}⚠️  Warning: $1${NC}" >&2
}

log_suggestion() {
    SUGGESTIONS+=("$1")
    echo -e "${CYAN}💡 Suggestion: $1${NC}" >&2
}

# Read commit message
if [[ ! -f "$COMMIT_MSG_FILE" ]]; then
    log_error "コミットメッセージファイルが見つかりません: $COMMIT_MSG_FILE"
    exit 1
fi

COMMIT_MSG=$(cat "$COMMIT_MSG_FILE")

# Remove comment lines and empty lines for validation
CLEAN_MSG=$(echo "$COMMIT_MSG" | sed '/^#/d' | sed '/^$/d')

if [[ -z "$CLEAN_MSG" ]]; then
    log_error "コミットメッセージが空です"
    exit 1
fi

# Split message into lines
mapfile -t LINES <<< "$CLEAN_MSG"
SUBJECT_LINE="${LINES[0]}"

echo -e "${BLUE}コミットメッセージを検証中...${NC}"
echo -e "${CYAN}Subject: $SUBJECT_LINE${NC}"

# 1. Basic format validation - Conventional Commits pattern
if ! echo "$SUBJECT_LINE" | grep -qE '^[a-z]+(\([^)]+\))?!?: .+'; then
    log_error "基本フォーマットが正しくありません"
    log_suggestion "正しい形式: <type>[optional scope]: <description>"
    log_suggestion "例: feat(auth): OAuth2.0ログイン機能を追加"
fi

# Extract components
TYPE=""
SCOPE=""
BREAKING=""
DESCRIPTION=""

if echo "$SUBJECT_LINE" | grep -qE '^([a-z]+)(\([^)]+\))?(!)?: (.+)'; then
    TYPE=$(echo "$SUBJECT_LINE" | sed -E 's/^([a-z]+)(\([^)]+\))?(!)?: (.+)/\1/')
    SCOPE=$(echo "$SUBJECT_LINE" | sed -E 's/^([a-z]+)\(([^)]+)\)(!)?: (.+)/\2/' | sed 's/^[a-z]+$//')
    BREAKING=$(echo "$SUBJECT_LINE" | grep -o '!' || true)
    DESCRIPTION=$(echo "$SUBJECT_LINE" | sed -E 's/^([a-z]+)(\([^)]+\))?(!)?: (.+)/\4/')
fi

# 2. Type validation
if [[ -n "$TYPE" ]]; then
    TYPE_VALID=false
    for valid_type in "${VALID_TYPES[@]}"; do
        if [[ "$TYPE" == "$valid_type" ]]; then
            TYPE_VALID=true
            break
        fi
    done
    
    if [[ "$TYPE_VALID" == false ]]; then
        log_error "無効なタイプ: '$TYPE'"
        log_suggestion "有効なタイプ: ${VALID_TYPES[*]}"
        
        # Suggest similar types
        case "$TYPE" in
            "update"|"modify"|"change") log_suggestion "代わりに 'fix' または 'feat' を使用してください" ;;
            "add") log_suggestion "代わりに 'feat' を使用してください" ;;
            "remove"|"delete") log_suggestion "代わりに 'feat' または 'refactor' を使用してください" ;;
            "bug"|"bugfix") log_suggestion "代わりに 'fix' を使用してください" ;;
            "feature") log_suggestion "代わりに 'feat' を使用してください" ;;
            "documentation") log_suggestion "代わりに 'docs' を使用してください" ;;
        esac
    fi
else
    log_error "タイプが指定されていません"
fi

# 3. Scope validation
if [[ -n "$SCOPE" ]]; then
    # Check if scope follows naming convention (lowercase, alphanumeric, dash, underscore)
    if ! echo "$SCOPE" | grep -qE '^[a-z0-9_-]+$'; then
        log_warning "スコープは小文字の英数字、ハイフン、アンダースコアのみ使用してください: '$SCOPE'"
    fi
    
    # Check against recommended scopes
    SCOPE_RECOMMENDED=false
    for rec_scope in "${RECOMMENDED_SCOPES[@]}"; do
        if [[ "$SCOPE" == "$rec_scope" ]]; then
            SCOPE_RECOMMENDED=true
            break
        fi
    done
    
    if [[ "$SCOPE_RECOMMENDED" == false ]]; then
        log_suggestion "推奨スコープではありません: '$SCOPE'"
        log_suggestion "推奨スコープ例: auth, api, ui, db, docs"
    fi
fi

# 4. Description validation
if [[ -n "$DESCRIPTION" ]]; then
    DESC_LENGTH=${#DESCRIPTION}
    
    # Length check
    if [[ $DESC_LENGTH -gt $MAX_SUBJECT_LENGTH ]]; then
        log_error "説明が長すぎます: $DESC_LENGTH文字 (最大: $MAX_SUBJECT_LENGTH文字)"
        log_suggestion "詳細な説明は本文に記載してください"
    fi
    
    if [[ $DESC_LENGTH -lt $MIN_SUBJECT_LENGTH ]]; then
        log_warning "説明が短すぎます: $DESC_LENGTH文字 (推奨最小: $MIN_SUBJECT_LENGTH文字)"
    fi
    
    # Check first character (should be lowercase for English, any for Japanese)
    FIRST_CHAR=$(echo "$DESCRIPTION" | cut -c1)
    if echo "$FIRST_CHAR" | grep -qE '[A-Z]'; then
        log_warning "説明は小文字で始めてください: '$FIRST_CHAR'"
    fi
    
    # Check ending (should not end with period)
    if echo "$DESCRIPTION" | grep -qE '\.$'; then
        log_warning "説明の末尾にピリオドは不要です"
    fi
    
    # Check for Japanese polite forms
    for ending in "${JP_FORBIDDEN_ENDINGS[@]}"; do
        if echo "$DESCRIPTION" | grep -qE "${ending}$"; then
            log_warning "命令形で記述してください（「${ending}」で終わらないようにしてください）"
            
            # Provide suggestions
            case "$ending" in
                "ました"|"した") log_suggestion "例: '〜を追加しました' → '〜を追加'" ;;
                "です") log_suggestion "例: '〜です' → '〜'" ;;
                "する") log_suggestion "例: '〜する' → '〜'" ;;
            esac
            break
        fi
    done
    
    # Check for common mistakes
    if echo "$DESCRIPTION" | grep -qiE '^(update|modify|change|fix)\b'; then
        log_suggestion "より具体的な説明を使用してください"
        log_suggestion "例: 'update API' → 'ユーザー作成APIのレスポンス形式を更新'"
    fi
    
    # Check for vague descriptions
    if echo "$DESCRIPTION" | grep -qiE '^(機能|バグ|問題|エラー)\b'; then
        log_suggestion "より具体的な説明を使用してください"
        log_suggestion "例: '機能追加' → 'OAuth2.0ログイン機能を追加'"
    fi
else
    log_error "説明が指定されていません"
fi

# 5. Body validation (if present)
if [[ ${#LINES[@]} -gt 1 ]]; then
    # Check for blank line after subject
    if [[ ${#LINES[@]} -gt 1 ]] && [[ -n "${LINES[1]}" ]]; then
        log_error "件名の後に空行が必要です"
    fi
    
    # Check body line lengths
    for i in $(seq 2 $((${#LINES[@]} - 1))); do
        if [[ ${#LINES[$i]} -gt $MAX_BODY_LINE_LENGTH ]]; then
            log_warning "本文の行が長すぎます (行 $((i + 1))): ${#LINES[$i]}文字 (最大: $MAX_BODY_LINE_LENGTH文字)"
        fi
    done
fi

# 6. Security checks - scan for sensitive information
for pattern in "${SENSITIVE_PATTERNS[@]}"; do
    if echo "$COMMIT_MSG" | grep -qiE "$pattern"; then
        log_error "機密情報の可能性がある内容が検出されました"
        log_suggestion "パスワード、APIキー、トークンなどの機密情報は含めないでください"
        break
    fi
done

# Check for email addresses (potential PII)
if echo "$COMMIT_MSG" | grep -qE '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' && \
   ! echo "$COMMIT_MSG" | grep -qE 'Co-authored-by:|Reviewed-by:|Tested-by:'; then
    log_warning "メールアドレスが含まれています（個人情報の可能性）"
    log_suggestion "必要でない限りメールアドレスの記載は避けてください"
fi

# 7. Breaking changes validation
if [[ -n "$BREAKING" ]] || echo "$COMMIT_MSG" | grep -qE '^BREAKING CHANGE:'; then
    if ! echo "$COMMIT_MSG" | grep -qE '^BREAKING CHANGE:'; then
        log_warning "破壊的変更の詳細説明がありません"
        log_suggestion "フッターに 'BREAKING CHANGE: 説明' を追加してください"
    fi
fi

# 8. Footer validation
if echo "$COMMIT_MSG" | grep -qE 'Closes|Fixes|Resolves|Refs'; then
    # Validate issue reference format
    if ! echo "$COMMIT_MSG" | grep -qE '(Closes|Fixes|Resolves|Refs) #[0-9]+'; then
        log_warning "Issue参照の形式が正しくない可能性があります"
        log_suggestion "正しい形式: 'Closes #123' または 'Fixes #456'"
    fi
fi

# 9. Type-specific validations
case "$TYPE" in
    "feat")
        if echo "$DESCRIPTION" | grep -qiE '修正|fix|bug'; then
            log_suggestion "新機能ではなくバグ修正の場合は 'fix' を使用してください"
        fi
        ;;
    "fix")
        if echo "$DESCRIPTION" | grep -qiE '追加|add|新|new'; then
            log_suggestion "バグ修正ではなく新機能の場合は 'feat' を使用してください"
        fi
        ;;
    "docs")
        if ! echo "$DESCRIPTION" | grep -qiE 'ドキュメント|doc|readme|guide|説明'; then
            log_suggestion "ドキュメント変更であることが分からない説明です"
        fi
        ;;
    "security")
        if ! echo "$COMMIT_MSG" | grep -qE 'Security-review:|CVE-|脆弱性|vulnerability|セキュリティ'; then
            log_suggestion "セキュリティ修正の詳細や影響について説明を追加することを検討してください"
        fi
        ;;
    "hotfix")
        if ! echo "$COMMIT_MSG" | grep -qE '緊急|urgent|critical|本番|production'; then
            log_suggestion "緊急修正の理由と影響を説明してください"
        fi
        ;;
esac

# 10. Generate improvement suggestions
if [[ ${#ERRORS[@]} -gt 0 ]] || [[ ${#WARNINGS[@]} -gt 0 ]]; then
    echo -e "\n${YELLOW}=== 改善案 ===${NC}"
    
    # Generate improved version
    if [[ -n "$TYPE" ]] && [[ -n "$DESCRIPTION" ]]; then
        IMPROVED_TYPE="$TYPE"
        IMPROVED_SCOPE="$SCOPE"
        IMPROVED_DESC="$DESCRIPTION"
        
        # Fix common issues
        IMPROVED_DESC=$(echo "$IMPROVED_DESC" | sed -E 's/ました$//')
        IMPROVED_DESC=$(echo "$IMPROVED_DESC" | sed -E 's/です$//')
        IMPROVED_DESC=$(echo "$IMPROVED_DESC" | sed -E 's/した$//') 
        IMPROVED_DESC=$(echo "$IMPROVED_DESC" | sed -E 's/する$//')
        IMPROVED_DESC=$(echo "$IMPROVED_DESC" | sed -E 's/\.$$//')
        
        # Capitalize first letter if needed
        IMPROVED_DESC="$(echo "${IMPROVED_DESC:0:1}" | tr '[:upper:]' '[:lower:]')${IMPROVED_DESC:1}"
        
        if [[ -n "$IMPROVED_SCOPE" ]]; then
            echo -e "${GREEN}改善例: ${IMPROVED_TYPE}(${IMPROVED_SCOPE}): ${IMPROVED_DESC}${NC}"
        else
            echo -e "${GREEN}改善例: ${IMPROVED_TYPE}: ${IMPROVED_DESC}${NC}"
        fi
    fi
    
    # Show examples for the current type
    case "$TYPE" in
        "feat")
            echo -e "${CYAN}feat例: feat(auth): OAuth2.0ログイン機能を追加${NC}"
            echo -e "${CYAN}feat例: feat(api): ユーザー検索エンドポイントを追加${NC}"
            ;;
        "fix")
            echo -e "${CYAN}fix例: fix(auth): セッション期限切れ時の無限リダイレクトを修正${NC}"
            echo -e "${CYAN}fix例: fix(ui): モバイル画面でのレイアウト崩れを修正${NC}"
            ;;
        "docs")
            echo -e "${CYAN}docs例: docs(readme): セットアップ手順を更新${NC}"
            echo -e "${CYAN}docs例: docs(api): エンドポイント仕様書を追加${NC}"
            ;;
    esac
fi

# Summary
echo -e "\n${BLUE}=== 検証結果 ===${NC}"
echo -e "${RED}Errors: ${#ERRORS[@]}${NC}"
echo -e "${YELLOW}Warnings: ${#WARNINGS[@]}${NC}"
echo -e "${CYAN}Suggestions: ${#SUGGESTIONS[@]}${NC}"

# Exit with error if there are any errors
if [[ ${#ERRORS[@]} -gt 0 ]]; then
    echo -e "\n${RED}コミットメッセージの修正が必要です${NC}"
    exit 1
fi

if [[ ${#WARNINGS[@]} -gt 0 ]]; then
    echo -e "\n${YELLOW}警告がありますが、コミットは可能です${NC}"
fi

if [[ ${#ERRORS[@]} -eq 0 ]] && [[ ${#WARNINGS[@]} -eq 0 ]]; then
    echo -e "\n${GREEN}✓ コミットメッセージは規約に適合しています${NC}"
fi

exit 0