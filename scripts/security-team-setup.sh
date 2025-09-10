#!/bin/bash
# Security Team Environment Setup Script
# エス・エー・エス株式会社 - セキュリティチーム用環境構築スクリプト

set -e

echo "====================================="
echo "Security Team Environment Setup"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to check command existence
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Security warning
echo -e "${RED}⚠️  SECURITY NOTICE ⚠️${NC}"
echo "This script installs security testing tools."
echo "Use these tools only on authorized systems."
echo "Unauthorized access or testing is illegal."
read -p "Do you understand and agree? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Setup cancelled."
    exit 1
fi

echo ""
echo "🔐 Installing Security Analysis Tools..."
echo "========================================"

# Update package manager
sudo apt-get update -qq

# Install basic security tools
sudo apt-get install -y -qq \
    nmap \
    netcat \
    tcpdump \
    wireshark \
    john \
    hashcat \
    aircrack-ng \
    hydra \
    nikto \
    dirb \
    sqlmap \
    metasploit-framework \
    burpsuite

# Install Python security tools
echo -e "${BLUE}Installing Python security tools...${NC}"
pip3 install --user \
    bandit \
    safety \
    semgrep \
    detect-secrets \
    truffleHog3 \
    checkov \
    prowler \
    scapy \
    impacket

# Install Ruby security tools
echo -e "${BLUE}Installing Ruby security tools...${NC}"
if command_exists gem; then
    gem install \
        brakeman \
        bundler-audit
fi

# Install Node.js security tools
echo -e "${BLUE}Installing Node.js security tools...${NC}"
if command_exists npm; then
    npm install -g \
        snyk \
        retire \
        eslint-plugin-security \
        npm-audit-resolver
fi

# Install Go security tools
echo -e "${BLUE}Installing Go security tools...${NC}"
if command_exists go; then
    go install github.com/securego/gosec/v2/cmd/gosec@latest
    go install github.com/aquasecurity/trivy/cmd/trivy@latest
    go install github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest
    go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
fi

# Create security scripts directory
echo ""
echo "📝 Creating Security Scripts..."
echo "==============================="

mkdir -p ~/security-scripts/{scanning,incident-response,forensics,reporting}

# Vulnerability scanning script
cat > ~/security-scripts/scanning/vuln-scan.sh << 'EOF'
#!/bin/bash
# Comprehensive Vulnerability Scanning Script

TARGET=$1
OUTPUT_DIR="./scan-results-$(date +%Y%m%d-%H%M%S)"

if [ -z "$TARGET" ]; then
    echo "Usage: $0 <target>"
    exit 1
fi

echo "Starting vulnerability scan for: $TARGET"
mkdir -p $OUTPUT_DIR

# Network scan
echo "[+] Running network scan..."
nmap -sV -sC -O -A -p- $TARGET -oA $OUTPUT_DIR/nmap-scan

