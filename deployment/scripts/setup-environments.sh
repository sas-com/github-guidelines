#!/bin/bash
# Setup Deployment Environments Script
# エス・エー・エス株式会社 - GitHub運用ガイドライン

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_FILE="${SCRIPT_DIR}/setup-environments.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Help function
show_help() {
    cat << EOF
GitHub Environment Setup Script

Usage: $0 [OPTIONS]

OPTIONS:
    -e, --environment ENV    Set up specific environment (dev|staging|prod|all)
    -o, --org ORG           GitHub organization name (default: sas-com)
    -r, --repo REPO         GitHub repository name (default: github-guidelines)
    -t, --token TOKEN       GitHub token with admin permissions
    -v, --verify            Verify existing environment configuration
    -d, --dry-run           Show what would be done without making changes
    -h, --help              Show this help message

EXAMPLES:
    $0 -e dev -o sas-com -r my-repo -t ghp_xxx
    $0 -e all --verify
    $0 --dry-run -e staging

REQUIREMENTS:
    - GitHub CLI (gh) must be installed and authenticated
    - Admin permissions on the target repository
    - Valid GitHub token with appropriate scopes

EOF
}

# Default values
ENVIRONMENT=""
GITHUB_ORG="sas-com"
GITHUB_REPO="github-guidelines"
GITHUB_TOKEN=""
VERIFY_ONLY=false
DRY_RUN=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -o|--org)
            GITHUB_ORG="$2"
            shift 2
            ;;
        -r|--repo)
            GITHUB_REPO="$2"
            shift 2
            ;;
        -t|--token)
            GITHUB_TOKEN="$2"
            shift 2
            ;;
        -v|--verify)
            VERIFY_ONLY=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validation
if [[ -z "$ENVIRONMENT" ]]; then
    log_error "Environment must be specified (-e|--environment)"
    show_help
    exit 1
fi

