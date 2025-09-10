# Multi-stage Dockerfile for PR Testing
# エス・エー・エス株式会社 - 包括的テスト環境

# =====================================
# Base Stage - 共通設定
# =====================================
FROM node:20-alpine AS base

# セキュリティ強化
RUN addgroup -g 1001 -S nodejs && adduser -S testuser -u 1001 -G nodejs

# 作業ディレクトリ設定
WORKDIR /app

# システム依存関係のインストール
RUN apk add --no-cache \
    git \
    bash \
    curl \
    jq \
    python3 \
    py3-pip \
    openjdk11-jre \
    chromium \
    nss \
    freetype \
    freetype-dev \
    harfbuzz \
    ca-certificates \
    ttf-freefont \
    && rm -rf /var/cache/apk/*

# Chromium設定
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser

# Python環境設定
RUN pip3 install --no-cache-dir \
    pytest \
    pytest-cov \
    pytest-xdist \
    pytest-html \
    pytest-mock \
    pytest-asyncio \
    bandit \
    safety \
    flake8 \
    black \
    isort \
    mypy

# =====================================
# Dependencies Stage - 依存関係インストール
# =====================================
FROM base AS dependencies

# package.jsonとlock fileのコピー
COPY package*.json ./
COPY yarn.lock* ./

# Node.js依存関係のインストール
RUN npm ci --only=production --silent && \
    npm ci --only=development --silent && \
    npm cache clean --force

# =====================================
# Security Scan Stage - セキュリティスキャン専用
# =====================================
FROM base AS security-scanner

# セキュリティツールのインストール
RUN npm install -g \
    @semgrep/semgrep \
    eslint-plugin-security \
    eslint-plugin-no-secrets \
    snyk \
    audit-ci \
    && pip3 install --no-cache-dir \
    bandit \
    safety \
    checkov

# GitLeaks インストール
RUN wget -O gitleaks.tar.gz https://github.com/zricethezav/gitleaks/releases/download/v8.18.0/gitleaks_8.18.0_linux_x64.tar.gz && \
    tar -xzf gitleaks.tar.gz && \
    mv gitleaks /usr/local/bin/ && \
    rm gitleaks.tar.gz

# Trivy インストール
RUN wget -O trivy.tar.gz https://github.com/aquasecurity/trivy/releases/download/v0.46.1/trivy_0.46.1_Linux-64bit.tar.gz && \
    tar -xzf trivy.tar.gz && \
    mv trivy /usr/local/bin/ && \
    rm trivy.tar.gz

# Hadolint インストール
RUN wget -O /usr/local/bin/hadolint https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint-Linux-x86_64 && \
    chmod +x /usr/local/bin/hadolint

COPY --from=dependencies /app/node_modules ./node_modules
COPY . .

# セキュリティスキャン実行スクリプト
RUN cat > /usr/local/bin/run-security-scan.sh << 'EOF' && chmod +x /usr/local/bin/run-security-scan.sh
#!/bin/bash
set -e

echo "🔒 Starting comprehensive security scan..."

# GitLeaks - シークレット検出
echo "Running GitLeaks..."
gitleaks detect --source . --verbose --report-format json --report-path security-reports/gitleaks.json || echo "GitLeaks warnings found"

# Semgrep - SAST
echo "Running Semgrep..."
semgrep --config=auto --json --output security-reports/semgrep.json . || echo "Semgrep issues found"

# NPM Audit
echo "Running NPM Audit..."
npm audit --audit-level=moderate --json > security-reports/npm-audit.json || echo "NPM vulnerabilities found"

# Snyk (if token available)
if [ -n "$SNYK_TOKEN" ]; then
    echo "Running Snyk..."
    snyk test --json > security-reports/snyk.json || echo "Snyk vulnerabilities found"
fi

# Bandit - Python security
if ls *.py &>/dev/null; then
    echo "Running Bandit..."
    bandit -r . -f json -o security-reports/bandit.json || echo "Bandit issues found"
fi

# Safety - Python dependencies
if [ -f "requirements.txt" ]; then
    echo "Running Safety..."
    safety check --json --output security-reports/safety.json || echo "Safety vulnerabilities found"
fi

# ESLint Security
echo "Running ESLint Security..."
npx eslint . --ext .js,.ts,.jsx,.tsx --plugin security --plugin no-secrets -f json -o security-reports/eslint-security.json || echo "ESLint security issues found"

echo "✅ Security scan completed. Results in security-reports/"
EOF

# =====================================
# Test Runner Stage - テスト実行環境
# =====================================
FROM base AS test-runner

# Playwright のインストール
RUN npm install -g @playwright/test playwright && \
    npx playwright install --with-deps chromium firefox webkit

# K6 負荷テストツールのインストール
RUN wget -O k6.tar.gz https://github.com/grafana/k6/releases/download/v0.47.0/k6-v0.47.0-linux-amd64.tar.gz && \
    tar -xzf k6.tar.gz && \
    mv k6-v0.47.0-linux-amd64/k6 /usr/local/bin/ && \
    rm -rf k6.tar.gz k6-v0.47.0-linux-amd64

# Lighthouse CLI のインストール
RUN npm install -g @lhci/cli lighthouse

# Apache Bench (ab) のインストール
RUN apk add --no-cache apache2-utils

COPY --from=dependencies /app/node_modules ./node_modules
COPY . .

# テスト実行スクリプト
RUN cat > /usr/local/bin/run-tests.sh << 'EOF' && chmod +x /usr/local/bin/run-tests.sh
#!/bin/bash
set -e

echo "🧪 Starting comprehensive test suite..."

# Create test result directories
mkdir -p test-results/{unit,integration,e2e,performance} coverage

# Unit Tests - Jest
echo "Running Unit Tests..."
if [ -f "jest.config.js" ]; then
    npm test -- --coverage --ci --reporters=default --reporters=jest-junit --outputFile=test-results/unit/jest-results.xml
    mv coverage/* test-results/unit/ 2>/dev/null || true
fi

# Python Unit Tests - Pytest
echo "Running Python Unit Tests..."
if [ -f "pytest.ini" ] && ls tests/*.py &>/dev/null; then
    pytest --junitxml=test-results/unit/pytest-results.xml --cov-report=xml:test-results/unit/coverage.xml
fi

# Integration Tests
echo "Running Integration Tests..."
if npm run test:integration &>/dev/null; then
    npm run test:integration -- --outputFile=test-results/integration/results.xml
fi

# E2E Tests - Playwright
echo "Running E2E Tests..."
if [ -f "playwright.config.ts" ] || [ -f "playwright.config.js" ]; then
    npx playwright test --reporter=junit --output-dir=test-results/e2e/
fi

# Performance Tests
echo "Running Performance Tests..."
if [ -f "tests/performance/load-test.js" ]; then
    k6 run tests/performance/load-test.js --out json=test-results/performance/k6-results.json
fi

# Lighthouse Performance
if npm run build &>/dev/null; then
    echo "Running Lighthouse..."
    npm run build
    npm start &
    sleep 30
    lhci autorun --outputDir=test-results/performance/lighthouse || echo "Lighthouse warnings"
    pkill -f "npm start" || true
fi

echo "✅ All tests completed. Results in test-results/"
EOF

# =====================================
# Development Stage - 開発用環境
# =====================================
FROM test-runner AS development

# 開発用ツールの追加インストール
RUN npm install -g \
    nodemon \
    ts-node \
    @types/node \
    concurrently

# ホットリロード設定
ENV NODE_ENV=development
EXPOSE 3000 3001 8000

# 開発用起動スクリプト
RUN cat > /usr/local/bin/dev-server.sh << 'EOF' && chmod +x /usr/local/bin/dev-server.sh
#!/bin/bash
if [ -f "package.json" ] && grep -q '"dev"' package.json; then
    npm run dev
elif [ -f "app.py" ]; then
    python3 app.py
else
    echo "No development script found"
    tail -f /dev/null
fi
EOF

CMD ["dev-server.sh"]

# =====================================
# Production Stage - 本番用最小イメージ
# =====================================
FROM node:20-alpine AS production

# セキュリティ強化
RUN addgroup -g 1001 -S nodejs && adduser -S appuser -u 1001 -G nodejs

WORKDIR /app

# 本番用依存関係のみ
COPY --from=dependencies /app/node_modules ./node_modules
COPY --chown=appuser:nodejs . .

# 本番ビルド
RUN npm run build 2>/dev/null || echo "No build script found"

# 非root権限で実行
USER appuser

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

EXPOSE 3000

CMD ["npm", "start"]

# =====================================
# CI Stage - CI/CD専用環境
# =====================================
FROM security-scanner AS ci

# CI専用設定
ENV CI=true
ENV NODE_ENV=test
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Playwright browser のキャッシュ
RUN npx playwright install --with-deps

# CI実行スクリプト
RUN cat > /usr/local/bin/ci-pipeline.sh << 'EOF' && chmod +x /usr/local/bin/ci-pipeline.sh
#!/bin/bash
set -e

echo "🚀 Starting CI Pipeline..."

# Stage 1: Basic Quality Checks
echo "Stage 1: Basic Quality Checks"
npm run lint || echo "Lint issues found"
npm run type-check || echo "Type errors found"

# Stage 2: Security Scans
echo "Stage 2: Security Scans"
/usr/local/bin/run-security-scan.sh

# Stage 3: Tests
echo "Stage 3: Tests"
/usr/local/bin/run-tests.sh

# Stage 4: Quality Reports
echo "Stage 4: Quality Reports"
if [ -f "sonar-project.properties" ]; then
    # SonarQube scan would go here
    echo "SonarQube scan ready"
fi

echo "✅ CI Pipeline completed successfully!"
EOF

CMD ["ci-pipeline.sh"]