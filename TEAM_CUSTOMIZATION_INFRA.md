# GitHub運用ガイドライン - インフラ/DevOpsチーム版

**エス・エー・エス株式会社 インフラストラクチャ・DevOpsチーム向け**  
*自動化、監視、デプロイメント最適化のための実践ガイド*

---

## 📚 目次

1. [インフラチーム責務マトリックス](#インフラチーム責務マトリックス)
2. [CI/CDパイプライン管理](#cicdパイプライン管理)
3. [インフラストラクチャ as Code](#インフラストラクチャ-as-code)
4. [監視とアラート](#監視とアラート)
5. [デプロイメント戦略](#デプロイメント戦略)
6. [運用自動化](#運用自動化)
7. [パフォーマンス最適化](#パフォーマンス最適化)
8. [成功指標とSLO](#成功指標とslo)

---

## インフラチーム責務マトリックス

### RACI マトリックス

| タスク | インフラ | 開発 | セキュリティ | PM |
|--------|----------|------|--------------|-----|
| CI/CD設計 | R/A | C | C | I |
| デプロイ実行 | R/A | I | I | I |
| 監視設定 | R/A | C | I | I |
| インシデント対応 | R | A | C | I |
| キャパシティ計画 | R/A | C | I | I |
| セキュリティ更新 | R | I | A | I |

*R=Responsible, A=Accountable, C=Consulted, I=Informed*

---

## CI/CDパイプライン管理

### 標準パイプライン構成

```yaml
# .github/workflows/infra-standard-pipeline.yml
name: Infrastructure Standard Pipeline

on:
  push:
    branches: [main, staging, dev]
  pull_request:
    branches: [main]

env:
  AWS_REGION: ap-northeast-1
  TERRAFORM_VERSION: 1.5.0

jobs:
  infrastructure-validation:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3
        
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: ${{ env.TERRAFORM_VERSION }}
          
      - name: Terraform Format Check
        run: terraform fmt -check -recursive
        
      - name: Terraform Validate
        run: |
          terraform init -backend=false
          terraform validate
          
      - name: Checkov Security Scan
        uses: bridgecrewio/checkov-action@master
        with:
          directory: ./terraform
          framework: terraform
          
      - name: Cost Estimation
        uses: infracost/infracost-action@v1
        with:
          path: ./terraform
          
  container-security:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3
        
      - name: Trivy Scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'config'
          scan-ref: '.'
          
      - name: Dockerfile Lint
        uses: hadolint/hadolint-action@v3.1.0
        with:
          dockerfile: ./Dockerfile
          
  deployment:
    needs: [infrastructure-validation, container-security]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to AWS
        run: |
          # デプロイメントスクリプト
          ./scripts/deploy.sh ${{ github.sha }}
```

### 環境別パイプライン設定

```yaml
# environments.yml
environments:
  development:
    auto_deploy: true
    approval_required: false
    rollback_enabled: true
    monitoring_level: basic
    
  staging:
    auto_deploy: true
    approval_required: true
    rollback_enabled: true
    monitoring_level: enhanced
    
  production:
    auto_deploy: false
    approval_required: true
    rollback_enabled: true
    monitoring_level: comprehensive
    blue_green_deployment: true
```

---

## インフラストラクチャ as Code

### Terraform標準構成

```hcl
# terraform/modules/standard/main.tf
module "vpc" {
  source = "./modules/vpc"
  
  cidr_block = var.vpc_cidr
  availability_zones = var.availability_zones
  
  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Team        = "Infrastructure"
  }
}

module "ecs_cluster" {
  source = "./modules/ecs"
  
  cluster_name = "${var.project}-${var.environment}"
  vpc_id       = module.vpc.vpc_id
  subnets      = module.vpc.private_subnets
  
  autoscaling = {
    min_capacity = var.min_capacity
    max_capacity = var.max_capacity
    target_cpu   = 70
    target_memory = 80
  }
}

module "monitoring" {
  source = "./modules/monitoring"
  
  cluster_name = module.ecs_cluster.cluster_name
  
  alerts = {
    cpu_threshold    = 80
    memory_threshold = 85
    error_rate       = 0.01
  }
}
```

### Kubernetes マニフェスト管理

```yaml
# k8s/base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-deployment
  labels:
    app: myapp
    version: v1
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
        version: v1
    spec:
      containers:
      - name: app
        image: myapp:latest
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

---

## 監視とアラート

### 監視スタック構成

```yaml
# monitoring/docker-compose.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=30d'
    ports:
      - "9090:9090"
      
  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"
      
  alertmanager:
    image: prom/alertmanager:latest
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
    ports:
      - "9093:9093"
      
  node_exporter:
    image: prom/node-exporter:latest
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
```

### アラートルール定義

```yaml
# alerts/infrastructure.yml
groups:
  - name: infrastructure
    interval: 30s
    rules:
      - alert: HighCPUUsage
        expr: |
          100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
          team: infrastructure
        annotations:
          summary: "High CPU usage on {{ $labels.instance }}"
          description: "CPU usage is above 80% (current value: {{ $value }}%)"
          
      - alert: DiskSpaceLow
        expr: |
          (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100 < 10
        for: 5m
        labels:
          severity: critical
          team: infrastructure
        annotations:
          summary: "Low disk space on {{ $labels.instance }}"
          description: "Disk space is below 10% (current value: {{ $value }}%)"
          
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
          team: infrastructure
        annotations:
          summary: "Service down: {{ $labels.job }}"
          description: "{{ $labels.instance }} has been down for more than 1 minute"
```

---

## デプロイメント戦略

### Blue-Green デプロイメント

```bash
#!/bin/bash
# scripts/blue-green-deploy.sh

set -e

ENVIRONMENT=$1
VERSION=$2

echo "Starting Blue-Green deployment for $ENVIRONMENT with version $VERSION"

# 1. 新環境（Green）の準備
echo "Preparing Green environment..."
terraform workspace select green-$ENVIRONMENT || terraform workspace new green-$ENVIRONMENT
terraform apply -var="version=$VERSION" -auto-approve

# 2. ヘルスチェック
echo "Running health checks..."
./scripts/health-check.sh green-$ENVIRONMENT
if [ $? -ne 0 ]; then
    echo "Health check failed. Rolling back..."
    terraform destroy -auto-approve
    exit 1
fi

# 3. トラフィック切り替え
echo "Switching traffic to Green..."
aws elb modify-load-balancer-attributes \
    --load-balancer-name $ENVIRONMENT-lb \
    --target-group-arn $(terraform output green_target_group_arn)

# 4. 監視期間
echo "Monitoring for 10 minutes..."
sleep 600

# 5. Blue環境の削除
echo "Cleaning up Blue environment..."
terraform workspace select blue-$ENVIRONMENT
terraform destroy -auto-approve

echo "Blue-Green deployment completed successfully"
```

### カナリアデプロイメント

```yaml
# k8s/canary-deployment.yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: myapp
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  progressDeadlineSeconds: 60
  service:
    port: 80
    targetPort: 8080
  analysis:
    interval: 30s
    threshold: 5
    maxWeight: 50
    stepWeight: 10
    metrics:
    - name: request-success-rate
      thresholdRange:
        min: 99
      interval: 30s
    - name: request-duration
      thresholdRange:
        max: 500
      interval: 30s
    webhooks:
    - name: smoke-test
      url: http://flagger-loadtester.test/
      timeout: 15s
      metadata:
        type: smoke
        cmd: "curl -s http://myapp-canary.test/"
```

---

## 運用自動化

### 自動スケーリング設定

```hcl
# terraform/autoscaling.tf
resource "aws_autoscaling_policy" "scale_up" {
  name                   = "${var.name}-scale-up"
  scaling_adjustment     = 2
  adjustment_type        = "ChangeInCapacity"
  cooldown              = 300
  autoscaling_group_name = aws_autoscaling_group.main.name
}

resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "${var.name}-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "120"
  statistic           = "Average"
  threshold           = "70"
  alarm_description   = "This metric monitors CPU utilization"
  alarm_actions       = [aws_autoscaling_policy.scale_up.arn]
}

resource "aws_autoscaling_policy" "scale_down" {
  name                   = "${var.name}-scale-down"
  scaling_adjustment     = -1
  adjustment_type        = "ChangeInCapacity"
  cooldown              = 300
  autoscaling_group_name = aws_autoscaling_group.main.name
}

resource "aws_cloudwatch_metric_alarm" "cpu_low" {
  alarm_name          = "${var.name}-cpu-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "120"
  statistic           = "Average"
  threshold           = "30"
  alarm_description   = "This metric monitors CPU utilization"
  alarm_actions       = [aws_autoscaling_policy.scale_down.arn]
}
```

### バックアップ自動化

```bash
#!/bin/bash
# scripts/automated-backup.sh

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/${TIMESTAMP}"

# データベースバックアップ
echo "Backing up databases..."
for DB in $(mysql -e "SHOW DATABASES;" | grep -v Database); do
    mysqldump --single-transaction --routines --triggers \
              --databases $DB > ${BACKUP_DIR}/${DB}.sql
done

# ファイルシステムバックアップ
echo "Backing up filesystem..."
tar -czf ${BACKUP_DIR}/filesystem.tar.gz \
    --exclude=/backup \
    --exclude=/tmp \
    --exclude=/var/log \
    /

# S3へアップロード
echo "Uploading to S3..."
aws s3 sync ${BACKUP_DIR} s3://backup-bucket/${TIMESTAMP}/ \
    --storage-class GLACIER

# 古いバックアップの削除
echo "Cleaning up old backups..."
find /backup -type d -mtime +30 -exec rm -rf {} \;

echo "Backup completed: ${TIMESTAMP}"
```

---

## パフォーマンス最適化

### ビルド時間最適化

```yaml
# .github/workflows/optimized-build.yml
name: Optimized Build Pipeline

on:
  push:
    branches: [main, dev]

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [api, web, worker]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Docker Buildx
        uses: docker/setup-buildx-action@v2
        
      - name: Cache Docker layers
        uses: actions/cache@v3
        with:
          path: /tmp/.buildx-cache
          key: ${{ runner.os }}-buildx-${{ github.sha }}
          restore-keys: |
            ${{ runner.os }}-buildx-
            
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: ./${{ matrix.service }}
          push: true
          tags: myapp/${{ matrix.service }}:${{ github.sha }}
          cache-from: type=local,src=/tmp/.buildx-cache
          cache-to: type=local,dest=/tmp/.buildx-cache-new,mode=max
          
      - name: Move cache
        run: |
          rm -rf /tmp/.buildx-cache
          mv /tmp/.buildx-cache-new /tmp/.buildx-cache
```

### CDN設定最適化

```hcl
# terraform/cloudfront.tf
resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled    = true
  default_root_object = "index.html"
  
  origin {
    domain_name = aws_s3_bucket.static.bucket_regional_domain_name
    origin_id   = "S3-${aws_s3_bucket.static.id}"
    
    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.main.cloudfront_access_identity_path
    }
  }
  
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.static.id}"
    
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
    
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 86400
    max_ttl                = 31536000
    compress               = true
  }
  
  ordered_cache_behavior {
    path_pattern     = "/api/*"
    allowed_methods  = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "ALB-${aws_lb.main.id}"
    
    forwarded_values {
      query_string = true
      headers      = ["*"]
      cookies {
        forward = "all"
      }
    }
    
    viewer_protocol_policy = "https-only"
    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0
  }
}
```

---

## 成功指標とSLO

### Service Level Objectives (SLO)

| サービス | 可用性 | レイテンシ (P99) | エラー率 |
|----------|--------|------------------|----------|
| API | 99.9% | < 200ms | < 0.1% |
| Web | 99.95% | < 100ms | < 0.05% |
| Database | 99.99% | < 50ms | < 0.01% |

### インフラKPI

```yaml
# metrics/infrastructure-kpi.yml
kpis:
  availability:
    target: 99.9%
    measurement: uptime / total_time * 100
    
  deployment_frequency:
    target: ">= 10 per week"
    measurement: count(deployments) / 7
    
  mttr:
    target: "< 30 minutes"
    measurement: avg(incident_resolution_time)
    
  infrastructure_cost:
    target: "< $10,000/month"
    measurement: sum(aws_costs + gcp_costs + azure_costs)
    
  resource_utilization:
    cpu:
      target: "60-80%"
      measurement: avg(cpu_usage)
    memory:
      target: "70-85%"
      measurement: avg(memory_usage)
    
  build_time:
    target: "< 5 minutes"
    measurement: avg(pipeline_duration)
    
  test_coverage:
    target: ">= 80%"
    measurement: covered_lines / total_lines * 100
```

### 週次運用レポートテンプレート

```markdown
## インフラ週次レポート

### サマリー
- 総稼働時間: XXX時間
- 可用性: XX.X%
- インシデント数: X件
- デプロイ回数: X回

### パフォーマンス
- 平均レスポンスタイム: XXms
- P99レイテンシ: XXms
- エラー率: X.XX%

### コスト
- 今週の費用: $X,XXX
- 前週比: +/- X%
- 予算消化率: XX%

### 改善アクション
1. [課題] → [対策]
2. [課題] → [対策]

### 来週の計画
- [ ] メンテナンス作業
- [ ] アップグレード計画
- [ ] 最適化タスク
```

---

## 🛠️ インフラツールボックス

### 必須CLIツール

```bash
# インストールスクリプト
#!/bin/bash

# AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && ./aws/install

# Terraform
wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### 診断スクリプト

```bash
#!/bin/bash
# scripts/infra-health-check.sh

echo "=== Infrastructure Health Check ==="
echo

# AWS接続確認
echo "Checking AWS connectivity..."
aws sts get-caller-identity > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ AWS connection OK"
else
    echo "✗ AWS connection FAILED"
fi

# Kubernetes接続確認
echo "Checking Kubernetes connectivity..."
kubectl cluster-info > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Kubernetes connection OK"
else
    echo "✗ Kubernetes connection FAILED"
fi

# Docker確認
echo "Checking Docker..."
docker version > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Docker OK"
else
    echo "✗ Docker FAILED"
fi

echo
echo "=== Health Check Complete ==="
```

---

## 📞 インフラチームサポート

### エスカレーション手順

1. **L1 - 情報収集** (5分)
   - ログ確認
   - 監視ダッシュボード確認
   - 最近の変更確認

2. **L2 - 初期対応** (15分)
   - 一時対処実施
   - 影響範囲特定
   - ステークホルダー通知

3. **L3 - 根本対応** (1時間)
   - 根本原因調査
   - 恒久対策実施
   - ドキュメント更新

### 連絡先

- **インフラチーム**: infra@sas-com.com
- **24時間対応**: oncall@sas-com.com
- **Slackチャンネル**: #infra-team
- **PagerDuty**: sas-infrastructure

---

**更新日**: 2025-09-11  
**バージョン**: 1.0.0  
**対象**: インフラストラクチャ・DevOpsチーム