if [[ "$ENVIRONMENT" != "dev" && "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "prod" && "$ENVIRONMENT" != "all" ]]; then
    log_error "Environment must be one of: dev, staging, prod, all"
    exit 1
fi

# Initialize log file
echo "GitHub Environment Setup - $(date)" > "$LOG_FILE"
log_info "Starting environment setup for: $ENVIRONMENT"

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if gh CLI is installed
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI (gh) is not installed. Please install it first."
        exit 1
    fi
    
    # Check if authenticated
    if ! gh auth status &> /dev/null; then
        log_error "GitHub CLI is not authenticated. Please run 'gh auth login' first."
        exit 1
    fi
    
    # Check repository access
    if ! gh repo view "$GITHUB_ORG/$GITHUB_REPO" &> /dev/null; then
        log_error "Cannot access repository $GITHUB_ORG/$GITHUB_REPO"
        exit 1
    fi
    
    log_success "Prerequisites check completed"
}

# Setup development environment
setup_dev_environment() {
    local env_name="development"
    log_info "Setting up $env_name environment..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would create environment: $env_name"
        return
    fi
    
    # Create environment
    gh api \
        --method POST \
        -H "Accept: application/vnd.github+json" \
        "/repos/$GITHUB_ORG/$GITHUB_REPO/environments/$env_name" \
        --input - << EOF || log_warning "Environment may already exist"
{
  "wait_timer": 0,
  "reviewers": [],
  "deployment_branch_policy": {
    "protected_branches": false,
    "custom_branch_policies": true
  }
}
EOF
    
    # Set environment variables
    local env_vars=(
        "NODE_ENV=development"
        "LOG_LEVEL=debug"
        "ENVIRONMENT=development"
        "DEBUG_MODE=true"
        "CACHE_TTL=300"
        "API_TIMEOUT=30000"
    )
    
    for var in "${env_vars[@]}"; do
        IFS='=' read -r key value <<< "$var"
        log_info "Setting environment variable: $key"
        
        gh api \
            --method PUT \
            -H "Accept: application/vnd.github+json" \
            "/repos/$GITHUB_ORG/$GITHUB_REPO/environments/$env_name/variables/$key" \
            --field name="$key" \
            --field value="$value" || log_warning "Failed to set $key"
    done
    
    log_success "Development environment setup completed"
}

# Setup staging environment
setup_staging_environment() {
    local env_name="staging"
    log_info "Setting up $env_name environment..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would create environment: $env_name"
        return
    fi
    
    # Create environment with protection rules
    gh api \
        --method POST \
        -H "Accept: application/vnd.github+json" \
        "/repos/$GITHUB_ORG/$GITHUB_REPO/environments/$env_name" \
        --input - << EOF || log_warning "Environment may already exist"
{
  "wait_timer": 0,
  "reviewers": [
    {
      "type": "Team",
      "id": null
    }
  ],
  "deployment_branch_policy": {
    "protected_branches": true,
    "custom_branch_policies": false
  }
}
EOF
    
    # Set environment variables
    local env_vars=(
        "NODE_ENV=production"
        "LOG_LEVEL=info"
        "ENVIRONMENT=staging"
        "DEBUG_MODE=false"
        "CACHE_TTL=600"
        "API_TIMEOUT=10000"
        "MAX_CONNECTIONS=100"
        "POOL_SIZE=10"
    )
    
    for var in "${env_vars[@]}"; do
        IFS='=' read -r key value <<< "$var"
        log_info "Setting environment variable: $key"
        
        gh api \
            --method PUT \
            -H "Accept: application/vnd.github+json" \
            "/repos/$GITHUB_ORG/$GITHUB_REPO/environments/$env_name/variables/$key" \
            --field name="$key" \
            --field value="$value" || log_warning "Failed to set $key"
    done
    
    log_success "Staging environment setup completed"
}

# Setup production environment
setup_production_environment() {
    local env_name="production"
    log_info "Setting up $env_name environment..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would create environment: $env_name"
        return
    fi
    
    # Create environment with strict protection rules
    gh api \
        --method POST \
        -H "Accept: application/vnd.github+json" \
        "/repos/$GITHUB_ORG/$GITHUB_REPO/environments/$env_name" \
        --input - << EOF || log_warning "Environment may already exist"
{
  "wait_timer": 5,
  "reviewers": [
    {
      "type": "Team",
      "id": null
    }
  ],
  "deployment_branch_policy": {
    "protected_branches": true,
    "custom_branch_policies": false
  }
}
EOF
    
    # Set environment variables
    local env_vars=(
        "NODE_ENV=production"
        "LOG_LEVEL=warn"
        "ENVIRONMENT=production"
        "DEBUG_MODE=false"
        "CACHE_TTL=3600"
        "API_TIMEOUT=5000"
        "MAX_CONNECTIONS=500"
        "POOL_SIZE=50"
        "WORKER_PROCESSES=auto"
        "SESSION_TIMEOUT=900"
        "CSRF_PROTECTION=true"
        "RATE_LIMITING=true"
        "CDN_ENABLED=true"
    )
    
    for var in "${env_vars[@]}"; do
        IFS='=' read -r key value <<< "$var"
        log_info "Setting environment variable: $key"
        
        gh api \
            --method PUT \
            -H "Accept: application/vnd.github+json" \
            "/repos/$GITHUB_ORG/$GITHUB_REPO/environments/$env_name/variables/$key" \
            --field name="$key" \
            --field value="$value" || log_warning "Failed to set $key"
    done
    
    log_success "Production environment setup completed"
}

# Verify environment configuration
verify_environment() {
    local env_name="$1"
    log_info "Verifying $env_name environment configuration..."
    
    # Get environment details
    local env_data
    env_data=$(gh api "/repos/$GITHUB_ORG/$GITHUB_REPO/environments/$env_name" 2>/dev/null)
    
    if [[ -z "$env_data" ]]; then
        log_error "Environment $env_name not found"
        return 1
    fi
    
    # Parse environment data
    local wait_timer
    wait_timer=$(echo "$env_data" | jq -r '.protection_rules[0].wait_timer // 0')
    
    local reviewer_count
    reviewer_count=$(echo "$env_data" | jq -r '.protection_rules[0].reviewers | length // 0')
    
    log_info "Environment: $env_name"
    log_info "  Wait Timer: ${wait_timer} minutes"
    log_info "  Required Reviewers: $reviewer_count"
    
    # Get environment variables
    log_info "Environment Variables:"
    gh api "/repos/$GITHUB_ORG/$GITHUB_REPO/environments/$env_name/variables" | \
        jq -r '.variables[]? | "  \(.name)=\(.value)"' || log_warning "No variables found"
    
    # Get secrets (names only)
    log_info "Environment Secrets:"
    gh api "/repos/$GITHUB_ORG/$GITHUB_REPO/environments/$env_name/secrets" | \
        jq -r '.secrets[]? | "  \(.name)"' || log_warning "No secrets found"
    
    log_success "$env_name environment verification completed"
}

# Setup repository secrets
setup_repository_secrets() {
    log_info "Setting up repository-level secrets..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would set up repository secrets"
        return
    fi
    
    # Common repository secrets (these would be set with actual values)
    local secrets=(
        "CODECOV_TOKEN"
        "SNYK_TOKEN"
        "SEMGREP_APP_TOKEN"
        "SONARQUBE_TOKEN"
        "CONTAINER_REGISTRY_TOKEN"
        "NOTIFICATION_WEBHOOK_URL"
    )
    
    log_info "Repository secrets to be configured:"
    for secret in "${secrets[@]}"; do
        log_info "  - $secret"
    done
    
    log_warning "Note: Repository secrets must be set manually through GitHub UI or with actual values"
    log_success "Repository secrets setup completed"
}

# Setup branch protection rules
setup_branch_protection() {
    log_info "Setting up branch protection rules..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would set up branch protection"
        return
    fi
    
    # Main branch protection
    log_info "Setting up protection for main branch..."
    gh api \
        --method PUT \
        -H "Accept: application/vnd.github+json" \
        "/repos/$GITHUB_ORG/$GITHUB_REPO/branches/main/protection" \
        --input - << EOF || log_warning "Failed to set main branch protection"
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["continuous-integration"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 2,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true
  },
  "restrictions": null
}
EOF
    
    # Staging branch protection
    log_info "Setting up protection for staging branch..."
    gh api \
        --method PUT \
        -H "Accept: application/vnd.github+json" \
        "/repos/$GITHUB_ORG/$GITHUB_REPO/branches/staging/protection" \
        --input - << EOF || log_warning "Failed to set staging branch protection"
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["continuous-integration"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true
  },
  "restrictions": null
}
EOF
    
    log_success "Branch protection setup completed"
}

