#!/bin/bash
# Infrastructure/DevOps Team Environment Setup Script
# エス・エー・エス株式会社 - インフラチーム用環境構築スクリプト

set -e

echo "============================================"
echo "Infrastructure/DevOps Team Environment Setup"
echo "============================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check command existence
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install tool with verification
install_tool() {
    local tool_name=$1
    local install_cmd=$2
    local verify_cmd=${3:-$1}
    
    if command_exists "$verify_cmd"; then
        echo -e "${GREEN}✓ $tool_name is already installed${NC}"
    else
        echo -e "${YELLOW}Installing $tool_name...${NC}"
        eval "$install_cmd"
        if command_exists "$verify_cmd"; then
            echo -e "${GREEN}✓ $tool_name installed successfully${NC}"
        else
            echo -e "${RED}✗ Failed to install $tool_name${NC}"
            return 1
        fi
    fi
}

echo ""
echo "🔧 Installing Infrastructure Tools..."
echo "===================================="

# Update package manager
sudo apt-get update -qq

# Install basic tools
sudo apt-get install -y -qq \
    curl \
    wget \
    unzip \
    jq \
    htop \
    net-tools \
    dnsutils \
    telnet \
    vim \
    tmux

# Install AWS CLI v2
echo -e "${BLUE}Installing AWS CLI v2...${NC}"
if ! command_exists aws; then
    curl -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"
    unzip -q /tmp/awscliv2.zip -d /tmp/
    sudo /tmp/aws/install
    rm -rf /tmp/aws*
fi

# Install Terraform
echo -e "${BLUE}Installing Terraform...${NC}"
if ! command_exists terraform; then
    wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg >/dev/null
    echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
    sudo apt-get update -qq && sudo apt-get install -y terraform
fi

# Install kubectl
echo -e "${BLUE}Installing kubectl...${NC}"
if ! command_exists kubectl; then
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
    sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
    rm kubectl
fi

# Install Helm
echo -e "${BLUE}Installing Helm...${NC}"
if ! command_exists helm; then
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi

# Install Docker
echo -e "${BLUE}Installing Docker...${NC}"
if ! command_exists docker; then
    curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
    sudo sh /tmp/get-docker.sh
    sudo usermod -aG docker $USER
    rm /tmp/get-docker.sh
fi

# Install Docker Compose
echo -e "${BLUE}Installing Docker Compose...${NC}"
if ! command_exists docker-compose; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Install Ansible
echo -e "${BLUE}Installing Ansible...${NC}"
if ! command_exists ansible; then
    sudo apt-get install -y software-properties-common
    sudo add-apt-repository --yes --update ppa:ansible/ansible
    sudo apt-get install -y ansible
fi

# Install monitoring tools
echo ""
echo "📊 Installing Monitoring Tools..."
echo "================================"

# Prometheus
mkdir -p ~/monitoring/prometheus
cat > ~/monitoring/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']
EOF

# Grafana datasources
mkdir -p ~/monitoring/grafana/provisioning/datasources
cat > ~/monitoring/grafana/provisioning/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

# Create infrastructure scripts
echo ""
echo "📝 Creating Infrastructure Scripts..."
echo "===================================="

mkdir -p ~/infra-scripts

# Health check script
cat > ~/infra-scripts/health-check.sh << 'EOF'
#!/bin/bash
# Infrastructure Health Check Script

echo "=== Infrastructure Health Check ==="
echo "Time: $(date)"
echo ""

# Check Docker
echo -n "Docker: "
if systemctl is-active --quiet docker; then
    echo "✓ Running"
    docker version --format 'Version: {{.Server.Version}}'
else
    echo "✗ Not running"
fi

# Check Kubernetes (if configured)
echo -n "Kubernetes: "
if kubectl cluster-info &>/dev/null; then
    echo "✓ Connected"
    kubectl get nodes --no-headers | wc -l | xargs echo "Nodes:"
else
    echo "⚠ Not configured or not reachable"
fi

# Check AWS
echo -n "AWS CLI: "
if aws sts get-caller-identity &>/dev/null; then
    echo "✓ Authenticated"
    aws sts get-caller-identity --query Account --output text | xargs echo "Account:"
else
    echo "⚠ Not authenticated"
fi

# Check Terraform
echo -n "Terraform: "
if command -v terraform &>/dev/null; then
    terraform version | head -n1 | cut -d' ' -f2
else
    echo "✗ Not installed"
fi

# System resources
echo ""
echo "=== System Resources ==="
echo "CPU Load: $(uptime | awk -F'load average:' '{print $2}')"
echo "Memory: $(free -h | grep '^Mem' | awk '{print $3 "/" $2}')"
echo "Disk: $(df -h / | tail -1 | awk '{print $3 "/" $2 " (" $5 ")"}')"

echo ""
echo "=== Health Check Complete ==="
EOF
chmod +x ~/infra-scripts/health-check.sh

# Deployment script
cat > ~/infra-scripts/deploy.sh << 'EOF'
#!/bin/bash
# Automated Deployment Script

set -e

ENVIRONMENT=${1:-dev}
SERVICE=${2:-all}
VERSION=${3:-latest}

echo "========================================="
echo "Deploying to: $ENVIRONMENT"
echo "Service: $SERVICE"
echo "Version: $VERSION"
echo "========================================="

# Pre-deployment checks
echo "Running pre-deployment checks..."
./health-check.sh

# Backup current state
echo "Backing up current state..."
kubectl get all -A -o yaml > backup-$(date +%Y%m%d-%H%M%S).yaml

