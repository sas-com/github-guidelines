#!/bin/bash

###############################################################################
# Evidence Collector - Comprehensive evidence collection for incident response
# SAS Corporation - GitHub Security Team
###############################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
EVIDENCE_BASE_DIR="/secure/forensics"
GITHUB_ORG="sas-com"
MAX_LOG_LINES=10000
PARALLEL_JOBS=4

# Function to print colored output
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to display usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Comprehensive evidence collection tool for security incident response.

OPTIONS:
    -i, --incident-id ID    Incident ID (required)
    -p, --priority LEVEL    Priority level (P0|P1|P2|P3)
    -t, --type TYPE         Evidence type to collect:
                           - all (default)
                           - github
                           - system
                           - network
                           - logs
                           - memory
    -r, --repos REPOS       Comma-separated list of repositories
    -u, --user USER         Specific user to investigate
    -d, --days DAYS         Number of days to look back (default: 7)
    -o, --output DIR        Output directory (default: /secure/forensics)
    -e, --encrypt           Encrypt collected evidence
    -c, --compress          Compress evidence archive
    -v, --verbose           Verbose output
    -h, --help              Display this help message

EXAMPLES:
    # Collect all evidence for a P0 incident
    $0 --incident-id INC-2025-001 --priority P0 --type all

    # Collect GitHub evidence for specific repositories
    $0 -i INC-2025-002 -t github -r "repo1,repo2"

    # Investigate specific user activity
    $0 -i INC-2025-003 -u suspicious_user -d 30

EOF
    exit 0
}

# Parse command line arguments
parse_arguments() {
    INCIDENT_ID=""
    PRIORITY="P2"
    EVIDENCE_TYPE="all"
    REPOS=""
    USER=""
    DAYS=7
    OUTPUT_DIR="${EVIDENCE_BASE_DIR}"
    ENCRYPT=false
    COMPRESS=true
    VERBOSE=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            -i|--incident-id)
                INCIDENT_ID="$2"
                shift 2
                ;;
            -p|--priority)
                PRIORITY="$2"
                shift 2
                ;;
            -t|--type)
                EVIDENCE_TYPE="$2"
                shift 2
                ;;
            -r|--repos)
                REPOS="$2"
                shift 2
                ;;
            -u|--user)
                USER="$2"
                shift 2
                ;;
            -d|--days)
                DAYS="$2"
                shift 2
                ;;
            -o|--output)
                OUTPUT_DIR="$2"
                shift 2
                ;;
            -e|--encrypt)
                ENCRYPT=true
                shift
                ;;
            -c|--compress)
                COMPRESS=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                usage
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                ;;
        esac
    done

    # Validate required arguments
    if [[ -z "${INCIDENT_ID}" ]]; then
        log_error "Incident ID is required"
        usage
    fi
}

# Initialize evidence collection
initialize_collection() {
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    EVIDENCE_DIR="${OUTPUT_DIR}/${INCIDENT_ID}/${TIMESTAMP}"
    
    log_info "Initializing evidence collection for incident ${INCIDENT_ID}"
    log_info "Evidence directory: ${EVIDENCE_DIR}"
    
    # Create directory structure
    mkdir -p "${EVIDENCE_DIR}"/{github,system,network,logs,memory,artifacts}
    
    # Create collection metadata
    cat > "${EVIDENCE_DIR}/collection_metadata.json" << EOF
{
    "incident_id": "${INCIDENT_ID}",
    "priority": "${PRIORITY}",
    "collection_started": "$(date -Iseconds)",
    "collector": "$(whoami)",
    "hostname": "$(hostname)",
    "evidence_type": "${EVIDENCE_TYPE}",
    "parameters": {
        "days_back": ${DAYS},
        "repos": "${REPOS}",
        "user": "${USER}"
    }
}
EOF
    
    log_success "Collection initialized"
}

