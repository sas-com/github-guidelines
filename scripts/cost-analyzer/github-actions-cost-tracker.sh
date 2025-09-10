#!/bin/bash

# GitHub Actions Cost Tracker
# エス・エー・エス株式会社
# 
# GitHub Actionsの実行コストを追跡・分析するツール
# 
# 使用方法:
#   ./github-actions-cost-tracker.sh [OPTIONS]
# 
# オプション:
#   -o, --owner OWNER       リポジトリオーナー（必須）
#   -r, --repo REPO         リポジトリ名（必須）
#   -t, --token TOKEN       GitHub Personal Access Token（必須）
#   -d, --days DAYS         分析期間（デフォルト: 30日）
#   -b, --branch BRANCH     対象ブランチ（オプション）
#   -f, --format FORMAT     出力形式 (json|csv|html) デフォルト: json
#   -s, --save PATH         結果保存先
#   -v, --verbose           詳細出力

set -euo pipefail

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# デフォルト値
DAYS=30
FORMAT="json"
VERBOSE=false
SAVE_PATH=""
BRANCH=""

# GitHub Actions料金（USD/分）
UBUNTU_RATE=0.008
WINDOWS_RATE=0.016
MACOS_RATE=0.08
MACOS_ARM_RATE=0.16

# 無料枠（分/月）
FREE_MINUTES_PUBLIC=0      # パブリックリポジトリは無制限
FREE_MINUTES_PRIVATE=2000  # プライベートリポジトリは2000分/月

# エラーハンドリング
error_exit() {
    echo -e "${RED}Error: $1${NC}" >&2
    exit 1
}

# 使用方法表示
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

GitHub Actions Cost Tracker - コスト分析ツール

必須オプション:
  -o, --owner OWNER       リポジトリオーナー
  -r, --repo REPO         リポジトリ名  
  -t, --token TOKEN       GitHub Personal Access Token

オプション:
  -d, --days DAYS         分析期間（デフォルト: 30日）
  -b, --branch BRANCH     対象ブランチ
  -f, --format FORMAT     出力形式 (json|csv|html|markdown)
  -s, --save PATH         結果保存先
  -a, --alert THRESHOLD   コストアラート閾値（USD）
  -v, --verbose           詳細出力
  -h, --help              ヘルプ表示

例:
  $0 -o sas-com -r my-repo -t ghp_xxxxx
  $0 -o sas-com -r my-repo -t ghp_xxxxx -d 7 -f html -s report.html
  $0 -o sas-com -r my-repo -t ghp_xxxxx -a 50 --verbose

EOF
    exit 0
}

# 引数解析
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -o|--owner)
                OWNER="$2"
                shift 2
                ;;
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
            -b|--branch)
                BRANCH="$2"
                shift 2
                ;;
            -f|--format)
                FORMAT="$2"
                shift 2
                ;;
            -s|--save)
                SAVE_PATH="$2"
                shift 2
                ;;
            -a|--alert)
                ALERT_THRESHOLD="$2"
                shift 2
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                show_usage
                ;;
            *)
                error_exit "Unknown option: $1"
                ;;
        esac
    done
    
    # 必須パラメータチェック
    [[ -z "${OWNER:-}" ]] && error_exit "Owner is required (-o)"
    [[ -z "${REPO:-}" ]] && error_exit "Repository is required (-r)"
    [[ -z "${TOKEN:-}" ]] && error_exit "Token is required (-t)"
}

# API呼び出し関数
github_api() {
    local endpoint="$1"
    local params="${2:-}"
    
    curl -s -H "Authorization: token $TOKEN" \
         -H "Accept: application/vnd.github.v3+json" \
         "https://api.github.com${endpoint}${params}"
}

# 日付計算
get_date_range() {
    local end_date=$(date -I)
    local start_date=$(date -I -d "$DAYS days ago")
    echo "$start_date..$end_date"
}

# ワークフロー実行情報取得
fetch_workflow_runs() {
    local date_range=$(get_date_range)
    local branch_param=""
    
    [[ -n "$BRANCH" ]] && branch_param="&branch=$BRANCH"
    
    if $VERBOSE; then
        echo -e "${BLUE}Fetching workflow runs from $date_range...${NC}"
    fi
    
    github_api "/repos/$OWNER/$REPO/actions/runs" \
               "?per_page=100&created=$date_range$branch_param"
}

