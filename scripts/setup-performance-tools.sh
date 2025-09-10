#!/bin/bash

# GitHub Actions Performance Tools Setup Script
# エス・エー・エス株式会社
# 
# パフォーマンス最適化ツールのセットアップスクリプト

set -euo pipefail

# カラー定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}GitHub Actions Performance Tools${NC}"
echo -e "${BLUE}Setup Script${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# 必要なディレクトリの作成
echo -e "${GREEN}[1/5] Creating directories...${NC}"
mkdir -p scripts/performance-monitor
mkdir -p scripts/cost-analyzer
mkdir -p .github/workflows/optimized
mkdir -p reports/performance
mkdir -p reports/costs

# 実行権限の付与
echo -e "${GREEN}[2/5] Setting execute permissions...${NC}"
chmod +x scripts/cost-analyzer/github-actions-cost-tracker.sh 2>/dev/null || true
chmod +x scripts/performance-monitor/workflow-analyzer.py 2>/dev/null || true

# Python依存関係のチェックとインストール
echo -e "${GREEN}[3/5] Checking Python dependencies...${NC}"
if command -v python3 &> /dev/null; then
    echo "Python3 found: $(python3 --version)"
    
    # 必要なパッケージのインストール
    if command -v pip3 &> /dev/null; then
        echo "Installing Python packages..."
        pip3 install --user requests 2>/dev/null || echo "  - requests already installed"
    else
        echo -e "${YELLOW}Warning: pip3 not found. Please install Python packages manually.${NC}"
    fi
else
    echo -e "${YELLOW}Warning: Python3 not found. Performance analyzer requires Python3.${NC}"
fi

# bashツール依存関係のチェック
echo -e "${GREEN}[4/5] Checking bash dependencies...${NC}"
MISSING_DEPS=""

if ! command -v jq &> /dev/null; then
    MISSING_DEPS="$MISSING_DEPS jq"
fi

if ! command -v bc &> /dev/null; then
    MISSING_DEPS="$MISSING_DEPS bc"
fi

if ! command -v curl &> /dev/null; then
    MISSING_DEPS="$MISSING_DEPS curl"
fi

if [ -n "$MISSING_DEPS" ]; then
    echo -e "${YELLOW}Missing dependencies:$MISSING_DEPS${NC}"
    echo "Please install missing dependencies:"
    echo "  Ubuntu/Debian: sudo apt-get install$MISSING_DEPS"
    echo "  macOS: brew install$MISSING_DEPS"
    echo "  RHEL/CentOS: sudo yum install$MISSING_DEPS"
else
    echo "All bash dependencies are installed ✓"
fi

# 設定ファイルの作成
echo -e "${GREEN}[5/5] Creating configuration files...${NC}"

# パフォーマンス監視設定
cat > scripts/performance-monitor/config.json <<EOF
{
  "github": {
    "owner": "sas-com",
    "repo": "",
    "token": ""
  },
  "monitoring": {
    "interval_minutes": 60,
    "retention_days": 30,
    "alert_threshold": {
      "duration_minutes": 30,
      "cost_usd": 10,
      "failure_rate_percent": 20
    }
  },
  "reporting": {
    "format": "html",
    "output_dir": "reports/performance",
    "send_email": false,
    "email_recipients": []
  }
}
EOF

# コスト管理設定
cat > scripts/cost-analyzer/config.sh <<EOF
#!/bin/bash
# Cost Analyzer Configuration

# GitHub設定
export GITHUB_OWNER="sas-com"
export GITHUB_REPO=""
export GITHUB_TOKEN=""

# 分析設定
export ANALYSIS_DAYS=30
export OUTPUT_FORMAT="html"
export REPORT_DIR="reports/costs"

# アラート設定
export COST_ALERT_THRESHOLD=100  # USD
export MINUTES_ALERT_THRESHOLD=1500  # 分
export EMAIL_ALERTS=false
export ALERT_RECIPIENTS=""

# 無料枠設定
export FREE_MINUTES_PRIVATE=2000
export FREE_MINUTES_PUBLIC=0
EOF

chmod +x scripts/cost-analyzer/config.sh

# サンプル実行スクリプトの作成
cat > run-performance-analysis.sh <<'EOF'
#!/bin/bash

# パフォーマンス分析実行スクリプト

set -euo pipefail

# 設定読み込み
source scripts/cost-analyzer/config.sh

# 使用方法
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -r, --repo REPO     Repository name"
    echo "  -t, --token TOKEN   GitHub token"
    echo "  -d, --days DAYS     Analysis period (default: 30)"
    echo "  -h, --help          Show this help"
    exit 0
}

# デフォルト値
REPO=""
TOKEN=""
DAYS=30

# 引数解析
while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--repo)
            REPO="$2"
            shift 2
            ;;
        -t|--token)
            TOKEN="$2"
            shift 2
            ;;
        -d|--days)
            DAYS="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            ;;
    esac
done

# パラメータチェック
if [[ -z "$REPO" ]]; then
    echo "Error: Repository name is required"
    show_usage
fi

if [[ -z "$TOKEN" ]]; then
    echo "Error: GitHub token is required"
    show_usage
fi

echo "Starting Performance Analysis..."
echo "Repository: $GITHUB_OWNER/$REPO"
echo "Period: Last $DAYS days"
echo ""

# タイムスタンプ
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# パフォーマンス分析実行
echo "Running workflow performance analysis..."
python3 scripts/performance-monitor/workflow-analyzer.py \
    --token "$TOKEN" \
    --owner "$GITHUB_OWNER" \
    --repo "$REPO" \
    --limit "$DAYS" \
    --output "reports/performance/performance_${REPO}_${TIMESTAMP}.html"

# コスト分析実行
echo "Running cost analysis..."
./scripts/cost-analyzer/github-actions-cost-tracker.sh \
    -o "$GITHUB_OWNER" \
    -r "$REPO" \
    -t "$TOKEN" \
    -d "$DAYS" \
    -f html \
    -s "reports/costs/cost_${REPO}_${TIMESTAMP}.html"

echo ""
echo "Analysis complete!"
echo "Performance report: reports/performance/performance_${REPO}_${TIMESTAMP}.html"
echo "Cost report: reports/costs/cost_${REPO}_${TIMESTAMP}.html"
EOF

chmod +x run-performance-analysis.sh

# 完了メッセージ
echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo -e "${BLUE}次のステップ:${NC}"
echo "1. GitHub Personal Access Tokenを取得:"
echo "   https://github.com/settings/tokens"
echo ""
echo "2. 設定ファイルを編集:"
echo "   - scripts/performance-monitor/config.json"
echo "   - scripts/cost-analyzer/config.sh"
echo ""
echo "3. 分析を実行:"
echo "   ./run-performance-analysis.sh -r <repo-name> -t <github-token>"
echo ""
echo -e "${YELLOW}ヒント:${NC}"
echo "- トークンには 'repo' と 'workflow' スコープが必要です"
echo "- 初回実行時は過去30日分のデータを分析します"
echo "- レポートは reports/ ディレクトリに保存されます"
echo ""
echo -e "${BLUE}詳細なドキュメント:${NC}"
echo "- CICD_PERFORMANCE_OPTIMIZATION_GUIDE.md"
echo "- .github/workflows/optimized/README.md"