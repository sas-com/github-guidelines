#!/bin/bash

# SAS Git Hooks Installation Script
# Installs commit message validation hooks for SAS GitHub guidelines

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
GIT_HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

echo -e "${BLUE}SAS GitHub ガイドライン - Git Hooks セットアップ${NC}"
echo -e "${BLUE}=================================================${NC}"

# Check if we're in a git repository
if [[ ! -d "$PROJECT_ROOT/.git" ]]; then
    echo -e "${RED}Error: Gitリポジトリではありません${NC}" >&2
    exit 1
fi

# Check if hooks directory exists
if [[ ! -d "$GIT_HOOKS_DIR" ]]; then
    echo -e "${RED}Error: Git hooks ディレクトリが見つかりません: $GIT_HOOKS_DIR${NC}" >&2
    exit 1
fi

# Function to install a hook
install_hook() {
    local hook_name="$1"
    local source_file="$PROJECT_ROOT/scripts/commit-hooks/$hook_name"
    local target_file="$GIT_HOOKS_DIR/$hook_name"
    local backup_file="$GIT_HOOKS_DIR/$hook_name.backup"
    
    echo -e "${YELLOW}Installing $hook_name hook...${NC}"
    
    # Check if source file exists
    if [[ ! -f "$source_file" ]]; then
        echo -e "${RED}Error: フックファイルが見つかりません: $source_file${NC}" >&2
        return 1
    fi
    
    # Backup existing hook if it exists
    if [[ -f "$target_file" ]] && [[ ! -f "$backup_file" ]]; then
        echo -e "${YELLOW}  既存のフックをバックアップ: $hook_name.backup${NC}"
        cp "$target_file" "$backup_file"
    fi
    
    # Copy and make executable
    cp "$source_file" "$target_file"
    chmod +x "$target_file"
    
    echo -e "${GREEN}  ✓ $hook_name hook installed${NC}"
}

# Install hooks
echo -e "${BLUE}Git hooks をインストール中...${NC}"

if install_hook "commit-msg" && install_hook "prepare-commit-msg"; then
    echo -e "${GREEN}✓ すべてのフックが正常にインストールされました${NC}"
else
    echo -e "${RED}❌ フックのインストールに失敗しました${NC}" >&2
    exit 1
fi

# Set git commit template
echo -e "${BLUE}Git commit template を設定中...${NC}"
if git config commit.template "$PROJECT_ROOT/.gitmessage"; then
    echo -e "${GREEN}✓ Git commit template が設定されました${NC}"
else
    echo -e "${YELLOW}⚠️  Git commit template の設定に失敗しました${NC}" >&2
fi

# Test validation script
echo -e "${BLUE}バリデーションスクリプトをテスト中...${NC}"
TEST_MSG_FILE="/tmp/test-commit-msg-$$"
echo "feat(test): テストメッセージ" > "$TEST_MSG_FILE"

if "$PROJECT_ROOT/scripts/validation/validate-commit-message.sh" "$TEST_MSG_FILE" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ バリデーションスクリプトが正常に動作しています${NC}"
    rm -f "$TEST_MSG_FILE"
else
    echo -e "${YELLOW}⚠️  バリデーションスクリプトのテストに失敗しました${NC}" >&2
    rm -f "$TEST_MSG_FILE"
fi

# Check for required tools
echo -e "${BLUE}依存関係をチェック中...${NC}"

check_command() {
    local cmd="$1"
    local description="$2"
    
    if command -v "$cmd" >/dev/null 2>&1; then
        echo -e "${GREEN}  ✓ $description${NC}"
        return 0
    else
        echo -e "${YELLOW}  ⚠️  $description が見つかりません${NC}"
        return 1
    fi
}

MISSING_TOOLS=0

if ! check_command "git" "Git"; then
    ((MISSING_TOOLS++))
fi

if ! check_command "bash" "Bash"; then
    ((MISSING_TOOLS++))
fi

# Optional tools
echo -e "${BLUE}オプションツールをチェック中...${NC}"

check_command "node" "Node.js (commitlint用)" || true
check_command "npm" "npm (パッケージ管理用)" || true

# Display next steps
echo -e "\n${BLUE}セットアップ完了！${NC}"
echo -e "${GREEN}✓ Git hooks がインストールされました${NC}"
echo -e "${GREEN}✓ コミットメッセージテンプレートが設定されました${NC}"

if [[ $MISSING_TOOLS -eq 0 ]]; then
    echo -e "${GREEN}✓ すべての必須ツールが利用可能です${NC}"
else
    echo -e "${YELLOW}⚠️  いくつかのツールが見つかりませんが、基本機能は利用できます${NC}"
fi

echo -e "\n${BLUE}次の手順:${NC}"
echo -e "1. ${YELLOW}npm install${NC} - commitlint をインストール（オプション）"
echo -e "2. ${YELLOW}git commit${NC} - 新しいコミット規約でコミットを作成"
echo -e "3. ${YELLOW}COMMIT_CONVENTION_GUIDE.md${NC} - 詳細な規約を確認"

echo -e "\n${BLUE}使用方法:${NC}"
echo -e "• コミット時に自動的にメッセージがバリデーションされます"
echo -e "• テンプレートが自動的に提供されます"
echo -e "• エラーがある場合は具体的な修正案が表示されます"

echo -e "\n${BLUE}アンインストール:${NC}"
echo -e "フックを無効にするには .git/hooks/ の該当ファイルを削除してください"

echo -e "\n${GREEN}セットアップが完了しました！🎉${NC}"