# ジョブ情報取得
fetch_job_details() {
    local run_id="$1"
    github_api "/repos/$OWNER/$REPO/actions/runs/$run_id/jobs"
}

# ビルド分数計算
calculate_billable_minutes() {
    local jobs_json="$1"
    local ubuntu_minutes=0
    local windows_minutes=0
    local macos_minutes=0
    local macos_arm_minutes=0
    
    # 各ジョブの実行時間を計算
    while IFS= read -r job; do
        local runner_os=$(echo "$job" | jq -r '.runner_os // "Linux"')
        local started_at=$(echo "$job" | jq -r '.started_at // ""')
        local completed_at=$(echo "$job" | jq -r '.completed_at // ""')
        local status=$(echo "$job" | jq -r '.status // ""')
        
        # 完了したジョブのみカウント
        if [[ "$status" == "completed" && -n "$started_at" && -n "$completed_at" ]]; then
            # 実行時間を秒単位で計算
            local start_epoch=$(date -d "$started_at" +%s 2>/dev/null || echo 0)
            local end_epoch=$(date -d "$completed_at" +%s 2>/dev/null || echo 0)
            local duration_seconds=$((end_epoch - start_epoch))
            
            # 分単位に変換（切り上げ）
            local duration_minutes=$(( (duration_seconds + 59) / 60 ))
            
            # OSごとに集計
            case "$runner_os" in
                *[Ll]inux*|*[Uu]buntu*)
                    ubuntu_minutes=$((ubuntu_minutes + duration_minutes))
                    ;;
                *[Ww]indows*)
                    windows_minutes=$((windows_minutes + duration_minutes))
                    ;;
                *[Mm]ac*|*[Oo][Ss][Xx]*)
                    # ARMかIntelか判定（簡易版）
                    if [[ "$runner_os" =~ "arm" || "$runner_os" =~ "M1" ]]; then
                        macos_arm_minutes=$((macos_arm_minutes + duration_minutes))
                    else
                        macos_minutes=$((macos_minutes + duration_minutes))
                    fi
                    ;;
            esac
        fi
    done < <(echo "$jobs_json" | jq -c '.jobs[]')
    
    echo "$ubuntu_minutes,$windows_minutes,$macos_minutes,$macos_arm_minutes"
}

# コスト計算
calculate_cost() {
    local ubuntu_minutes=$1
    local windows_minutes=$2
    local macos_minutes=$3
    local macos_arm_minutes=$4
    
    # 料金計算
    local ubuntu_cost=$(echo "scale=4; $ubuntu_minutes * $UBUNTU_RATE" | bc)
    local windows_cost=$(echo "scale=4; $windows_minutes * $WINDOWS_RATE" | bc)
    local macos_cost=$(echo "scale=4; $macos_minutes * $MACOS_RATE" | bc)
    local macos_arm_cost=$(echo "scale=4; $macos_arm_minutes * $MACOS_ARM_RATE" | bc)
    
    local total_cost=$(echo "scale=4; $ubuntu_cost + $windows_cost + $macos_cost + $macos_arm_cost" | bc)
    
    echo "$ubuntu_cost,$windows_cost,$macos_cost,$macos_arm_cost,$total_cost"
}

