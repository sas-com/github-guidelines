#!/bin/bash
# Monitoring and Metrics Setup Script
# エス・エー・エス株式会社 - GitHub運用ガイドライン

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONFIG_DIR="$SCRIPT_DIR/../configs"
LOG_FILE="${SCRIPT_DIR}/monitoring-setup.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
Monitoring and Metrics Setup Script

Usage: $0 [OPTIONS]

OPTIONS:
    -e, --environment ENV    Target environment (dev|staging|prod|all)
    -m, --monitoring TYPE    Monitoring type (basic|intermediate|enterprise|all)
    -p, --provider PROVIDER  Monitoring provider (prometheus|elastic|datadog|newrelic)
    -c, --configure          Configure monitoring rules and alerts
    -d, --dashboard          Setup monitoring dashboards
    -v, --validate           Validate monitoring configuration
    --dry-run                Show what would be done without making changes
    -h, --help               Show this help message

EXAMPLES:
    $0 -e prod -m enterprise -p prometheus
    $0 -e staging --configure --dashboard
    $0 --validate --dry-run

MONITORING TYPES:
    basic        - Basic system and application monitoring
    intermediate - Enhanced monitoring with APM and custom metrics
    enterprise   - Comprehensive monitoring with security and compliance
    all          - Setup all monitoring types

SUPPORTED PROVIDERS:
    prometheus   - Prometheus + Grafana stack
    elastic      - Elastic Stack (ELK)
    datadog      - Datadog APM and monitoring
    newrelic     - New Relic monitoring platform

EOF
}

# Default values
ENVIRONMENT=""
MONITORING_TYPE="basic"
PROVIDER="prometheus"
CONFIGURE_RULES=false
SETUP_DASHBOARDS=false
VALIDATE_ONLY=false
DRY_RUN=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -m|--monitoring)
            MONITORING_TYPE="$2"
            shift 2
            ;;
        -p|--provider)
            PROVIDER="$2"
            shift 2
            ;;
        -c|--configure)
            CONFIGURE_RULES=true
            shift
            ;;
        -d|--dashboard)
            SETUP_DASHBOARDS=true
            shift
            ;;
        -v|--validate)
            VALIDATE_ONLY=true
            shift
            ;;
        --dry-run)
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
echo "Monitoring Setup - $(date)" > "$LOG_FILE"
log_info "Starting monitoring setup for environment: $ENVIRONMENT"
log_info "Monitoring type: $MONITORING_TYPE"
log_info "Provider: $PROVIDER"

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check required tools
    local required_tools=("curl" "jq" "yq")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool is not installed. Please install it first."
            return 1
        fi
    done
    
    # Check Docker (if needed)
    if [[ "$PROVIDER" == "prometheus" || "$PROVIDER" == "elastic" ]]; then
        if ! command -v docker &> /dev/null; then
            log_error "Docker is required for $PROVIDER but not installed."
            return 1
        fi
    fi
    
    # Check configuration files
    if [[ ! -f "$CONFIG_DIR/monitoring-config.yml" ]]; then
        log_error "Monitoring configuration file not found: $CONFIG_DIR/monitoring-config.yml"
        return 1
    fi
    
    log_success "Prerequisites check completed"
}

# Load configuration for environment
load_environment_config() {
    local env="$1"
    log_info "Loading configuration for environment: $env"
    
    # Extract environment-specific configuration
    yq eval ".environments.$env" "$CONFIG_DIR/monitoring-config.yml" > "/tmp/monitoring-$env.yml"
    
    # Load thresholds
    CPU_THRESHOLD=$(yq eval '.thresholds.cpu_usage' "/tmp/monitoring-$env.yml")
    MEMORY_THRESHOLD=$(yq eval '.thresholds.memory_usage' "/tmp/monitoring-$env.yml")
    RESPONSE_TIME_THRESHOLD=$(yq eval '.thresholds.response_time' "/tmp/monitoring-$env.yml")
    ERROR_RATE_THRESHOLD=$(yq eval '.thresholds.error_rate' "/tmp/monitoring-$env.yml")
    
    log_info "Configuration loaded for $env environment"
    log_info "  CPU Threshold: $CPU_THRESHOLD"
    log_info "  Memory Threshold: $MEMORY_THRESHOLD"
    log_info "  Response Time Threshold: $RESPONSE_TIME_THRESHOLD"
    log_info "  Error Rate Threshold: $ERROR_RATE_THRESHOLD"
}