# Collect GitHub evidence
collect_github_evidence() {
    log_info "Collecting GitHub evidence..."
    
    local github_dir="${EVIDENCE_DIR}/github"
    
    # Organization audit log
    if [[ "${PRIORITY}" == "P0" ]] || [[ "${PRIORITY}" == "P1" ]]; then
        log_info "Collecting organization audit log..."
        gh api \
            -H "Accept: application/vnd.github+json" \
            /orgs/${GITHUB_ORG}/audit-log \
            --paginate \
            > "${github_dir}/org_audit_log.json" 2>/dev/null || \
            log_warning "Failed to collect org audit log (may require additional permissions)"
    fi
    
    # Repository list
    log_info "Collecting repository list..."
    gh repo list ${GITHUB_ORG} \
        --json name,private,archived,createdAt,updatedAt,defaultBranch \
        --limit 1000 \
        > "${github_dir}/repositories.json"
    
    # Process specific repositories or all
    if [[ -n "${REPOS}" ]]; then
        IFS=',' read -ra REPO_ARRAY <<< "${REPOS}"
    else
        # Get all repositories if not specified
        REPO_ARRAY=($(gh repo list ${GITHUB_ORG} --json name -q '.[].name' --limit 100))
    fi
    
    # Collect evidence for each repository
    for repo in "${REPO_ARRAY[@]}"; do
        log_info "Processing repository: ${repo}"
        
        local repo_dir="${github_dir}/repos/${repo}"
        mkdir -p "${repo_dir}"
        
        # Repository metadata
        gh api /repos/${GITHUB_ORG}/${repo} \
            > "${repo_dir}/metadata.json" 2>/dev/null || true
        
        # Recent commits
        gh api /repos/${GITHUB_ORG}/${repo}/commits \
            --paginate \
            -F per_page=100 \
            -F since="$(date -d "${DAYS} days ago" -Iseconds)" \
            > "${repo_dir}/recent_commits.json" 2>/dev/null || true
        
        # Pull requests
        gh pr list \
            --repo ${GITHUB_ORG}/${repo} \
            --state all \
            --json number,title,author,createdAt,closedAt,state \
            --limit 100 \
            > "${repo_dir}/pull_requests.json" 2>/dev/null || true
        
        # Security alerts
        gh api /repos/${GITHUB_ORG}/${repo}/vulnerability-alerts \
            > "${repo_dir}/vulnerability_alerts.json" 2>/dev/null || true
        
        # Webhooks (if accessible)
        gh api /repos/${GITHUB_ORG}/${repo}/hooks \
            > "${repo_dir}/webhooks.json" 2>/dev/null || true
        
        # Branch protection rules
        for branch in $(gh api /repos/${GITHUB_ORG}/${repo}/branches --jq '.[].name' 2>/dev/null || echo "main"); do
            gh api /repos/${GITHUB_ORG}/${repo}/branches/${branch}/protection \
                > "${repo_dir}/branch_protection_${branch}.json" 2>/dev/null || true
        done
    done
    
    # User-specific investigation
    if [[ -n "${USER}" ]]; then
        log_info "Investigating user: ${USER}"
        
        local user_dir="${github_dir}/users/${USER}"
        mkdir -p "${user_dir}"
        
        # User profile
        gh api /users/${USER} > "${user_dir}/profile.json" 2>/dev/null || true
        
        # User events
        gh api /users/${USER}/events \
            --paginate \
            > "${user_dir}/events.json" 2>/dev/null || true
        
        # User's repositories
        gh api /users/${USER}/repos \
            --paginate \
            > "${user_dir}/repositories.json" 2>/dev/null || true
    fi
    
    # Collect GitHub Actions logs if P0/P1
    if [[ "${PRIORITY}" == "P0" ]] || [[ "${PRIORITY}" == "P1" ]]; then
        log_info "Collecting GitHub Actions logs..."
        
        local actions_dir="${github_dir}/actions"
        mkdir -p "${actions_dir}"
        
        for repo in "${REPO_ARRAY[@]}"; do
            gh run list \
                --repo ${GITHUB_ORG}/${repo} \
                --json databaseId,status,conclusion,createdAt \
                --limit 50 \
                > "${actions_dir}/${repo}_runs.json" 2>/dev/null || true
        done
    fi
    
    log_success "GitHub evidence collection completed"
}

# Collect system evidence
collect_system_evidence() {
    log_info "Collecting system evidence..."
    
    local system_dir="${EVIDENCE_DIR}/system"
    
    # System information
    cat > "${system_dir}/system_info.txt" << EOF
=== System Information ===
Date: $(date)
Hostname: $(hostname)
Kernel: $(uname -a)
Uptime: $(uptime)
EOF
    
    # Process list
    ps auxww > "${system_dir}/process_list.txt"
    
    # Network connections
    netstat -tulpn > "${system_dir}/network_connections.txt" 2>/dev/null || \
        ss -tulpn > "${system_dir}/network_connections.txt" 2>/dev/null || true
    
    # Open files
    lsof > "${system_dir}/open_files.txt" 2>/dev/null || true
    
    # Users and groups
    cat /etc/passwd > "${system_dir}/users.txt"
    cat /etc/group > "${system_dir}/groups.txt"
    who > "${system_dir}/logged_in_users.txt"
    last -n 100 > "${system_dir}/login_history.txt"
    
    # Environment variables
    env > "${system_dir}/environment.txt"
    
    # Cron jobs
    for user in $(cut -f1 -d: /etc/passwd); do
        crontab -u $user -l > "${system_dir}/cron_${user}.txt" 2>/dev/null || true
    done
    
    # Package list
    if command -v dpkg &> /dev/null; then
        dpkg -l > "${system_dir}/installed_packages_dpkg.txt"
    elif command -v rpm &> /dev/null; then
        rpm -qa > "${system_dir}/installed_packages_rpm.txt"
    fi
    
    # Docker containers (if applicable)
    if command -v docker &> /dev/null; then
        docker ps -a > "${system_dir}/docker_containers.txt" 2>/dev/null || true
        docker images > "${system_dir}/docker_images.txt" 2>/dev/null || true
    fi
    
    log_success "System evidence collection completed"
}