# Web vulnerability scan
if [[ $TARGET =~ ^https?:// ]]; then
    echo "[+] Running web vulnerability scan..."
    nikto -h $TARGET -output $OUTPUT_DIR/nikto-scan.txt
    dirb $TARGET -o $OUTPUT_DIR/dirb-scan.txt
    
    # SQL injection test (be careful!)
    echo "[+] Testing for SQL injection..."
    sqlmap -u $TARGET --batch --random-agent --output-dir=$OUTPUT_DIR/sqlmap
fi

# SSL/TLS scan
echo "[+] Running SSL/TLS scan..."
testssl.sh $TARGET > $OUTPUT_DIR/ssl-scan.txt

# Generate report
echo "[+] Generating report..."
cat > $OUTPUT_DIR/report.md << REPORT
# Vulnerability Scan Report
**Target**: $TARGET
**Date**: $(date)

## Network Scan Results
$(cat $OUTPUT_DIR/nmap-scan.nmap | head -50)

## Web Vulnerabilities
$(cat $OUTPUT_DIR/nikto-scan.txt | head -50)

## Recommendations
- Review all findings
- Prioritize based on CVSS scores
- Implement remediation plan
REPORT

echo "Scan complete. Results in: $OUTPUT_DIR"
EOF
chmod +x ~/security-scripts/scanning/vuln-scan.sh

# Incident response script
cat > ~/security-scripts/incident-response/respond.sh << 'EOF'
#!/bin/bash
# Incident Response Script

INCIDENT_ID=$(date +%Y%m%d-%H%M%S)
INCIDENT_DIR="/var/incident/$INCIDENT_ID"

echo "=== INCIDENT RESPONSE INITIATED ==="
echo "Incident ID: $INCIDENT_ID"

# Create incident directory
sudo mkdir -p $INCIDENT_DIR
cd $INCIDENT_DIR

# Step 1: Isolate
echo "[1/6] Isolating system..."
read -p "Isolate network? (y/n): " isolate
if [ "$isolate" = "y" ]; then
    sudo iptables -P INPUT DROP
    sudo iptables -P OUTPUT DROP
    echo "Network isolated."
fi

# Step 2: Preserve evidence
echo "[2/6] Preserving evidence..."
# Memory dump
sudo cat /proc/kcore > memory.dump 2>/dev/null || echo "Memory dump failed"
# Process list
ps auxww > processes.txt
# Network connections
netstat -plant > connections.txt
# Open files
lsof > open_files.txt
# System logs
sudo tar czf logs.tar.gz /var/log/

# Step 3: Identify
echo "[3/6] Identifying threat..."
# Look for suspicious processes
ps aux | awk '{if($3 > 80.0) print $0}' > suspicious_processes.txt
# Check for rootkits
sudo chkrootkit > chkrootkit.txt 2>&1
sudo rkhunter --check --skip-keypress > rkhunter.txt 2>&1

# Step 4: Contain
echo "[4/6] Containing threat..."
# Kill suspicious processes
read -p "Kill suspicious processes? (y/n): " kill_proc
if [ "$kill_proc" = "y" ]; then
    # Implementation would go here
    echo "Manual intervention required"
fi

# Step 5: Eradicate
echo "[5/6] Eradicating threat..."
echo "Manual eradication required based on findings"

# Step 6: Recover
echo "[6/6] Recovery phase..."
echo "Review logs and implement recovery plan"

echo "=== INITIAL RESPONSE COMPLETE ==="
echo "Evidence collected in: $INCIDENT_DIR"
echo "Next steps: Review evidence and complete investigation"
EOF
chmod +x ~/security-scripts/incident-response/respond.sh

# Forensics collection script
cat > ~/security-scripts/forensics/collect-evidence.sh << 'EOF'
#!/bin/bash
# Digital Forensics Evidence Collection

CASE_ID=$1
EVIDENCE_DIR="/forensics/$CASE_ID-$(date +%Y%m%d-%H%M%S)"

if [ -z "$CASE_ID" ]; then
    echo "Usage: $0 <case-id>"
    exit 1
fi

echo "Starting evidence collection for case: $CASE_ID"
sudo mkdir -p $EVIDENCE_DIR
cd $EVIDENCE_DIR

# System information
echo "[+] Collecting system information..."
uname -a > system_info.txt
date > collection_timestamp.txt
uptime >> system_info.txt
df -h > disk_usage.txt
free -m > memory_usage.txt

# User information
echo "[+] Collecting user information..."
w > logged_in_users.txt
last -n 100 > login_history.txt
sudo cat /etc/passwd > users.txt
sudo cat /etc/shadow > shadow.txt
sudo lastlog > lastlog.txt

# Process information
echo "[+] Collecting process information..."
ps auxww > processes_full.txt
pstree -p > process_tree.txt
sudo lsof > open_files.txt

# Network information
echo "[+] Collecting network information..."
netstat -plant > network_connections.txt
arp -a > arp_cache.txt
ip route > routing_table.txt
sudo iptables -L -n -v > firewall_rules.txt
ss -tulpn > socket_stats.txt

# File system timeline
echo "[+] Creating filesystem timeline..."
find / -type f -printf "%T+ %p\n" 2>/dev/null | sort > filesystem_timeline.txt

# Hash critical files
echo "[+] Hashing critical system files..."
find /bin /sbin /usr/bin /usr/sbin -type f -exec sha256sum {} \; > system_binaries_hash.txt

# Collect logs
echo "[+] Collecting system logs..."
sudo tar czf logs.tar.gz /var/log/

# Memory dump (if possible)
echo "[+] Attempting memory dump..."
sudo dd if=/proc/kcore of=memory.img bs=1M count=1024 2>/dev/null || echo "Memory dump failed"

# Create evidence manifest
cat > EVIDENCE_MANIFEST.txt << MANIFEST
Evidence Collection Report
==========================
Case ID: $CASE_ID
Collection Date: $(date)
Collector: $(whoami)
System: $(hostname)

Files Collected:
$(ls -la)

SHA256 Checksums:
$(sha256sum *)
MANIFEST

echo "Evidence collection complete: $EVIDENCE_DIR"
EOF
chmod +x ~/security-scripts/forensics/collect-evidence.sh

# Security automation script
cat > ~/security-scripts/security-check.sh << 'EOF'
#!/bin/bash
# Daily Security Check Script

echo "=== Daily Security Check ==="
echo "Date: $(date)"
echo ""

# Check for suspicious users
echo "Checking for new users..."
if [ -f /tmp/last_users ]; then
    diff /tmp/last_users /etc/passwd | grep "^>"
fi
cp /etc/passwd /tmp/last_users

# Check for listening ports
echo "Checking for new listening ports..."
if [ -f /tmp/last_ports ]; then
    diff /tmp/last_ports <(netstat -tlpn 2>/dev/null)
fi
netstat -tlpn 2>/dev/null > /tmp/last_ports

# Check for failed login attempts
echo "Failed login attempts (last 24h):"
sudo grep "Failed password" /var/log/auth.log | tail -10

# Check for sudo usage
echo "Recent sudo usage:"
sudo grep sudo /var/log/auth.log | tail -10

# Check for large files (potential data exfiltration)
echo "Large files created in last 24h:"
find / -type f -size +100M -mtime -1 2>/dev/null | head -10

# Check installed packages
echo "Recently installed packages:"
grep " install " /var/log/dpkg.log | tail -10

# Security updates
echo "Available security updates:"
apt list --upgradable 2>/dev/null | grep -i security

echo ""
echo "=== Security Check Complete ==="
EOF
chmod +x ~/security-scripts/security-check.sh

# Create YARA rules directory
echo ""
echo "📋 Setting up YARA Rules..."
echo "=========================="

mkdir -p ~/yara-rules
cat > ~/yara-rules/malware_detection.yar << 'EOF'
rule Suspicious_Strings
{
    meta:
        description = "Detects suspicious strings commonly found in malware"
        author = "Security Team"
        date = "2025-09-11"
    
    strings:
        $a = "cmd.exe" nocase
        $b = "powershell.exe" nocase
        $c = "/etc/passwd"
        $d = "/etc/shadow"
        $e = "wget http" nocase
        $f = "curl http" nocase
        $g = "nc -e" nocase
        
    condition:
        2 of them
}

rule Crypto_Miner
{
    meta:
        description = "Detects potential cryptocurrency miners"
    
    strings:
        $a = "stratum+tcp://"
        $b = "xmrig"
        $c = "monero"
        $d = "cryptonight"
        
    condition:
        any of them
}
EOF

# Create security monitoring dashboard
echo ""
echo "📊 Creating Security Dashboard..."
echo "================================"

cat > ~/security-scripts/dashboard.sh << 'EOF'
#!/bin/bash
# Security Monitoring Dashboard

while true; do
    clear
    echo "==================================="
    echo "   SECURITY MONITORING DASHBOARD"
    echo "==================================="
    echo "Time: $(date)"
    echo ""
    
    echo "[SYSTEM STATUS]"
    echo "Uptime: $(uptime -p)"
    echo "Load: $(uptime | awk -F'load average:' '{print $2}')"
    echo ""
    
    echo "[NETWORK ACTIVITY]"
    echo "Active connections: $(netstat -ant | grep ESTABLISHED | wc -l)"
    echo "Listening ports: $(netstat -tlpn 2>/dev/null | grep -c LISTEN)"
    echo ""
    
    echo "[AUTHENTICATION]"
    echo "Logged in users: $(who | wc -l)"
    echo "Failed logins (last hour): $(sudo grep "Failed password" /var/log/auth.log | grep "$(date '+%b %d %H')" | wc -l)"
    echo ""
    
    echo "[PROCESSES]"
    echo "Total processes: $(ps aux | wc -l)"
    echo "High CPU processes:"
    ps aux | sort -nrk 3,3 | head -3 | awk '{print $11, $3"%"}'
    echo ""
    
    echo "[ALERTS]"
    # Check for various security conditions
    if [ $(netstat -ant | grep -c ":4444") -gt 0 ]; then
        echo "⚠️  WARNING: Port 4444 detected (common backdoor)"
    fi
    if [ $(ps aux | grep -c "nc -l") -gt 1 ]; then
        echo "⚠️  WARNING: Netcat listener detected"
    fi
    
    echo ""
    echo "Press Ctrl+C to exit"
    sleep 5
done
EOF
chmod +x ~/security-scripts/dashboard.sh

# Create aliases for security team
echo ""
echo "⚙️  Setting up Security Aliases..."
echo "================================="

cat >> ~/.bashrc << 'EOF'

# Security Team Aliases
alias scan='~/security-scripts/scanning/vuln-scan.sh'
alias respond='~/security-scripts/incident-response/respond.sh'
alias forensics='~/security-scripts/forensics/collect-evidence.sh'
alias seccheck='~/security-scripts/security-check.sh'
alias secdash='~/security-scripts/dashboard.sh'

# Quick security commands
alias ports='netstat -tulpn'
alias connections='netstat -ant'
alias processes='ps auxww --forest'
alias listening='lsof -i -P -n | grep LISTEN'
alias established='lsof -i -P -n | grep ESTABLISHED'
alias failedlogins='sudo grep "Failed password" /var/log/auth.log | tail -20'
alias sudolog='sudo grep sudo /var/log/auth.log | tail -20'

# Network analysis
alias tcpdump='sudo tcpdump -i any -n'
alias httptraffic='sudo tcpdump -i any -n -A -s 0 "tcp port 80"'
alias httpstraffic='sudo tcpdump -i any -n -A -s 0 "tcp port 443"'
alias dnstraffic='sudo tcpdump -i any -n "port 53"'

# File analysis
hashfile() { sha256sum "$1" | tee "$1.sha256"; }
strings() { command strings "$1" | less; }
entropy() { ent "$1"; }

# Process analysis
strace() { command strace -f -e trace=network,file "$@"; }
ltrace() { command ltrace -f "$@"; }

# Log analysis
authlog() { sudo tail -f /var/log/auth.log; }
syslog() { sudo tail -f /var/log/syslog; }
kernlog() { sudo dmesg -wT; }

# Quick security checks
checkrootkit() { sudo chkrootkit; }
rkhunter() { sudo rkhunter --check --skip-keypress; }
lynis() { sudo lynis audit system; }
EOF

# Create incident response templates
echo ""
echo "📄 Creating Incident Response Templates..."
echo "========================================"

mkdir -p ~/security-templates
cat > ~/security-templates/incident-report.md << 'EOF'
# Incident Report

## Incident Details
- **Incident ID**: INC-YYYYMMDD-XXX
- **Date/Time Detected**: 
- **Date/Time Reported**: 
- **Reporter**: 
- **Severity**: [P1/P2/P3/P4]
- **Status**: [Open/Investigating/Contained/Resolved]

## Executive Summary
[Brief description of the incident and its impact]

## Timeline
- **HH:MM** - Event description
- **HH:MM** - Event description

## Technical Details
### Attack Vector
[Description of how the attack occurred]

### Affected Systems
- System 1
- System 2

### Indicators of Compromise (IoCs)
- IP Addresses:
- Domain Names:
- File Hashes:
- Other:

## Response Actions
1. Action taken
2. Action taken

## Lessons Learned
- What went well
- What could be improved

## Recommendations
1. Recommendation
2. Recommendation

## Appendices
- Log files
- Screenshots
- Other evidence
EOF

# Final setup message
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Security Environment Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${RED}⚠️  IMPORTANT SECURITY REMINDERS ⚠️${NC}"
echo "1. Use security tools only on authorized systems"
echo "2. Always obtain written permission before testing"
echo "3. Document all security activities"
echo "4. Follow incident response procedures"
echo "5. Protect sensitive information"
echo ""
echo "Useful commands:"
echo "  scan       - Run vulnerability scan"
echo "  respond    - Start incident response"
echo "  forensics  - Collect forensic evidence"
echo "  seccheck   - Run security check"
echo "  secdash    - Launch security dashboard"
echo ""
echo "Key directories:"
echo "  ~/security-scripts/     - Security automation scripts"
echo "  ~/yara-rules/          - YARA detection rules"
echo "  ~/security-templates/  - Report templates"
echo ""
echo "Stay vigilant! 🛡️"