# Setup Prometheus monitoring
setup_prometheus_monitoring() {
    local env="$1"
    log_info "Setting up Prometheus monitoring for $env environment"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would setup Prometheus for $env"
        return
    fi
    
    # Create prometheus configuration directory
    mkdir -p "$PROJECT_ROOT/monitoring/prometheus/$env"
    
    # Generate Prometheus configuration
    cat > "$PROJECT_ROOT/monitoring/prometheus/$env/prometheus.yml" << EOF
global:
  scrape_interval: 30s
  evaluation_interval: 30s
  external_labels:
    environment: '$env'
    cluster: 'sas-com'

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
  
  - job_name: 'application'
    static_configs:
      - targets: ['app:3000']
    metrics_path: '/metrics'
    scrape_interval: 15s
  
  - job_name: 'github-actions'
    static_configs:
      - targets: ['github-exporter:8080']
    scrape_interval: 60s
EOF
    
    # Generate alert rules
    generate_prometheus_alerts "$env"
    
    # Generate docker-compose for monitoring stack
    generate_monitoring_docker_compose "$env"
    
    log_success "Prometheus configuration generated for $env"
}

# Generate Prometheus alert rules
generate_prometheus_alerts() {
    local env="$1"
    log_info "Generating Prometheus alert rules for $env"
    
    # Load environment-specific thresholds
    load_environment_config "$env"
    
    cat > "$PROJECT_ROOT/monitoring/prometheus/$env/alert_rules.yml" << EOF
groups:
  - name: system_alerts
    rules:
      - alert: HighCPUUsage
        expr: cpu_usage_percent > ${CPU_THRESHOLD%\%}
        for: 5m
        labels:
          severity: warning
          environment: $env
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is {{ \$value }}% on {{ \$labels.instance }}"
      
      - alert: HighMemoryUsage
        expr: memory_usage_percent > ${MEMORY_THRESHOLD%\%}
        for: 5m
        labels:
          severity: warning
          environment: $env
        annotations:
          summary: "High memory usage detected"
          description: "Memory usage is {{ \$value }}% on {{ \$labels.instance }}"
      
      - alert: HighDiskUsage
        expr: disk_usage_percent > 85
        for: 1m
        labels:
          severity: critical
          environment: $env
        annotations:
          summary: "High disk usage detected"
          description: "Disk usage is {{ \$value }}% on {{ \$labels.instance }}"

  - name: application_alerts
    rules:
      - alert: HighResponseTime
        expr: http_request_duration_seconds{quantile="0.95"} > ${RESPONSE_TIME_THRESHOLD%ms} / 1000
        for: 3m
        labels:
          severity: warning
          environment: $env
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ \$value }}s"
      
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > ${ERROR_RATE_THRESHOLD%\%} / 100
        for: 2m
        labels:
          severity: critical
          environment: $env
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ \$value | humanizePercentage }}"
      
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
          environment: $env
        annotations:
          summary: "Service is down"
          description: "{{ \$labels.job }} service is down on {{ \$labels.instance }}"

  - name: deployment_alerts
    rules:
      - alert: DeploymentFailed
        expr: github_actions_workflow_run_conclusion{conclusion="failure"} == 1
        for: 0m
        labels:
          severity: high
          environment: $env
        annotations:
          summary: "Deployment failed"
          description: "GitHub Actions workflow {{ \$labels.workflow_name }} failed"
      
      - alert: LongRunningDeployment
        expr: github_actions_workflow_run_duration_seconds > 1800
        for: 0m
        labels:
          severity: warning
          environment: $env
        annotations:
          summary: "Long running deployment"
          description: "Deployment has been running for {{ \$value | humanizeDuration }}"
EOF
    
    log_success "Alert rules generated for $env"
}