# Generate environment documentation
generate_documentation() {
    log_info "Generating environment documentation..."
    
    local doc_file="$PROJECT_ROOT/DEPLOYMENT_ENVIRONMENTS.md"
    
    cat > "$doc_file" << EOF
# Deployment Environments

Generated on: $(date)

## Environment Overview

This repository is configured with three deployment environments:

### Development Environment
- **Name**: development
- **Purpose**: Feature development and initial testing
- **Approval**: None required
- **Branch**: dev, feature/*, bugfix/*
- **URL**: https://dev.sas-com.example.com

### Staging Environment
- **Name**: staging
- **Purpose**: Integration testing and UAT
- **Approval**: 1 reviewer required
- **Branch**: staging, release/*
- **URL**: https://staging.sas-com.example.com

### Production Environment
- **Name**: production
- **Purpose**: Live service delivery
- **Approval**: 2 reviewers + 5min wait timer
- **Branch**: main, hotfix/*
- **URL**: https://sas-com.example.com

## Environment Variables

Each environment has specific configuration through environment variables.
See the environment configuration files in \`.github/environments/\` for details.

## Secrets Management

Environment-specific secrets are managed through GitHub's environment secrets.
Repository-level secrets are used for common services like:

- Code coverage (Codecov)
- Security scanning (Snyk, Semgrep)
- Container registry access
- Notification services

## Deployment Workflows

- **Development**: Automatic deployment on push to dev branch
- **Staging**: Manual deployment with approval after dev testing
- **Production**: Manual deployment with multiple approvals and safety checks

## Emergency Procedures

For emergency rollbacks, use the emergency-rollback workflow with appropriate
emergency level (L1-L4) and target environment.

## Monitoring and Alerts

Each environment has monitoring configured with appropriate thresholds:
- Development: Basic monitoring, relaxed thresholds
- Staging: Enhanced monitoring, moderate thresholds  
- Production: Comprehensive monitoring, strict thresholds

For more details, see:
- [Environment Deployment Strategy](./ENVIRONMENT_DEPLOYMENT_STRATEGY.md)
- [Emergency Response Guide](./EMERGENCY_RESPONSE.md)
EOF
    
    log_success "Documentation generated: $doc_file"
}

# Main execution
main() {
    log_info "GitHub Environment Setup Script"
    log_info "Organization: $GITHUB_ORG"
    log_info "Repository: $GITHUB_REPO"
    log_info "Environment: $ENVIRONMENT"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN MODE - No changes will be made"
    fi
    
    # Check prerequisites
    check_prerequisites
    
    if [[ "$VERIFY_ONLY" == "true" ]]; then
        log_info "Verification mode - checking existing environments"
        
        if [[ "$ENVIRONMENT" == "all" ]]; then
            verify_environment "development"
            verify_environment "staging" 
            verify_environment "production"
        else
            case "$ENVIRONMENT" in
                "dev") verify_environment "development" ;;
                "staging") verify_environment "staging" ;;
                "prod") verify_environment "production" ;;
            esac
        fi
        
        log_success "Environment verification completed"
        return
    fi
    
    # Setup environments
    case "$ENVIRONMENT" in
        "dev")
            setup_dev_environment
            ;;
        "staging")
            setup_staging_environment
            ;;
        "prod")
            setup_production_environment
            ;;
        "all")
            setup_dev_environment
            setup_staging_environment
            setup_production_environment
            setup_repository_secrets
            setup_branch_protection
            generate_documentation
            ;;
    esac
    
    log_success "Environment setup completed successfully!"
    
    if [[ "$ENVIRONMENT" == "all" || "$ENVIRONMENT" == "prod" ]]; then
        log_info ""
        log_info "Next steps:"
        log_info "1. Set actual values for repository and environment secrets"
        log_info "2. Configure team reviewers for staging and production environments"
        log_info "3. Test deployment workflows with each environment"
        log_info "4. Review and customize environment protection rules as needed"
        log_info ""
        log_info "Documentation generated: DEPLOYMENT_ENVIRONMENTS.md"
    fi
}

# Execute main function
main "$@"