# メイン分析処理
analyze_costs() {
    local runs_json=$(fetch_workflow_runs)
    local total_runs=$(echo "$runs_json" | jq '.total_count')
    
    if [[ "$total_runs" -eq 0 ]]; then
        echo -e "${YELLOW}No workflow runs found in the specified period.${NC}"
        exit 0
    fi
    
    echo -e "${GREEN}Analyzing $total_runs workflow runs...${NC}"
    
    # 集計変数
    local total_ubuntu_minutes=0
    local total_windows_minutes=0
    local total_macos_minutes=0
    local total_macos_arm_minutes=0
    local workflow_costs=""
    
    # 各ワークフロー実行を分析
    while IFS= read -r run; do
        local run_id=$(echo "$run" | jq -r '.id')
        local workflow_name=$(echo "$run" | jq -r '.name')
        local run_number=$(echo "$run" | jq -r '.run_number')
        local created_at=$(echo "$run" | jq -r '.created_at')
        local status=$(echo "$run" | jq -r '.status')
        
        if $VERBOSE; then
            echo "  Analyzing: $workflow_name #$run_number"
        fi
        
        # ジョブ詳細取得
        local jobs_json=$(fetch_job_details "$run_id")
        
        # ビルド分数計算
        IFS=',' read -r ubuntu_min windows_min macos_min macos_arm_min <<< \
            $(calculate_billable_minutes "$jobs_json")
        
        # 累計
        total_ubuntu_minutes=$((total_ubuntu_minutes + ubuntu_min))
        total_windows_minutes=$((total_windows_minutes + windows_min))
        total_macos_minutes=$((total_macos_minutes + macos_min))
        total_macos_arm_minutes=$((total_macos_arm_minutes + macos_arm_min))
        
        # ワークフローごとのコスト記録
        workflow_costs="${workflow_costs}${workflow_name},${run_number},${created_at},${ubuntu_min},${windows_min},${macos_min},${macos_arm_min}\n"
        
        # API制限対策
        sleep 0.1
    done < <(echo "$runs_json" | jq -c '.workflow_runs[]')
    
    # 総コスト計算
    IFS=',' read -r ubuntu_cost windows_cost macos_cost macos_arm_cost total_cost <<< \
        $(calculate_cost $total_ubuntu_minutes $total_windows_minutes $total_macos_minutes $total_macos_arm_minutes)
    
    # 結果生成
    generate_report "$total_ubuntu_minutes" "$total_windows_minutes" "$total_macos_minutes" "$total_macos_arm_minutes" \
                   "$ubuntu_cost" "$windows_cost" "$macos_cost" "$macos_arm_cost" "$total_cost" \
                   "$workflow_costs"
}

# レポート生成
generate_report() {
    local ubuntu_min=$1
    local windows_min=$2
    local macos_min=$3
    local macos_arm_min=$4
    local ubuntu_cost=$5
    local windows_cost=$6
    local macos_cost=$7
    local macos_arm_cost=$8
    local total_cost=$9
    local workflow_details=${10}
    
    local total_minutes=$((ubuntu_min + windows_min + macos_min + macos_arm_min))
    local timestamp=$(date -Iseconds)
    
    case "$FORMAT" in
        json)
            generate_json_report "$@"
            ;;
        csv)
            generate_csv_report "$@"
            ;;
        html)
            generate_html_report "$@"
            ;;
        markdown)
            generate_markdown_report "$@"
            ;;
        *)
            generate_json_report "$@"
            ;;
    esac
    
    # アラートチェック
    if [[ -n "${ALERT_THRESHOLD:-}" ]]; then
        if (( $(echo "$total_cost > $ALERT_THRESHOLD" | bc -l) )); then
            echo -e "${RED}⚠️  ALERT: Total cost ($${total_cost}) exceeds threshold ($${ALERT_THRESHOLD})${NC}"
        fi
    fi
}

# JSON形式レポート
generate_json_report() {
    local report=$(cat <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "period": {
    "days": $DAYS,
    "start": "$(date -I -d "$DAYS days ago")",
    "end": "$(date -I)"
  },
  "repository": {
    "owner": "$OWNER",
    "name": "$REPO"
  },
  "usage": {
    "total_minutes": $((ubuntu_min + windows_min + macos_min + macos_arm_min)),
    "ubuntu_minutes": $1,
    "windows_minutes": $2,
    "macos_minutes": $3,
    "macos_arm_minutes": $4
  },
  "costs": {
    "ubuntu": $5,
    "windows": $6,
    "macos": $7,
    "macos_arm": $8,
    "total": $9
  },
  "rates": {
    "ubuntu_per_minute": $UBUNTU_RATE,
    "windows_per_minute": $WINDOWS_RATE,
    "macos_per_minute": $MACOS_RATE,
    "macos_arm_per_minute": $MACOS_ARM_RATE
  },
  "free_minutes": {
    "available": $FREE_MINUTES_PRIVATE,
    "remaining": $((FREE_MINUTES_PRIVATE - ubuntu_min - windows_min - macos_min - macos_arm_min)),
    "percentage_used": $(echo "scale=2; ($ubuntu_min + $windows_min + $macos_min + $macos_arm_min) * 100 / $FREE_MINUTES_PRIVATE" | bc)
  }
}
EOF
)
    
    if [[ -n "$SAVE_PATH" ]]; then
        echo "$report" > "$SAVE_PATH"
        echo -e "${GREEN}Report saved to: $SAVE_PATH${NC}"
    else
        echo "$report"
    fi
}