# Collect network evidence
collect_network_evidence() {
    log_info "Collecting network evidence..."
    
    local network_dir="${EVIDENCE_DIR}/network"
    
    # Network interfaces
    ip addr show > "${network_dir}/interfaces.txt" 2>/dev/null || \
        ifconfig -a > "${network_dir}/interfaces.txt" 2>/dev/null || true
    
    # Routing table
    ip route > "${network_dir}/routes.txt" 2>/dev/null || \
        route -n > "${network_dir}/routes.txt" 2>/dev/null || true
    
    # ARP cache
    arp -a > "${network_dir}/arp_cache.txt" 2>/dev/null || true
    
    # DNS configuration
    cat /etc/resolv.conf > "${network_dir}/dns_config.txt"
    cat /etc/hosts > "${network_dir}/hosts.txt"
    
    # Firewall rules
    iptables -L -n -v > "${network_dir}/iptables.txt" 2>/dev/null || true
    
    # Network statistics
    netstat -s > "${network_dir}/network_stats.txt" 2>/dev/null || true
    
    # Capture network traffic (if P0)
    if [[ "${PRIORITY}" == "P0" ]] && command -v tcpdump &> /dev/null; then
        log_info "Capturing network traffic (30 seconds)..."
        timeout 30 tcpdump -i any -w "${network_dir}/traffic_capture.pcap" 2>/dev/null || true
    fi
    
    log_success "Network evidence collection completed"
}

# Collect log files
collect_logs() {
    log_info "Collecting log files..."
    
    local logs_dir="${EVIDENCE_DIR}/logs"
    
    # System logs
    if [[ -d /var/log ]]; then
        # Key log files
        for logfile in syslog auth.log kern.log messages secure; do
            if [[ -f "/var/log/${logfile}" ]]; then
                tail -n ${MAX_LOG_LINES} "/var/log/${logfile}" > "${logs_dir}/${logfile}" 2>/dev/null || true
            fi
        done
        
        # Application logs
        if [[ -d /var/log/nginx ]]; then
            tail -n ${MAX_LOG_LINES} /var/log/nginx/access.log > "${logs_dir}/nginx_access.log" 2>/dev/null || true
            tail -n ${MAX_LOG_LINES} /var/log/nginx/error.log > "${logs_dir}/nginx_error.log" 2>/dev/null || true
        fi
        
        if [[ -d /var/log/apache2 ]]; then
            tail -n ${MAX_LOG_LINES} /var/log/apache2/access.log > "${logs_dir}/apache_access.log" 2>/dev/null || true
            tail -n ${MAX_LOG_LINES} /var/log/apache2/error.log > "${logs_dir}/apache_error.log" 2>/dev/null || true
        fi
    fi
    
    # Docker logs
    if command -v docker &> /dev/null; then
        for container in $(docker ps -q); do
            docker logs --tail ${MAX_LOG_LINES} $container > "${logs_dir}/docker_${container}.log" 2>/dev/null || true
        done
    fi
    
    # Journal logs (systemd)
    if command -v journalctl &> /dev/null; then
        journalctl --since "${DAYS} days ago" > "${logs_dir}/journal.log" 2>/dev/null || true
    fi
    
    log_success "Log collection completed"
}

# Collect memory evidence
collect_memory_evidence() {
    log_info "Collecting memory evidence..."
    
    local memory_dir="${EVIDENCE_DIR}/memory"
    
    # Memory information
    cat /proc/meminfo > "${memory_dir}/meminfo.txt" 2>/dev/null || true
    free -h > "${memory_dir}/free.txt" 2>/dev/null || true
    vmstat 1 5 > "${memory_dir}/vmstat.txt" 2>/dev/null || true
    
    # Process memory maps (for suspicious processes)
    if [[ "${PRIORITY}" == "P0" ]]; then
        log_warning "Full memory dump requires specialized tools and permissions"
        
        # Capture memory maps for key processes
        for pid in $(ps aux | grep -E "(ssh|bash|python|node)" | awk '{print $2}'); do
            if [[ -r /proc/$pid/maps ]]; then
                cat /proc/$pid/maps > "${memory_dir}/proc_${pid}_maps.txt" 2>/dev/null || true
            fi
        done
    fi
    
    log_success "Memory evidence collection completed"
}