# Generate Docker Compose for monitoring stack
generate_monitoring_docker_compose() {
    local env="$1"
    log_info "Generating Docker Compose for monitoring stack ($env)"
    
    cat > "$PROJECT_ROOT/monitoring/docker-compose.$env.yml" << EOF
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus-$env
    restart: unless-stopped
    ports:
      - "9090:9090"
    command:
      - --config.file=/etc/prometheus/prometheus.yml
      - --storage.tsdb.path=/prometheus
      - --storage.tsdb.retention.time=30d
      - --web.console.libraries=/etc/prometheus/console_libraries
      - --web.console.templates=/etc/prometheus/consoles
      - --web.enable-lifecycle
      - --web.external-url=http://prometheus-$env.sas-com.local:9090
    volumes:
      - ./prometheus/$env/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./prometheus/$env/alert_rules.yml:/etc/prometheus/alert_rules.yml
      - prometheus-data-$env:/prometheus
    networks:
      - monitoring-$env

  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager-$env
    restart: unless-stopped
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager/$env/alertmanager.yml:/etc/alertmanager/alertmanager.yml
      - alertmanager-data-$env:/alertmanager
    networks:
      - monitoring-$env

  grafana:
    image: grafana/grafana:latest
    container_name: grafana-$env
    restart: unless-stopped
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    volumes:
      - ./grafana/$env/provisioning:/etc/grafana/provisioning
      - ./grafana/$env/dashboards:/var/lib/grafana/dashboards
      - grafana-data-$env:/var/lib/grafana
    networks:
      - monitoring-$env

  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter-$env
    restart: unless-stopped
    ports:
      - "9100:9100"
    command:
      - --path.rootfs=/host
    volumes:
      - /:/host:ro,rslave
    networks:
      - monitoring-$env

volumes:
  prometheus-data-$env:
  alertmanager-data-$env:
  grafana-data-$env:

networks:
  monitoring-$env:
    driver: bridge
EOF
    
    log_success "Docker Compose configuration generated for $env"
}

# Setup Alertmanager configuration
setup_alertmanager() {
    local env="$1"
    log_info "Setting up Alertmanager for $env environment"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would setup Alertmanager for $env"
        return
    fi
    
    mkdir -p "$PROJECT_ROOT/monitoring/alertmanager/$env"
    
    cat > "$PROJECT_ROOT/monitoring/alertmanager/$env/alertmanager.yml" << EOF
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@sas-com.example.com'
  smtp_auth_username: '\${SMTP_USERNAME}'
  smtp_auth_password: '\${SMTP_PASSWORD}'

templates:
  - '/etc/alertmanager/templates/*.tmpl'

route:
  group_by: ['alertname', 'environment']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 12h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
    - match:
        severity: warning
      receiver: 'warning-alerts'
    - match:
        environment: production
      receiver: 'production-alerts'

receivers:
  - name: 'default'
    email_configs:
      - to: 'github@sas-com.com'
        subject: '[{{ .GroupLabels.environment | upper }}] Alert: {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          Environment: {{ .Labels.environment }}
          Severity: {{ .Labels.severity }}
          {{ end }}

  - name: 'critical-alerts'
    email_configs:
      - to: 'github@sas-com.com'
        subject: '[CRITICAL][{{ .GroupLabels.environment | upper }}] {{ .GroupLabels.alertname }}'
        body: |
          🚨 CRITICAL ALERT 🚨
          
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          Environment: {{ .Labels.environment }}
          Instance: {{ .Labels.instance }}
          Time: {{ .StartsAt.Format "2006-01-02 15:04:05" }}
          {{ end }}
    webhook_configs:
      - url: '\${TEAMS_WEBHOOK_URL}'
        title: '[CRITICAL] {{ .GroupLabels.alertname }}'
        text: |
          {{ range .Alerts }}
          **Alert:** {{ .Annotations.summary }}
          **Environment:** {{ .Labels.environment }}
          **Description:** {{ .Annotations.description }}
          {{ end }}

  - name: 'warning-alerts'
    email_configs:
      - to: 'github@sas-com.com'
        subject: '[WARNING][{{ .GroupLabels.environment | upper }}] {{ .GroupLabels.alertname }}'

  - name: 'production-alerts'
    email_configs:
      - to: 'github@sas-com.com,management@sas-com.com'
        subject: '[PRODUCTION] {{ .GroupLabels.alertname }}'
    webhook_configs:
      - url: '\${TEAMS_WEBHOOK_URL}'
      - url: '\${SLACK_WEBHOOK_URL}'
      
inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'instance']
EOF
    
    log_success "Alertmanager configuration created for $env"
}