# CSV形式レポート
generate_csv_report() {
    local csv_header="Date,Repository,Total Minutes,Ubuntu Minutes,Windows Minutes,macOS Minutes,macOS ARM Minutes,Total Cost (USD)"
    local csv_data="$(date -I),$OWNER/$REPO,$((ubuntu_min + windows_min + macos_min + macos_arm_min)),$1,$2,$3,$4,$9"
    
    if [[ -n "$SAVE_PATH" ]]; then
        echo "$csv_header" > "$SAVE_PATH"
        echo "$csv_data" >> "$SAVE_PATH"
        echo -e "${GREEN}CSV report saved to: $SAVE_PATH${NC}"
    else
        echo "$csv_header"
        echo "$csv_data"
    fi
}

# HTML形式レポート
generate_html_report() {
    local html=$(cat <<EOF
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>GitHub Actions Cost Report - $OWNER/$REPO</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #24292e; border-bottom: 2px solid #e1e4e8; padding-bottom: 10px; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .metric { background: #f6f8fa; padding: 15px; border-radius: 6px; border-left: 4px solid #0366d6; }
        .metric-value { font-size: 24px; font-weight: bold; color: #0366d6; }
        .metric-label { color: #586069; font-size: 14px; margin-top: 5px; }
        .cost-breakdown { margin: 20px 0; }
        table { width: 100%; border-collapse: collapse; }
        th { background: #f6f8fa; padding: 10px; text-align: left; }
        td { padding: 10px; border-bottom: 1px solid #e1e4e8; }
        .alert { background: #fffbdd; border: 1px solid #f0c36d; padding: 10px; border-radius: 4px; margin: 20px 0; }
        .chart { margin: 20px 0; }
        canvas { max-width: 100%; }
    </style>
</head>
<body>
    <div class="container">
        <h1>💰 GitHub Actions Cost Report</h1>
        <p><strong>Repository:</strong> $OWNER/$REPO | <strong>Period:</strong> Last $DAYS days | <strong>Generated:</strong> $(date)</p>
        
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">$9 USD</div>
                <div class="metric-label">Total Cost</div>
            </div>
            <div class="metric">
                <div class="metric-value">$((ubuntu_min + windows_min + macos_min + macos_arm_min))</div>
                <div class="metric-label">Total Minutes</div>
            </div>
            <div class="metric">
                <div class="metric-value">$(echo "scale=1; ($ubuntu_min + $windows_min + $macos_min + macos_arm_min) * 100 / $FREE_MINUTES_PRIVATE" | bc)%</div>
                <div class="metric-label">Free Tier Used</div>
            </div>
        </div>
        
        <h2>Cost Breakdown by OS</h2>
        <table>
            <thead>
                <tr>
                    <th>Operating System</th>
                    <th>Minutes Used</th>
                    <th>Rate (USD/min)</th>
                    <th>Cost (USD)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>🐧 Ubuntu</td>
                    <td>$1</td>
                    <td>\$$UBUNTU_RATE</td>
                    <td>\$$5</td>
                </tr>
                <tr>
                    <td>🪟 Windows</td>
                    <td>$2</td>
                    <td>\$$WINDOWS_RATE</td>
                    <td>\$$6</td>
                </tr>
                <tr>
                    <td>🍎 macOS</td>
                    <td>$3</td>
                    <td>\$$MACOS_RATE</td>
                    <td>\$$7</td>
                </tr>
                <tr>
                    <td>🍎 macOS (ARM)</td>
                    <td>$4</td>
                    <td>\$$MACOS_ARM_RATE</td>
                    <td>\$$8</td>
                </tr>
            </tbody>
        </table>
        
        <h2>Recommendations</h2>
        <ul>
            $(if (( $(echo "$9 > 50" | bc -l) )); then echo "<li>⚠️ Consider using self-hosted runners to reduce costs</li>"; fi)
            $(if (( $ubuntu_min > 1000 )); then echo "<li>💡 Optimize Ubuntu workflows - they consume the most minutes</li>"; fi)
            $(if (( $macos_min > 100 )); then echo "<li>💰 macOS runners are expensive - consider moving non-critical tests to Linux</li>"; fi)
            <li>✅ Enable workflow caching to reduce build times</li>
            <li>📊 Review and optimize long-running workflows</li>
        </ul>
    </div>
</body>
</html>
EOF
)
    
    if [[ -n "$SAVE_PATH" ]]; then
        echo "$html" > "$SAVE_PATH"
        echo -e "${GREEN}HTML report saved to: $SAVE_PATH${NC}"
    else
        echo "$html"
    fi
}

# Markdown形式レポート
generate_markdown_report() {
    local markdown=$(cat <<EOF
# GitHub Actions Cost Report

**Repository:** $OWNER/$REPO  
**Period:** Last $DAYS days  
**Generated:** $(date)

## 📊 Summary

| Metric | Value |
|--------|-------|
| **Total Cost** | \$$9 USD |
| **Total Minutes** | $((ubuntu_min + windows_min + macos_min + macos_arm_min)) |
| **Free Tier Used** | $(echo "scale=1; ($ubuntu_min + $windows_min + $macos_min + macos_arm_min) * 100 / $FREE_MINUTES_PRIVATE" | bc)% |

## 💰 Cost Breakdown

| Operating System | Minutes | Rate (USD/min) | Cost (USD) |
|-----------------|---------|----------------|------------|
| Ubuntu | $1 | \$$UBUNTU_RATE | \$$5 |
| Windows | $2 | \$$WINDOWS_RATE | \$$6 |
| macOS | $3 | \$$MACOS_RATE | \$$7 |
| macOS (ARM) | $4 | \$$MACOS_ARM_RATE | \$$8 |
| **Total** | **$((ubuntu_min + windows_min + macos_min + macos_arm_min))** | - | **\$$9** |

## 📈 Trends

- Daily average: $(echo "scale=2; $9 / $DAYS" | bc) USD
- Monthly projection: $(echo "scale=2; $9 * 30 / $DAYS" | bc) USD
- Yearly projection: $(echo "scale=2; $9 * 365 / $DAYS" | bc) USD

## 💡 Recommendations

$(if (( $(echo "$9 > 50" | bc -l) )); then echo "- ⚠️ **High cost alert**: Consider implementing cost optimization strategies"; fi)
$(if (( $ubuntu_min > 1000 )); then echo "- Optimize Ubuntu workflows to reduce minutes consumption"; fi)
$(if (( $macos_min > 100 )); then echo "- Consider moving non-critical macOS tests to Linux runners"; fi)
- Enable aggressive caching strategies
- Implement parallel job execution
- Use matrix builds efficiently
- Consider self-hosted runners for high-volume workflows

## 🔧 Next Steps

1. Review long-running workflows
2. Implement caching strategies
3. Optimize test suites
4. Monitor cost trends weekly
5. Set up cost alerts

---
*Report generated by GitHub Actions Cost Tracker*
EOF
)
    
    if [[ -n "$SAVE_PATH" ]]; then
        echo "$markdown" > "$SAVE_PATH"
        echo -e "${GREEN}Markdown report saved to: $SAVE_PATH${NC}"
    else
        echo "$markdown"
    fi
}

# メイン処理
main() {
    parse_args "$@"
    
    echo -e "${BLUE}GitHub Actions Cost Tracker${NC}"
    echo -e "${BLUE}Repository: $OWNER/$REPO${NC}"
    echo -e "${BLUE}Analysis Period: Last $DAYS days${NC}"
    echo ""
    
    # 必要なコマンドチェック
    command -v jq >/dev/null 2>&1 || error_exit "jq is required but not installed"
    command -v bc >/dev/null 2>&1 || error_exit "bc is required but not installed"
    command -v curl >/dev/null 2>&1 || error_exit "curl is required but not installed"
    
    # 分析実行
    analyze_costs
}

# スクリプト実行
main "$@"