# Calculate hashes for all collected files
calculate_hashes() {
    log_info "Calculating file hashes..."
    
    find "${EVIDENCE_DIR}" -type f -exec sha256sum {} \; > "${EVIDENCE_DIR}/SHA256SUMS.txt"
    
    log_success "Hash calculation completed"
}

# Compress evidence
compress_evidence() {
    if [[ "${COMPRESS}" == true ]]; then
        log_info "Compressing evidence..."
        
        local archive_name="${EVIDENCE_DIR}.tar.gz"
        tar czf "${archive_name}" -C "$(dirname ${EVIDENCE_DIR})" "$(basename ${EVIDENCE_DIR})"
        
        log_success "Evidence compressed to ${archive_name}"
        
        # Calculate hash of archive
        sha256sum "${archive_name}" > "${archive_name}.sha256"
    fi
}

# Encrypt evidence
encrypt_evidence() {
    if [[ "${ENCRYPT}" == true ]]; then
        log_info "Encrypting evidence..."
        
        local archive_name="${EVIDENCE_DIR}.tar.gz"
        
        if [[ -f "${archive_name}" ]]; then
            # Encrypt with GPG
            gpg --cipher-algo AES256 --symmetric --batch --passphrase-file /secure/.evidence_passphrase \
                "${archive_name}" 2>/dev/null || {
                log_warning "Encryption failed - GPG not configured properly"
                return 1
            }
            
            # Remove unencrypted archive
            rm -f "${archive_name}"
            
            log_success "Evidence encrypted to ${archive_name}.gpg"
        fi
    fi
}

# Generate collection report
generate_report() {
    log_info "Generating collection report..."
    
    local report_file="${EVIDENCE_DIR}/collection_report.md"
    
    cat > "${report_file}" << EOF
# Evidence Collection Report

## Incident Information
- **Incident ID**: ${INCIDENT_ID}
- **Priority**: ${PRIORITY}
- **Collection Date**: $(date)
- **Collector**: $(whoami)@$(hostname)

## Collection Parameters
- **Evidence Type**: ${EVIDENCE_TYPE}
- **Days Back**: ${DAYS}
- **Repositories**: ${REPOS:-"All accessible"}
- **User Investigation**: ${USER:-"None"}

## Evidence Collected

### GitHub Evidence
$(find ${EVIDENCE_DIR}/github -type f -name "*.json" | wc -l) files collected
- Organization audit logs
- Repository metadata and events
- Security alerts and webhooks
- User activity logs

### System Evidence
$(find ${EVIDENCE_DIR}/system -type f | wc -l) files collected
- System information
- Process and network data
- User and authentication logs

### Network Evidence
$(find ${EVIDENCE_DIR}/network -type f | wc -l) files collected
- Network configuration
- Connection information
- Traffic captures (if applicable)

### Log Files
$(find ${EVIDENCE_DIR}/logs -type f | wc -l) files collected
- System logs
- Application logs
- Security logs

## File Integrity
SHA256 checksums have been calculated and stored in SHA256SUMS.txt

## Storage Location
${EVIDENCE_DIR}

## Notes
- Collection completed at $(date)
- Total size: $(du -sh ${EVIDENCE_DIR} | cut -f1)
- Files collected: $(find ${EVIDENCE_DIR} -type f | wc -l)

---
*This report was automatically generated by the Evidence Collector tool.*
EOF
    
    log_success "Collection report generated"
}

# Main execution
main() {
    parse_arguments "$@"
    
    # Check required tools
    command -v gh &> /dev/null || {
        log_error "GitHub CLI (gh) is required but not installed"
        exit 1
    }
    
    # Initialize collection
    initialize_collection
    
    # Collect evidence based on type
    case "${EVIDENCE_TYPE}" in
        all)
            collect_github_evidence
            collect_system_evidence
            collect_network_evidence
            collect_logs
            collect_memory_evidence
            ;;
        github)
            collect_github_evidence
            ;;
        system)
            collect_system_evidence
            ;;
        network)
            collect_network_evidence
            ;;
        logs)
            collect_logs
            ;;
        memory)
            collect_memory_evidence
            ;;
        *)
            log_error "Unknown evidence type: ${EVIDENCE_TYPE}"
            exit 1
            ;;
    esac
    
    # Post-processing
    calculate_hashes
    compress_evidence
    encrypt_evidence
    generate_report
    
    # Update collection metadata
    cat >> "${EVIDENCE_DIR}/collection_metadata.json" << EOF
    ,
    "collection_completed": "$(date -Iseconds)",
    "total_files": $(find ${EVIDENCE_DIR} -type f | wc -l),
    "total_size": "$(du -sh ${EVIDENCE_DIR} | cut -f1)"
}
EOF
    
    log_success "Evidence collection completed successfully!"
    log_info "Evidence location: ${EVIDENCE_DIR}"
}

# Run main function
main "$@"