# Setup Grafana dashboards
setup_grafana_dashboards() {
    local env="$1"
    log_info "Setting up Grafana dashboards for $env environment"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would setup Grafana dashboards for $env"
        return
    fi
    
    mkdir -p "$PROJECT_ROOT/monitoring/grafana/$env/"{provisioning/{datasources,dashboards},dashboards}
    
    # Datasource configuration
    cat > "$PROJECT_ROOT/monitoring/grafana/$env/provisioning/datasources/prometheus.yml" << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF
    
    # Dashboard provisioning
    cat > "$PROJECT_ROOT/monitoring/grafana/$env/provisioning/dashboards/dashboards.yml" << EOF
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF
    
    # Generate system dashboard
    generate_system_dashboard "$env"
    
    # Generate application dashboard
    generate_application_dashboard "$env"
    
    # Generate deployment dashboard
    generate_deployment_dashboard "$env"
    
    log_success "Grafana dashboards created for $env"
}

# Generate system dashboard
generate_system_dashboard() {
    local env="$1"
    log_info "Generating system dashboard for $env"
    
    cat > "$PROJECT_ROOT/monitoring/grafana/$env/dashboards/system-overview.json" << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "System Overview",
    "tags": ["system", "infrastructure"],
    "timezone": "browser",
    "panels": [
      {
        "title": "CPU Usage",
        "type": "stat",
        "targets": [
          {
            "expr": "100 - (avg by (instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "legendFormat": "{{instance}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 70},
                {"color": "red", "value": 90}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
      },
      {
        "title": "Memory Usage",
        "type": "stat",
        "targets": [
          {
            "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
            "legendFormat": "{{instance}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 75},
                {"color": "red", "value": 90}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0}
      }
    ],
    "time": {"from": "now-1h", "to": "now"},
    "refresh": "30s"
  }
}
EOF
    
    log_info "System dashboard generated for $env"
}

# Generate application dashboard
generate_application_dashboard() {
    local env="$1"
    log_info "Generating application dashboard for $env"
    
    cat > "$PROJECT_ROOT/monitoring/grafana/$env/dashboards/application-performance.json" << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "Application Performance",
    "tags": ["application", "performance"],
    "timezone": "browser",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{handler}}"
          }
        ],
        "yAxes": [
          {"unit": "reqps", "label": "Requests/sec"}
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ],
        "yAxes": [
          {"unit": "s", "label": "Response Time"}
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      }
    ],
    "time": {"from": "now-1h", "to": "now"},
    "refresh": "30s"
  }
}
EOF
    
    log_info "Application dashboard generated for $env"
}

# Generate deployment dashboard
generate_deployment_dashboard() {
    local env="$1"
    log_info "Generating deployment dashboard for $env"
    
    cat > "$PROJECT_ROOT/monitoring/grafana/$env/dashboards/deployment-metrics.json" << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "Deployment Metrics",
    "tags": ["deployment", "devops"],
    "timezone": "browser",
    "panels": [
      {
        "title": "Deployment Frequency",
        "type": "stat",
        "targets": [
          {
            "expr": "increase(github_actions_workflow_runs_total{workflow_name=\"Deploy to Production\"}[7d])",
            "legendFormat": "Deployments per week"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "short"
          }
        },
        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
      },
      {
        "title": "Deployment Success Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(github_actions_workflow_runs_total{conclusion=\"success\"}[7d]) / rate(github_actions_workflow_runs_total[7d]) * 100",
            "legendFormat": "Success Rate"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"color": "red", "value": null},
                {"color": "yellow", "value": 95},
                {"color": "green", "value": 99}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0}
      }
    ],
    "time": {"from": "now-7d", "to": "now"},
    "refresh": "1m"
  }
}
EOF
    
    log_info "Deployment dashboard generated for $env"
}

