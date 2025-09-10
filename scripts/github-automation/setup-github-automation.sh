#!/bin/bash

# GitHub運用自動化スクリプト - セットアップ
# エス・エー・エス株式会社
# 用途: GitHub組織の設定自動適用、監視、レポート

set -euo pipefail

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログ関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# 設定ファイルの読み込み
CONFIG_FILE="./config/github-automation.conf"
if [[ -f "$CONFIG_FILE" ]]; then
    source "$CONFIG_FILE"
else
    log_warn "設定ファイルが見つかりません。デフォルト設定を使用します。"
fi

# デフォルト設定
GITHUB_ORG=${GITHUB_ORG:-"sas-com"}
GITHUB_TOKEN=${GITHUB_TOKEN:-""}
DRY_RUN=${DRY_RUN:-"true"}
LOG_LEVEL=${LOG_LEVEL:-"INFO"}

# 必要なツールの確認
check_dependencies() {
    local deps=("gh" "curl" "jq" "git")
    local missing=()
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing+=("$dep")
        fi
    done
    
    if [ ${#missing[@]} -ne 0 ]; then
        log_error "必要なツールが不足しています: ${missing[*]}"
        log_info "以下のコマンドでインストールしてください:"
        log_info "Ubuntu/Debian: sudo apt-get install curl jq git"
        log_info "GitHub CLI: https://cli.github.com/"
        exit 1
    fi
    
    log_success "依存関係チェック完了"
}

# GitHub CLI認証確認
check_github_auth() {
    if ! gh auth status &> /dev/null; then
        log_error "GitHub CLI認証が必要です"
        log_info "以下のコマンドで認証してください:"
        log_info "gh auth login"
        exit 1
    fi
    
    # 組織へのアクセス確認
    if ! gh api orgs/"$GITHUB_ORG" &> /dev/null; then
        log_error "組織 '$GITHUB_ORG' にアクセスできません"
        exit 1
    fi
    
    log_success "GitHub認証確認完了"
}

# 組織設定の適用
apply_organization_settings() {
    log_info "組織設定を適用中..."
    
    # 組織レベルのセキュリティ設定
    local org_settings='{
        "members_can_create_repositories": false,
        "members_can_create_public_repositories": false,
        "members_can_create_private_repositories": false,
        "members_can_create_internal_repositories": false,
        "members_can_delete_repositories": false,
        "members_can_delete_issues": false,
        "members_can_create_pages": false,
        "members_can_fork_private_repositories": false,
        "web_commit_signoff_required": true,
        "advanced_security_enabled_for_new_repositories": true,
        "dependency_graph_enabled_for_new_repositories": true,
        "dependabot_alerts_enabled_for_new_repositories": true,
        "dependabot_security_updates_enabled_for_new_repositories": true,
        "dependency_review_enabled": true
    }'
    
    if [[ "$DRY_RUN" == "false" ]]; then
        gh api -X PATCH orgs/"$GITHUB_ORG" --input - <<< "$org_settings"
        log_success "組織設定を適用しました"
    else
        log_info "[DRY RUN] 組織設定適用をシミュレート"
    fi
}

# リポジトリ設定のテンプレート適用
apply_repository_settings() {
    local repo=$1
    log_info "リポジトリ '$repo' に設定を適用中..."
    
    # ブランチ保護ルール
    local branch_protection='{
        "required_status_checks": {
            "strict": true,
            "contexts": ["ci/build", "ci/test", "security/scan"]
        },
        "enforce_admins": true,
        "required_pull_request_reviews": {
            "required_approving_review_count": 2,
            "dismiss_stale_reviews": true,
            "require_code_owner_reviews": true,
            "require_last_push_approval": true
        },
        "restrictions": null,
        "required_conversation_resolution": true,
        "allow_force_pushes": false,
        "allow_deletions": false,
        "block_creations": false,
        "required_linear_history": true
    }'
    
    if [[ "$DRY_RUN" == "false" ]]; then
        gh api -X PUT repos/"$GITHUB_ORG"/"$repo"/branches/main/protection \
            --input - <<< "$branch_protection"
        log_success "ブランチ保護ルールを適用: $repo"
    else
        log_info "[DRY RUN] ブランチ保護ルール適用をシミュレート: $repo"
    fi
    
    # セキュリティ機能の有効化
    if [[ "$DRY_RUN" == "false" ]]; then
        gh api -X PUT repos/"$GITHUB_ORG"/"$repo"/vulnerability-alerts
        gh api -X PUT repos/"$GITHUB_ORG"/"$repo"/automated-security-fixes
        log_success "セキュリティ機能を有効化: $repo"
    else
        log_info "[DRY RUN] セキュリティ機能有効化をシミュレート: $repo"
    fi
}