# Deploy based on environment
case $ENVIRONMENT in
    dev)
        echo "Deploying to development..."
        kubectl apply -f manifests/dev/
        ;;
    staging)
        echo "Deploying to staging..."
        kubectl apply -f manifests/staging/
        ;;
    production)
        echo "Deploying to production..."
        read -p "Are you sure you want to deploy to PRODUCTION? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            kubectl apply -f manifests/production/
        else
            echo "Production deployment cancelled."
            exit 1
        fi
        ;;
    *)
        echo "Unknown environment: $ENVIRONMENT"
        exit 1
        ;;
esac

# Wait for rollout
echo "Waiting for rollout to complete..."
kubectl rollout status deployment/$SERVICE -n $ENVIRONMENT

# Post-deployment verification
echo "Running post-deployment verification..."
kubectl get pods -n $ENVIRONMENT
kubectl get services -n $ENVIRONMENT

echo "Deployment completed successfully!"
EOF
chmod +x ~/infra-scripts/deploy.sh

# Monitoring setup script
cat > ~/infra-scripts/setup-monitoring.sh << 'EOF'
#!/bin/bash
# Setup Monitoring Stack

set -e

echo "Setting up monitoring stack..."

# Create monitoring namespace
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Deploy Prometheus
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
    --namespace monitoring \
    --set grafana.adminPassword=admin

# Deploy Loki for log aggregation
helm repo add grafana https://grafana.github.io/helm-charts
helm upgrade --install loki grafana/loki-stack \
    --namespace monitoring

echo "Monitoring stack deployed!"
echo "Access Grafana at: http://localhost:3000"
echo "Username: admin"
echo "Password: admin (please change immediately)"
EOF
chmod +x ~/infra-scripts/setup-monitoring.sh

# Create Terraform modules
echo ""
echo "🏗️  Creating Terraform Modules..."
echo "================================"

mkdir -p ~/terraform-modules/{vpc,eks,rds,s3}

# VPC module
cat > ~/terraform-modules/vpc/main.tf << 'EOF'
variable "cidr_block" {
  description = "CIDR block for VPC"
  default     = "10.0.0.0/16"
}

variable "environment" {
  description = "Environment name"
}

resource "aws_vpc" "main" {
  cidr_block           = var.cidr_block
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "${var.environment}-vpc"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

output "vpc_id" {
  value = aws_vpc.main.id
}
EOF

# Create aliases for infrastructure team
echo ""
echo "⚙️  Setting up Infrastructure Aliases..."
echo "======================================="

cat >> ~/.bashrc << 'EOF'

# Infrastructure Team Aliases
alias tf='terraform'
alias tfi='terraform init'
alias tfp='terraform plan'
alias tfa='terraform apply'
alias tfd='terraform destroy'
alias tfv='terraform validate'

# Kubernetes aliases
alias k='kubectl'
alias kg='kubectl get'
alias kd='kubectl describe'
alias kl='kubectl logs'
alias ke='kubectl exec -it'
alias kns='kubectl config set-context --current --namespace'

# Docker aliases
alias d='docker'
alias dc='docker-compose'
alias dps='docker ps'
alias dpsa='docker ps -a'
alias di='docker images'
alias dex='docker exec -it'
alias dlog='docker logs -f'

# AWS aliases
alias awsid='aws sts get-caller-identity'
alias awsregion='aws configure get region'
alias ec2ls='aws ec2 describe-instances --query "Reservations[*].Instances[*].[InstanceId,State.Name,Tags[?Key==`Name`].Value|[0]]" --output table'

# Helm aliases
alias h='helm'
alias hl='helm list'
alias hi='helm install'
alias hu='helm upgrade'
alias hd='helm delete'

# Quick functions
kpods() { kubectl get pods ${1:+-n $1}; }
klogs() { kubectl logs -f $(kubectl get pods ${2:+-n $2} -o jsonpath="{.items[0].metadata.name}") ${2:+-n $2}; }
kexec() { kubectl exec -it $(kubectl get pods ${2:+-n $2} -o jsonpath="{.items[0].metadata.name}") ${2:+-n $2} -- ${1:-bash}; }

# Infrastructure scripts
alias health='~/infra-scripts/health-check.sh'
alias deploy='~/infra-scripts/deploy.sh'
alias monitor='~/infra-scripts/setup-monitoring.sh'
EOF

# Create kubectl config
mkdir -p ~/.kube
touch ~/.kube/config

# Setup completion
echo ""
echo "🔧 Setting up Command Completion..."
echo "==================================="

# Kubectl completion
echo 'source <(kubectl completion bash)' >> ~/.bashrc
echo 'complete -F __start_kubectl k' >> ~/.bashrc

# Helm completion
echo 'source <(helm completion bash)' >> ~/.bashrc

# Terraform completion
echo 'complete -C /usr/bin/terraform terraform' >> ~/.bashrc
echo 'complete -C /usr/bin/terraform tf' >> ~/.bashrc

# Final message
echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}✅ Infrastructure Environment Setup Complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Next steps:"
echo "1. Restart terminal or run: source ~/.bashrc"
echo "2. Configure AWS credentials: aws configure"
echo "3. Configure kubectl: kubectl config set-context"
echo "4. Login to container registries"
echo ""
echo "Useful commands:"
echo "  health     - Run infrastructure health check"
echo "  deploy     - Deploy to environment"
echo "  monitor    - Setup monitoring stack"
echo "  k          - kubectl shorthand"
echo "  tf         - terraform shorthand"
echo ""
echo "Key directories:"
echo "  ~/infra-scripts/      - Infrastructure automation scripts"
echo "  ~/terraform-modules/  - Reusable Terraform modules"
echo "  ~/monitoring/         - Monitoring configurations"
echo ""
echo "Infrastructure as Code! 🚀"