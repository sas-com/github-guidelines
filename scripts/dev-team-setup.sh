#!/bin/bash
# Development Team Environment Setup Script
# エス・エー・エス株式会社 - 開発チーム用環境構築スクリプト

set -e

echo "==================================="
echo "Development Team Environment Setup"
echo "==================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on WSL
if grep -qi microsoft /proc/version; then
    echo -e "${GREEN}✓ WSL environment detected${NC}"
else
    echo -e "${YELLOW}⚠ Not running on WSL. Some features may not work as expected.${NC}"
fi

# Function to check command existence
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install if missing
install_if_missing() {
    if ! command_exists "$1"; then
        echo -e "${YELLOW}Installing $1...${NC}"
        $2
    else
        echo -e "${GREEN}✓ $1 is already installed${NC}"
    fi
}

echo ""
echo "📦 Installing Development Tools..."
echo "================================="

# Git configuration
echo "Configuring Git..."
git config --global pull.rebase false
git config --global init.defaultBranch main
git config --global core.autocrlf input

# Create git message template
cat > ~/.gitmessage << 'EOF'
# <type>(<scope>): <subject>
# 
# <body>
# 
# <footer>
# 
# Type:
#   feat: 新機能
#   fix: バグ修正
#   docs: ドキュメント
#   style: フォーマット変更
#   refactor: リファクタリング
#   test: テスト追加・修正
#   chore: ビルドプロセスやツールの変更
EOF

git config --global commit.template ~/.gitmessage

# Install Node.js (via nvm)
if ! command_exists nvm; then
    echo "Installing NVM..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    nvm install --lts
    nvm use --lts
fi

# Install development tools
npm install -g \
    eslint \
    prettier \
    typescript \
    @commitlint/cli \
    @commitlint/config-conventional \
    husky \
    lint-staged

# Install Python tools
if command_exists python3; then
    pip3 install --user \
        black \
        flake8 \
        mypy \
        pytest \
        pre-commit
fi

# Setup VS Code settings
echo ""
echo "⚙️  Setting up VS Code configurations..."
echo "======================================="

mkdir -p ~/.config/Code/User
cat > ~/.config/Code/User/settings.json << 'EOF'
{
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.fixAll.eslint": true
    },
    "editor.rulers": [80, 120],
    "editor.tabSize": 2,
    "files.trimTrailingWhitespace": true,
    "files.insertFinalNewline": true,
    "git.enableSmartCommit": true,
    "git.confirmSync": false,
    "terminal.integrated.defaultProfile.linux": "bash",
    "typescript.updateImportsOnFileMove.enabled": "always",
    "eslint.validate": [
        "javascript",
        "javascriptreact",
        "typescript",
        "typescriptreact"
    ],
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black"
}
EOF

# Create useful aliases
echo ""
echo "🔧 Creating useful aliases..."
echo "============================="

cat >> ~/.bashrc << 'EOF'

# GitHub Development Aliases
alias gs='git status -sb'
alias gco='git checkout'
alias gcm='git commit -m'
alias gpl='git pull origin'
alias gps='git push origin'
alias gdev='git checkout dev && git pull origin dev'
alias gfeat='git checkout -b feature/'
alias gbug='git checkout -b bugfix/'
alias ghot='git checkout -b hotfix/'

# Docker aliases
alias dc='docker-compose'
alias dcu='docker-compose up -d'
alias dcd='docker-compose down'
alias dcl='docker-compose logs -f'

# NPM aliases
alias ni='npm install'
alias nr='npm run'
alias nt='npm test'
alias nb='npm run build'

# Quick navigation
alias ..='cd ..'
alias ...='cd ../..'
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'

# Development helpers
alias serve='python3 -m http.server 8000'
alias json='python3 -m json.tool'
alias timestamp='date +%s'
EOF

# Create project structure template
echo ""
echo "📁 Creating project templates..."
echo "==============================="

mkdir -p ~/templates/github-project
cat > ~/templates/github-project/.gitignore << 'EOF'
# Dependencies
node_modules/
vendor/
venv/
.env

# Build outputs
dist/
build/
*.pyc
__pycache__/

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Testing
coverage/
.coverage
.pytest_cache/
*.cover

# Security
.env
.env.local
*.pem
*.key
EOF

cat > ~/templates/github-project/.eslintrc.js << 'EOF'
module.exports = {
  env: {
    browser: true,
    es2021: true,
    node: true,
  },
  extends: [
    'eslint:recommended',
  ],
  parserOptions: {
    ecmaVersion: 12,
    sourceType: 'module',
  },
  rules: {
    'indent': ['error', 2],
    'linebreak-style': ['error', 'unix'],
    'quotes': ['error', 'single'],
    'semi': ['error', 'always'],
  },
};
EOF

cat > ~/templates/github-project/.prettierrc << 'EOF'
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2
}
EOF

# Create pre-commit check script
echo ""
echo "🔍 Creating pre-commit check script..."
echo "====================================="

mkdir -p ~/scripts
cat > ~/scripts/pre-commit-check.sh << 'EOF'
#!/bin/bash
# Pre-commit checks for development team

echo "Running pre-commit checks..."

# Check for console.log
if git diff --cached --name-only | xargs grep -n "console.log" 2>/dev/null; then
    echo "⚠️  Warning: console.log statements found"
fi

# Check for TODO comments
if git diff --cached --name-only | xargs grep -n "TODO\|FIXME" 2>/dev/null; then
    echo "📝 Note: TODO/FIXME comments found"
fi

# Check for large files
for file in $(git diff --cached --name-only); do
    if [ -f "$file" ]; then
        size=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file" 2>/dev/null)
        if [ "$size" -gt 1048576 ]; then
            echo "⚠️  Warning: Large file detected: $file ($(($size / 1024 / 1024))MB)"
        fi
    fi
done

# Run linters if available
if command -v eslint >/dev/null 2>&1; then
    echo "Running ESLint..."
    git diff --cached --name-only --diff-filter=ACM | grep ".js\|.ts" | xargs eslint
fi

if command -v flake8 >/dev/null 2>&1; then
    echo "Running Flake8..."
    git diff --cached --name-only --diff-filter=ACM | grep ".py" | xargs flake8
fi

echo "✅ Pre-commit checks complete"
EOF

chmod +x ~/scripts/pre-commit-check.sh

# Setup completion message
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Development Environment Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Restart your terminal or run: source ~/.bashrc"
echo "2. Configure your GitHub credentials:"
echo "   git config --global user.name 'Your Name'"
echo "   git config --global user.email 'your.email@sas-com.com'"
echo "3. Set up GitHub CLI: gh auth login"
echo "4. Clone your first repository and start coding!"
echo ""
echo "Useful commands:"
echo "  gdev    - Switch to dev branch and pull latest"
echo "  gfeat   - Create a new feature branch"
echo "  gs      - Git status (short format)"
echo "  ~/scripts/pre-commit-check.sh - Run pre-commit checks"
echo ""
echo "Happy coding! 🚀"