# 全リポジトリに設定を適用
apply_all_repository_settings() {
    log_info "全リポジトリに設定を適用中..."
    
    # 組織のリポジトリ一覧を取得
    local repos
    repos=$(gh api orgs/"$GITHUB_ORG"/repos --jq '.[].name')
    
    local total_repos
    total_repos=$(echo "$repos" | wc -l)
    local current=0
    
    while IFS= read -r repo; do
        ((current++))
        log_info "進行状況: $current/$total_repos - $repo"
        apply_repository_settings "$repo"
        
        # API制限を考慮した待機
        sleep 1
    done <<< "$repos"
    
    log_success "全リポジトリ設定適用完了"
}

# チーム設定の適用
setup_teams() {
    log_info "チーム設定を適用中..."
    
    # チーム定義
    declare -A teams=(
        ["developers"]="Development Team"
        ["devops"]="DevOps/Infrastructure Team"
        ["security"]="Security Team"
        ["reviewers"]="Code Reviewers"
        ["admins"]="Administrators"
    )
    
    for slug in "${!teams[@]}"; do
        local name="${teams[$slug]}"
        local team_data="{\"name\":\"$name\",\"description\":\"$name for GitHub operations\",\"privacy\":\"closed\"}"
        
        if [[ "$DRY_RUN" == "false" ]]; then
            if gh api orgs/"$GITHUB_ORG"/teams/"$slug" &> /dev/null; then
                log_info "チーム '$slug' は既に存在します"
            else
                gh api -X POST orgs/"$GITHUB_ORG"/teams --input - <<< "$team_data"
                log_success "チーム '$slug' を作成しました"
            fi
        else
            log_info "[DRY RUN] チーム作成をシミュレート: $slug"
        fi
    done
}

# 監視設定のセットアップ
setup_monitoring() {
    log_info "監視設定をセットアップ中..."
    
    # Webhook設定のテンプレート作成
    mkdir -p ./monitoring/webhooks
    cat > ./monitoring/webhooks/webhook-config.json << 'EOF'
{
    "name": "web",
    "active": true,
    "events": [
        "push",
        "pull_request",
        "pull_request_review",
        "issues",
        "issue_comment",
        "create",
        "delete",
        "deployment",
        "deployment_status",
        "status",
        "check_run",
        "security_advisory"
    ],
    "config": {
        "url": "https://your-monitoring-endpoint.com/github-webhook",
        "content_type": "json",
        "secret": "your-webhook-secret",
        "insecure_ssl": "0"
    }
}
EOF
    
    # 監視ダッシュボード設定
    cat > ./monitoring/dashboard-config.json << 'EOF'
{
    "github_metrics": {
        "repositories": [],
        "metrics": [
            "commits_per_day",
            "pull_requests_per_day",
            "issues_opened_closed",
            "code_review_time",
            "deployment_frequency",
            "failure_rate",
            "recovery_time",
            "security_alerts"
        ],
        "alerts": {
            "high_failure_rate": {"threshold": 0.15, "severity": "warning"},
            "slow_recovery": {"threshold": 3600, "severity": "critical"},
            "security_alerts": {"threshold": 1, "severity": "high"}
        }
    }
}
EOF
    
    log_success "監視設定テンプレートを作成しました"
}