# Validate monitoring configuration
validate_monitoring_config() {
    log_info "Validating monitoring configuration..."
    
    local validation_errors=0
    
    # Check configuration files exist
    if [[ ! -f "$CONFIG_DIR/monitoring-config.yml" ]]; then
        log_error "Missing monitoring configuration file"
        ((validation_errors++))
    else
        log_success "Monitoring configuration file found"
    fi
    
    # Validate YAML syntax
    if ! yq eval '.' "$CONFIG_DIR/monitoring-config.yml" > /dev/null 2>&1; then
        log_error "Invalid YAML syntax in monitoring configuration"
        ((validation_errors++))
    else
        log_success "YAML syntax is valid"
    fi
    
    # Check required environment variables
    local required_vars=(
        "PROMETHEUS_PORT"
        "GRAFANA_PORT"
        "ALERTMANAGER_PORT"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_warning "Environment variable $var is not set"
        else
            log_success "Environment variable $var is configured"
        fi
    done
    
    # Validate monitoring endpoints (if services are running)
    if command -v curl &> /dev/null; then
        local endpoints=(
            "http://localhost:9090/-/healthy"
            "http://localhost:3001/api/health"
            "http://localhost:9093/-/healthy"
        )
        
        for endpoint in "${endpoints[@]}"; do
            if curl -f -s "$endpoint" > /dev/null 2>&1; then
                log_success "Endpoint $endpoint is healthy"
            else
                log_warning "Endpoint $endpoint is not accessible (service may not be running)"
            fi
        done
    fi
    
    if [[ $validation_errors -eq 0 ]]; then
        log_success "Monitoring configuration validation completed successfully"
        return 0
    else
        log_error "Monitoring configuration validation failed with $validation_errors errors"
        return 1
    fi
}

# Start monitoring services
start_monitoring_services() {
    local env="$1"
    log_info "Starting monitoring services for $env environment"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would start monitoring services for $env"
        return
    fi
    
    cd "$PROJECT_ROOT/monitoring"
    
    # Start monitoring stack
    docker-compose -f "docker-compose.$env.yml" up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    local services=("prometheus" "grafana" "alertmanager" "node-exporter")
    for service in "${services[@]}"; do
        if docker-compose -f "docker-compose.$env.yml" ps | grep -q "$service.*Up"; then
            log_success "$service is running"
        else
            log_error "$service failed to start"
        fi
    done
    
    log_success "Monitoring services started for $env"
    log_info "Access URLs:"
    log_info "  Prometheus: http://localhost:9090"
    log_info "  Grafana: http://localhost:3001 (admin/admin123)"
    log_info "  Alertmanager: http://localhost:9093"
}

# Main execution function
main() {
    log_info "Monitoring and Metrics Setup Script"
    log_info "Environment: $ENVIRONMENT"
    log_info "Monitoring Type: $MONITORING_TYPE"
    log_info "Provider: $PROVIDER"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN MODE - No changes will be made"
    fi
    
    # Check prerequisites
    if ! check_prerequisites; then
        exit 1
    fi
    
    # Validate configuration if requested
    if [[ "$VALIDATE_ONLY" == "true" ]]; then
        validate_monitoring_config
        exit $?
    fi
    
    # Setup monitoring based on environment
    case "$ENVIRONMENT" in
        "dev")
            setup_environment_monitoring "development"
            ;;
        "staging")
            setup_environment_monitoring "staging"
            ;;
        "prod")
            setup_environment_monitoring "production"
            ;;
        "all")
            setup_environment_monitoring "development"
            setup_environment_monitoring "staging"
            setup_environment_monitoring "production"
            ;;
    esac
    
    log_success "Monitoring setup completed successfully!"
    
    if [[ "$DRY_RUN" != "true" ]]; then
        log_info ""
        log_info "Next steps:"
        log_info "1. Review generated configurations in monitoring/ directory"
        log_info "2. Set environment variables for SMTP and webhook URLs"
        log_info "3. Start monitoring services: ./monitoring-setup.sh -e $ENVIRONMENT --start"
        log_info "4. Access Grafana dashboards and configure additional alerts"
        log_info ""
    fi
}

# Setup monitoring for specific environment
setup_environment_monitoring() {
    local env_key="$1"
    local env_display="${env_key^}"  # Capitalize first letter
    
    log_info "Setting up monitoring for $env_display environment"
    
    # Load environment configuration
    load_environment_config "$env_key"
    
    # Setup based on provider
    case "$PROVIDER" in
        "prometheus")
            setup_prometheus_monitoring "$env_key"
            setup_alertmanager "$env_key"
            if [[ "$SETUP_DASHBOARDS" == "true" ]]; then
                setup_grafana_dashboards "$env_key"
            fi
            ;;
        "elastic")
            log_warning "Elastic Stack setup not implemented yet"
            ;;
        "datadog")
            log_warning "Datadog setup not implemented yet"
            ;;
        "newrelic")
            log_warning "New Relic setup not implemented yet"
            ;;
        *)
            log_error "Unsupported monitoring provider: $PROVIDER"
            return 1
            ;;
    esac
    
    log_success "Monitoring setup completed for $env_display environment"
}

# Execute main function
main "$@"