# レポート生成
generate_report() {
    log_info "組織レポートを生成中..."
    
    local report_dir="./reports/$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$report_dir"
    
    # 組織概要
    gh api orgs/"$GITHUB_ORG" | jq '{
        name: .name,
        login: .login,
        public_repos: .public_repos,
        total_private_repos: .total_private_repos,
        owned_private_repos: .owned_private_repos,
        members: .collaborators,
        created_at: .created_at,
        updated_at: .updated_at
    }' > "$report_dir/organization-overview.json"
    
    # リポジトリ一覧と設定状況
    gh api orgs/"$GITHUB_ORG"/repos --paginate | jq '[.[] | {
        name: .name,
        private: .private,
        security_and_analysis: .security_and_analysis,
        default_branch: .default_branch,
        created_at: .created_at,
        updated_at: .updated_at,
        pushed_at: .pushed_at,
        language: .language
    }]' > "$report_dir/repositories.json"
    
    # チーム一覧
    gh api orgs/"$GITHUB_ORG"/teams | jq '[.[] | {
        name: .name,
        slug: .slug,
        description: .description,
        privacy: .privacy,
        members_count: .members_count,
        repos_count: .repos_count
    }]' > "$report_dir/teams.json"
    
    # セキュリティアラート（過去30日）
    local thirty_days_ago
    thirty_days_ago=$(date -d '30 days ago' +%Y-%m-%d)
    
    {
        echo "# GitHub組織レポート - $(date '+%Y-%m-%d %H:%M:%S')"
        echo ""
        echo "## 組織概要"
        echo "- 組織名: $(jq -r '.name' "$report_dir/organization-overview.json")"
        echo "- パブリックリポジトリ: $(jq -r '.public_repos' "$report_dir/organization-overview.json")"
        echo "- プライベートリポジトリ: $(jq -r '.total_private_repos' "$report_dir/organization-overview.json")"
        echo "- メンバー数: $(jq -r '.members' "$report_dir/organization-overview.json")"
        echo ""
        echo "## セキュリティ状況"
        echo "- 高セキュリティリポジトリ: $(jq '[.[] | select(.security_and_analysis.advanced_security.status == "enabled")] | length' "$report_dir/repositories.json")"
        echo "- Dependabotアラート有効: $(jq '[.[] | select(.security_and_analysis.dependabot_security_updates.status == "enabled")] | length' "$report_dir/repositories.json")"
        echo ""
        echo "## チーム状況"
        jq -r '.[] | "- \(.name): \(.members_count)名, \(.repos_count)リポジトリ"' "$report_dir/teams.json"
    } > "$report_dir/summary-report.md"
    
    log_success "レポートを生成しました: $report_dir"
}

# メイン処理
main() {
    echo "============================================"
    echo "GitHub運用自動化スクリプト"
    echo "エス・エー・エス株式会社"
    echo "============================================"
    echo ""
    
    log_info "設定確認:"
    log_info "- 組織: $GITHUB_ORG"
    log_info "- DRY RUN: $DRY_RUN"
    log_info "- ログレベル: $LOG_LEVEL"
    echo ""
    
    # 実行確認
    if [[ "$DRY_RUN" == "false" ]]; then
        log_warn "本番実行モードです。組織設定が変更されます。"
        read -p "続行しますか? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "処理を中断しました"
            exit 0
        fi
    fi
    
    # 実行フェーズ
    check_dependencies
    check_github_auth
    
    # 設定適用
    apply_organization_settings
    setup_teams
    apply_all_repository_settings
    setup_monitoring
    
    # レポート生成
    generate_report
    
    log_success "GitHub運用自動化セットアップが完了しました"
    
    # 次のステップ
    echo ""
    echo "============================================"
    echo "次のステップ:"
    echo "1. ./monitoring/ ディレクトリの設定をカスタマイズ"
    echo "2. Webhook URLとシークレットを設定"
    echo "3. 監視ダッシュボードをデプロイ"
    echo "4. 定期的なレポート生成をcronで設定"
    echo "============================================"
}

# 引数処理
while [[ $# -gt 0 ]]; do
    case $1 in
        --org)
            GITHUB_ORG="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN="true"
            shift
            ;;
        --apply)
            DRY_RUN="false"
            shift
            ;;
        --help)
            echo "使用方法: $0 [オプション]"
            echo ""
            echo "オプション:"
            echo "  --org ORG_NAME    GitHub組織名 (デフォルト: sas-com)"
            echo "  --dry-run         変更を適用せずにシミュレーション (デフォルト)"
            echo "  --apply           実際に変更を適用"
            echo "  --help            このヘルプを表示"
            exit 0
            ;;
        *)
            log_error "未知のオプション: $1"
            exit 1
            ;;
    esac
done

# メイン処理実行
main