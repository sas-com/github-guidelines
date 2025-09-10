# GitHub Webhook デプロイ・運用ガイド

**エス・エー・エス株式会社**  
*GitHub Webhook セキュリティシステム デプロイ・運用マニュアル*

## 📋 目次

1. [デプロイ概要](#デプロイ概要)
2. [環境構成](#環境構成)
3. [前提条件](#前提条件)
4. [デプロイ手順](#デプロイ手順)
5. [設定管理](#設定管理)
6. [監視・ログ](#監視ログ)
7. [運用手順](#運用手順)
8. [トラブルシューティング](#トラブルシューティング)
9. [セキュリティ運用](#セキュリティ運用)
10. [災害復旧](#災害復旧)

## 📌 デプロイ概要

### システム構成

```mermaid
graph TB
    subgraph "GitHub"
        GH[GitHub.com]
    end
    
    subgraph "Load Balancer"
        LB[AWS ALB / Azure LB]
    end
    
    subgraph "Kubernetes Cluster"
        subgraph "Webhook Services"
            NS[Node.js Service]
            PS[Python Service]
            GS[Go Service]
        end
        
        subgraph "Infrastructure"
            REDIS[Redis Cache]
            DB[(PostgreSQL)]
            ES[Elasticsearch]
        end
        
        subgraph "Monitoring"
            PROM[Prometheus]
            GRAF[Grafana]
            ALERT[AlertManager]
        end
    end
    
    subgraph "External Services"
        SLACK[Slack/Teams通知]
        EMAIL[メール通知]
        SIEM[SIEM/SOC]
    end
    
    GH --> LB
    LB --> NS
    LB --> PS
    LB --> GS
    
    NS --> REDIS
    PS --> REDIS
    GS --> REDIS
    
    NS --> DB
    PS --> DB
    GS --> DB
    
    NS --> ES
    PS --> ES
    GS --> ES
    
    PROM --> GRAF
    PROM --> ALERT
    
    ALERT --> SLACK
    ALERT --> EMAIL
    ALERT --> SIEM
```

### 対応プラットフォーム

| プラットフォーム | サポート状況 | 推奨度 |
|-----------------|-------------|--------|
| **AWS EKS** | ✅ 完全対応 | ★★★ |
| **Azure AKS** | ✅ 完全対応 | ★★★ |
| **Google GKE** | ✅ 完全対応 | ★★★ |
| **オンプレミス** | ⚠️ 制限付き | ★☆☆ |
| **Docker Compose** | ✅ 開発用 | ★★☆ |

## 🏗️ 環境構成

### 推奨環境構成

#### 本番環境 (Production)
```yaml
environments:
  production:
    cluster:
      nodes: 6-12
      instance_type: "m5.xlarge" # AWS
      cpu: "4 vCPU"
      memory: "16GB RAM"
      storage: "100GB SSD"
    
    webhook_services:
      replicas: 3
      resources:
        requests:
          cpu: "500m"
          memory: "1Gi"
        limits:
          cpu: "2000m"
          memory: "4Gi"
    
    database:
      type: "Managed Service"
      instance: "db.r5.large"
      storage: "500GB"
      backup_retention: "30 days"
      multi_az: true
    
    cache:
      type: "ElastiCache/Azure Redis"
      instance: "cache.m5.large"
      nodes: 3
      
    monitoring:
      retention: "1 year"
      metrics_interval: "15s"
      log_retention: "90 days"
```

#### ステージング環境 (Staging)
```yaml
environments:
  staging:
    cluster:
      nodes: 3
      instance_type: "m5.large"
      cpu: "2 vCPU"
      memory: "8GB RAM"
      storage: "50GB SSD"
    
    webhook_services:
      replicas: 2
      resources:
        requests:
          cpu: "250m"
          memory: "512Mi"
        limits:
          cpu: "1000m"
          memory: "2Gi"
```

#### 開発環境 (Development)
```yaml
environments:
  development:
    cluster:
      nodes: 1
      instance_type: "m5.medium"
      cpu: "1 vCPU"
      memory: "4GB RAM"
      storage: "20GB SSD"
    
    webhook_services:
      replicas: 1
      resources:
        requests:
          cpu: "100m"
          memory: "256Mi"
        limits:
          cpu: "500m"
          memory: "1Gi"
```

## 🔧 前提条件

### システム要件

#### Kubernetes クラスター
- **Kubernetes バージョン**: 1.25以上
- **Container Runtime**: containerd または CRI-O
- **Network Plugin**: Calico, Weave Net, または AWS VPC CNI
- **Ingress Controller**: NGINX、ALB、または Traefik
- **Certificate Manager**: cert-manager
- **DNS**: CoreDNS

#### 外部サービス
- **GitHub Enterprise Cloud**: Webhook設定権限
- **DNS管理**: Route53、CloudDNS、または Azure DNS
- **SSL証明書**: Let's Encrypt または企業証明書
- **秘密管理**: AWS Secrets Manager、Azure Key Vault、または HashiCorp Vault

### 必要なツール

#### 管理ツール
```bash
# Kubernetes管理
kubectl >= 1.25
helm >= 3.8

# クラウド CLI
aws-cli >= 2.0      # AWS使用時
az-cli >= 2.40      # Azure使用時
gcloud >= 400.0     # GCP使用時

# 監視・ログ
prometheus-operator
grafana
elasticsearch-operator

# CI/CD
github-actions      # GitHub Actions
argocd             # ArgoCD (推奨)
fluxcd             # Flux CD (代替)
```

#### 開発・テストツール
```bash
# コンテナ
docker >= 20.10
docker-compose >= 2.0

# テスト・検証
curl
jq
httpie
k6                 # 負荷テスト

# セキュリティ
trivy              # 脆弱性スキャン
cosign             # コンテナ署名
falco              # ランタイムセキュリティ
```

## 🚀 デプロイ手順

### Step 1: 環境準備

#### 1.1 Kubernetes クラスター作成

**AWS EKS**:
```bash
# EKS クラスター作成
eksctl create cluster \
  --name sas-webhook-cluster \
  --version 1.27 \
  --region ap-northeast-1 \
  --nodegroup-name webhook-nodes \
  --node-type m5.xlarge \
  --nodes 3 \
  --nodes-min 3 \
  --nodes-max 12 \
  --ssh-access \
  --ssh-public-key sas-webhook-key \
  --managed

# EKS cluster への接続設定
aws eks update-kubeconfig --region ap-northeast-1 --name sas-webhook-cluster
```

**Azure AKS**:
```bash
# AKS クラスター作成
az aks create \
  --resource-group sas-webhook-rg \
  --name sas-webhook-cluster \
  --kubernetes-version 1.27.3 \
  --location japaneast \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3 \
  --enable-managed-identity \
  --enable-addons monitoring \
  --generate-ssh-keys

# AKS cluster への接続設定
az aks get-credentials --resource-group sas-webhook-rg --name sas-webhook-cluster
```

**Google GKE**:
```bash
# GKE クラスター作成
gcloud container clusters create sas-webhook-cluster \
  --zone asia-northeast1-a \
  --num-nodes 3 \
  --machine-type e2-standard-4 \
  --cluster-version 1.27 \
  --enable-autorepair \
  --enable-autoupgrade \
  --enable-network-policy

# GKE cluster への接続設定
gcloud container clusters get-credentials sas-webhook-cluster --zone asia-northeast1-a
```

#### 1.2 必須コンポーネントインストール

```bash
# Helm追加
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add elastic https://helm.elastic.co
helm repo update

# Ingress Controller
helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.replicaCount=3 \
  --set controller.nodeSelector."kubernetes\.io/arch"=amd64

# cert-manager (SSL証明書管理)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Prometheus Operator
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheusOperator.enabled=true \
  --set prometheus.enabled=true \
  --set alertmanager.enabled=true \
  --set grafana.enabled=true
```

### Step 2: 秘密管理セットアップ

#### 2.1 Kubernetes Secrets作成

```bash
# Webhook秘密鍵 (GitHub設定と同じ値を使用)
kubectl create secret generic webhook-secrets \
  --namespace webhook \
  --from-literal=WEBHOOK_SECRET="your-super-secure-webhook-secret" \
  --from-literal=DATABASE_URL="postgresql://user:password@db-host:5432/webhooks" \
  --from-literal=REDIS_URL="redis://redis-host:6379" \
  --from-literal=ELASTICSEARCH_URL="https://es-host:9200"

# TLS証明書 (Let's Encryptまたは企業証明書)
kubectl create secret tls webhook-tls \
  --namespace webhook \
  --cert=webhook.sas-com.com.crt \
  --key=webhook.sas-com.com.key
```

#### 2.2 外部秘密管理統合 (推奨)

**AWS Secrets Manager統合**:
```yaml
# external-secrets-operator
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: webhook
spec:
  provider:
    aws:
      service: SecretsManager
      region: ap-northeast-1
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets-sa
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: webhook-secrets
  namespace: webhook
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: webhook-secrets
  data:
    - secretKey: WEBHOOK_SECRET
      remoteRef:
        key: webhook/production/secret
    - secretKey: DATABASE_URL
      remoteRef:
        key: webhook/production/database-url
```

### Step 3: アプリケーションデプロイ

#### 3.1 Kubernetes マニフェスト作成

**Namespace作成**:
```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: webhook
  labels:
    name: webhook
    security.sas-com.com/tier: critical
```

**ConfigMap作成**:
```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: webhook-config
  namespace: webhook
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "info"
  ENABLE_METRICS: "true"
  ENABLE_HEALTH_CHECK: "true"
  RATE_LIMIT_GLOBAL: "1000"
  RATE_LIMIT_PER_IP: "60"
  RATE_LIMIT_PER_HOOK: "120"
  RATE_LIMIT_PER_REPO: "100"
  MAX_PAYLOAD_SIZE_MB: "10"
  IP_VALIDATION_STRICT: "true"
  GEO_RESTRICTIONS: "JP,US"
  ALLOWED_IPS: "140.82.112.0/20,143.55.64.0/20,185.199.108.0/22,192.30.252.0/22"
```

**Deployment作成 (Node.js)**:
```yaml
# deployment-nodejs.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webhook-nodejs
  namespace: webhook
  labels:
    app: webhook-nodejs
    version: v1.0.0
    component: webhook-handler
    language: nodejs
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: webhook-nodejs
  template:
    metadata:
      labels:
        app: webhook-nodejs
        version: v1.0.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "3000"
        prometheus.io/path: "/metrics"
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
        fsGroup: 1001
      containers:
      - name: webhook-nodejs
        image: sas-com/webhook-nodejs:v1.0.0
        imagePullPolicy: Always
        ports:
        - containerPort: 3000
          name: http
          protocol: TCP
        env:
        - name: HOST
          value: "0.0.0.0"
        - name: PORT
          value: "3000"
        envFrom:
        - configMapRef:
            name: webhook-config
        - secretRef:
            name: webhook-secrets
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 4Gi
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          capabilities:
            drop:
              - ALL
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: tmp
        emptyDir: {}
      - name: logs
        emptyDir: {}
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - webhook-nodejs
              topologyKey: kubernetes.io/hostname
```

**Service作成**:
```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: webhook-service
  namespace: webhook
  labels:
    app: webhook
    component: webhook-handler
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "3000"
    prometheus.io/path: "/metrics"
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 3000
    protocol: TCP
    name: http
  selector:
    app: webhook-nodejs
```

**Ingress作成**:
```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: webhook-ingress
  namespace: webhook
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/rate-limit: "60"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  tls:
  - hosts:
    - webhook.sas-com.internal
    secretName: webhook-tls
  rules:
  - host: webhook.sas-com.internal
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: webhook-service
            port:
              number: 80
```

#### 3.2 デプロイ実行

```bash
# Namespace作成
kubectl apply -f namespace.yaml

# 設定適用
kubectl apply -f configmap.yaml

# アプリケーションデプロイ
kubectl apply -f deployment-nodejs.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

# デプロイ状況確認
kubectl get pods -n webhook
kubectl get svc -n webhook
kubectl get ingress -n webhook

# ログ確認
kubectl logs -n webhook -l app=webhook-nodejs -f

# ヘルスチェック
kubectl port-forward -n webhook svc/webhook-service 8080:80
curl http://localhost:8080/health
```

### Step 4: 監視・ログセットアップ

#### 4.1 Prometheus ServiceMonitor

```yaml
# servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: webhook-metrics
  namespace: webhook
  labels:
    app: webhook
spec:
  selector:
    matchLabels:
      app: webhook
  endpoints:
  - port: http
    path: /metrics
    interval: 15s
    scrapeTimeout: 10s
```

#### 4.2 Grafana Dashboard

```json
{
  "dashboard": {
    "title": "GitHub Webhook Security Dashboard",
    "tags": ["webhook", "github", "security"],
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(webhook_requests_total[5m]))",
            "legendFormat": "Requests/sec"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(webhook_errors_total[5m]))",
            "legendFormat": "Errors/sec"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, webhook_processing_duration_seconds)",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Security Events",
        "type": "table",
        "targets": [
          {
            "expr": "increase(webhook_security_events_total[1h])",
            "legendFormat": "{{event_type}}"
          }
        ]
      }
    ]
  }
}
```

#### 4.3 アラート設定

```yaml
# alerts.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: webhook-alerts
  namespace: webhook
  labels:
    prometheus: kube-prometheus
    role: alert-rules
spec:
  groups:
  - name: webhook.rules
    rules:
    - alert: WebhookHighErrorRate
      expr: rate(webhook_errors_total[5m]) > 0.1
      for: 2m
      labels:
        severity: critical
      annotations:
        summary: "High webhook error rate detected"
        description: "Webhook error rate is {{ $value }} errors/sec"
        
    - alert: WebhookHighLatency
      expr: histogram_quantile(0.95, webhook_processing_duration_seconds) > 2
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High webhook processing latency"
        description: "95th percentile latency is {{ $value }}s"
        
    - alert: WebhookSecurityEvent
      expr: rate(webhook_security_events_total[1m]) > 0
      for: 0m
      labels:
        severity: critical
      annotations:
        summary: "Security event detected"
        description: "Security event: {{ $labels.event_type }}"
        
    - alert: WebhookServiceDown
      expr: up{job="webhook"} == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "Webhook service is down"
        description: "Webhook service {{ $labels.instance }} is down"
```

### Step 5: CI/CDパイプライン設定

#### 5.1 GitHub Actions ワークフロー

```yaml
# .github/workflows/webhook-ci-cd.yml
name: Webhook CI/CD Pipeline

on:
  push:
    branches: [main, develop]
    paths: ['src/webhook-handlers/**']
  pull_request:
    branches: [main]
    paths: ['src/webhook-handlers/**']

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: sas-com/webhook

jobs:
  # セキュリティスキャン
  security-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'
    
    - name: Upload Trivy scan results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'

  # ビルド・テスト
  build-test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        language: [nodejs, python, go]
    steps:
    - uses: actions/checkout@v4
    
    - name: Build and Test - Node.js
      if: matrix.language == 'nodejs'
      run: |
        cd src/webhook-handlers/nodejs
        npm ci
        npm run build
        npm run test
        npm audit
    
    - name: Build and Test - Python
      if: matrix.language == 'python'
      run: |
        cd src/webhook-handlers/python
        pip install -r requirements.txt
        python -m pytest tests/ -v --cov=src
        python -m bandit -r src/
    
    - name: Build and Test - Go
      if: matrix.language == 'go'
      run: |
        cd src/webhook-handlers/go
        go mod verify
        go test -race -coverprofile=coverage.out ./...
        go run github.com/securecodewarrior/sast-scan/cmd/gosec@latest ./...
    
    - name: Build Docker Image
      run: |
        cd src/webhook-handlers/${{ matrix.language }}
        docker build -t ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-${{ matrix.language }}:${{ github.sha }} .
        
    - name: Container Security Scan
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: '${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-${{ matrix.language }}:${{ github.sha }}'
        format: 'table'
        exit-code: '1'
        severity: 'CRITICAL,HIGH'

  # デプロイ (本番)
  deploy-production:
    if: github.ref == 'refs/heads/main'
    needs: [security-scan, build-test]
    runs-on: ubuntu-latest
    environment: production
    steps:
    - uses: actions/checkout@v4
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ap-northeast-1
    
    - name: Push to ECR
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        ECR_REPOSITORY: sas-webhook
      run: |
        aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin $ECR_REGISTRY
        docker tag ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-nodejs:${{ github.sha }} $ECR_REGISTRY/$ECR_REPOSITORY:nodejs-${{ github.sha }}
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:nodejs-${{ github.sha }}
    
    - name: Update Kubernetes
      run: |
        aws eks update-kubeconfig --region ap-northeast-1 --name sas-webhook-cluster
        kubectl set image deployment/webhook-nodejs webhook-nodejs=$ECR_REGISTRY/$ECR_REPOSITORY:nodejs-${{ github.sha }} -n webhook
        kubectl rollout status deployment/webhook-nodejs -n webhook
    
    - name: Verify Deployment
      run: |
        kubectl get pods -n webhook
        kubectl logs -n webhook -l app=webhook-nodejs --tail=100
        
        # ヘルスチェック
        WEBHOOK_URL=$(kubectl get ingress -n webhook webhook-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
        curl -f https://$WEBHOOK_URL/health || exit 1
```

## ⚙️ 設定管理

### 環境別設定

#### 本番環境設定
```yaml
# config/production.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: webhook-config-prod
  namespace: webhook
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "info"
  ENABLE_METRICS: "true"
  ENABLE_HEALTH_CHECK: "true"
  ENABLE_CORS: "false"
  ENABLE_DOCS: "false"
  
  # セキュリティ設定
  IP_VALIDATION_STRICT: "true"
  ENABLE_SIGNATURE_VERIFY: "true"
  MAX_PAYLOAD_SIZE_MB: "10"
  
  # レート制限
  RATE_LIMIT_GLOBAL: "1000"
  RATE_LIMIT_PER_IP: "60"
  RATE_LIMIT_PER_HOOK: "120"
  RATE_LIMIT_PER_REPO: "100"
  
  # 許可IP範囲
  ALLOWED_IPS: |
    140.82.112.0/20,
    143.55.64.0/20,
    185.199.108.0/22,
    192.30.252.0/22,
    20.201.28.151/32,
    20.205.243.166/32
  
  # 地域制限
  GEO_RESTRICTIONS: "JP,US"
  
  # 外部サービス
  ELASTICSEARCH_ENABLED: "true"
  REDIS_ENABLED: "true"
  PROMETHEUS_ENABLED: "true"
```

#### セキュリティ設定
```yaml
# config/security-policies.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: webhook-network-policy
  namespace: webhook
spec:
  podSelector:
    matchLabels:
      app: webhook-nodejs
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 3000
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
  - to: []
    ports:
    - protocol: TCP
      port: 5432  # PostgreSQL
    - protocol: TCP
      port: 6379  # Redis
    - protocol: TCP
      port: 9200  # Elasticsearch
    - protocol: TCP
      port: 443   # HTTPS outbound
---
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: webhook-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

## 📊 監視・ログ

### 主要メトリクス

#### アプリケーション メトリクス
```yaml
# 重要メトリクス一覧
application_metrics:
  - name: webhook_requests_total
    type: counter
    description: "総リクエスト数"
    labels: [event_type, status, repository]
    
  - name: webhook_processing_duration_seconds
    type: histogram
    description: "処理時間"
    labels: [event_type, status]
    
  - name: webhook_errors_total
    type: counter
    description: "エラー総数"
    labels: [error_type, event_type]
    
  - name: webhook_security_events_total
    type: counter
    description: "セキュリティイベント数"
    labels: [event_type, severity]
    
  - name: webhook_active_connections
    type: gauge
    description: "アクティブ接続数"

# SLIメトリクス
sli_metrics:
  availability:
    target: 99.9%
    measurement: "up{job='webhook'}"
    
  latency:
    target: "95% < 500ms"
    measurement: "histogram_quantile(0.95, webhook_processing_duration_seconds)"
    
  error_rate:
    target: "< 1%"
    measurement: "rate(webhook_errors_total[5m]) / rate(webhook_requests_total[5m])"
    
  throughput:
    target: "1000 req/min"
    measurement: "rate(webhook_requests_total[1m]) * 60"
```

#### インフラ メトリクス
```yaml
infrastructure_metrics:
  kubernetes:
    - kube_deployment_status_replicas_available
    - kube_deployment_status_replicas_unavailable
    - kube_pod_container_status_restarts_total
    - kube_pod_status_phase
    
  system:
    - node_cpu_seconds_total
    - node_memory_MemAvailable_bytes
    - node_filesystem_avail_bytes
    - node_network_receive_bytes_total
    
  application:
    - process_cpu_seconds_total
    - process_resident_memory_bytes
    - go_memstats_alloc_bytes
    - nodejs_heap_size_used_bytes
```

### ログ管理

#### ログ形式標準化
```json
{
  "timestamp": "2025-09-10T21:00:00.000Z",
  "level": "info",
  "service": "webhook-nodejs",
  "version": "1.0.0",
  "environment": "production",
  "request_id": "req_1234567890",
  "delivery_id": "12345678-1234-1234-1234-123456789012",
  "event_type": "push",
  "message": "Webhook processed successfully",
  "fields": {
    "client_ip": "140.82.112.1",
    "repository": "sas-com/example-repo",
    "sender": "developer",
    "processing_time_ms": 150,
    "payload_size": 1024,
    "security_checks_passed": true,
    "sensitive_data_detected": false
  },
  "labels": {
    "team": "platform",
    "component": "webhook-handler",
    "criticality": "high"
  }
}
```

#### ELK Stack設定
```yaml
# Elasticsearch Index Template
PUT _index_template/webhook-logs
{
  "index_patterns": ["webhook-logs-*"],
  "template": {
    "settings": {
      "number_of_shards": 3,
      "number_of_replicas": 1,
      "index.lifecycle.name": "webhook-logs-policy",
      "index.lifecycle.rollover_alias": "webhook-logs"
    },
    "mappings": {
      "properties": {
        "@timestamp": {"type": "date"},
        "level": {"type": "keyword"},
        "service": {"type": "keyword"},
        "request_id": {"type": "keyword"},
        "delivery_id": {"type": "keyword"},
        "event_type": {"type": "keyword"},
        "client_ip": {"type": "ip"},
        "repository": {"type": "keyword"},
        "processing_time_ms": {"type": "integer"},
        "security_checks_passed": {"type": "boolean"}
      }
    }
  }
}
```

### アラート設定

#### 重要度別アラート
```yaml
# Critical (P0) - 即座対応
critical_alerts:
  - name: ServiceDown
    condition: up{job="webhook"} == 0
    duration: 1m
    notification: ["pagerduty", "slack-critical", "email"]
    
  - name: HighErrorRate
    condition: rate(webhook_errors_total[5m]) > 0.05
    duration: 2m
    notification: ["pagerduty", "slack-critical"]
    
  - name: SecurityBreach
    condition: rate(webhook_security_events_total{severity="critical"}[1m]) > 0
    duration: 0s
    notification: ["pagerduty", "slack-security", "siem"]

# High (P1) - 15分以内対応
high_alerts:
  - name: HighLatency
    condition: histogram_quantile(0.95, webhook_processing_duration_seconds) > 2
    duration: 5m
    notification: ["slack-ops", "email"]
    
  - name: MemoryUsageHigh
    condition: process_resident_memory_bytes / node_memory_MemTotal_bytes > 0.8
    duration: 10m
    notification: ["slack-ops"]

# Medium (P2) - 1時間以内対応
medium_alerts:
  - name: PodRestartFrequent
    condition: rate(kube_pod_container_status_restarts_total[1h]) > 0.1
    duration: 15m
    notification: ["slack-ops"]
    
  - name: DiskSpaceLow
    condition: node_filesystem_avail_bytes / node_filesystem_size_bytes < 0.2
    duration: 30m
    notification: ["slack-ops"]
```

## 🔄 運用手順

### 日次運用

#### 1. ヘルスチェック
```bash
#!/bin/bash
# daily-health-check.sh

echo "=== Webhook Service Health Check ==="
date

# Kubernetes Pod状態確認
kubectl get pods -n webhook
kubectl get svc -n webhook
kubectl get ingress -n webhook

# エンドポイントヘルスチェック
WEBHOOK_URL="https://webhook.sas-com.internal"
echo "Health Check: $WEBHOOK_URL/health"
curl -f $WEBHOOK_URL/health | jq

echo "Metrics Check: $WEBHOOK_URL/metrics"
curl -s $WEBHOOK_URL/metrics | grep webhook_requests_total

# リソース使用状況
echo "=== Resource Usage ==="
kubectl top nodes
kubectl top pods -n webhook

# ログ確認（直近1時間のエラー）
echo "=== Recent Errors ==="
kubectl logs -n webhook -l app=webhook-nodejs --since=1h | grep ERROR | tail -10
```

#### 2. セキュリティ監査
```bash
#!/bin/bash
# security-audit.sh

echo "=== Security Audit ==="
date

# セキュリティイベント確認
curl -s "http://prometheus.monitoring.svc.cluster.local:9090/api/v1/query?query=increase(webhook_security_events_total[24h])" | jq

# 不審なアクセスパターン検知
curl -s "http://elasticsearch.logging.svc.cluster.local:9200/webhook-logs-*/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "bool": {
        "must": [
          {"range": {"@timestamp": {"gte": "now-24h"}}},
          {"term": {"level": "error"}},
          {"exists": {"field": "client_ip"}}
        ]
      }
    },
    "aggs": {
      "suspicious_ips": {
        "terms": {"field": "client_ip", "size": 10}
      }
    }
  }' | jq '.aggregations.suspicious_ips'

# 証明書有効期限確認
echo "=== SSL Certificate Expiry ==="
openssl s_client -servername webhook.sas-com.internal -connect webhook.sas-com.internal:443 2>/dev/null | openssl x509 -noout -enddate
```

### 週次運用

#### 1. パフォーマンス分析
```bash
#!/bin/bash
# weekly-performance-analysis.sh

echo "=== Weekly Performance Report ==="
date

# 週間統計取得
WEEK_AGO=$(date -d "7 days ago" -u +"%Y-%m-%dT%H:%M:%SZ")
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# リクエスト統計
echo "Total Requests (7 days):"
curl -s "http://prometheus.monitoring.svc.cluster.local:9090/api/v1/query?query=increase(webhook_requests_total[7d])" | jq

# エラー率
echo "Error Rate (7 days):"
curl -s "http://prometheus.monitoring.svc.cluster.local:9090/api/v1/query?query=rate(webhook_errors_total[7d]) / rate(webhook_requests_total[7d])" | jq

# レスポンス時間分析
echo "95th Percentile Response Time:"
curl -s "http://prometheus.monitoring.svc.cluster.local:9090/api/v1/query?query=histogram_quantile(0.95, rate(webhook_processing_duration_seconds_bucket[7d]))" | jq

# 容量計画
echo "=== Capacity Planning ==="
kubectl top nodes
kubectl describe node | grep -A 5 "Allocated resources"
```

#### 2. セキュリティレビュー
```bash
#!/bin/bash
# weekly-security-review.sh

echo "=== Weekly Security Review ==="
date

# 脆弱性スキャン実行
trivy image sas-com/webhook-nodejs:latest --severity HIGH,CRITICAL

# コンテナセキュリティ監査
kubectl get pods -n webhook -o json | \
  jq '.items[] | select(.spec.securityContext.runAsNonRoot != true)'

# Network Policy確認
kubectl get networkpolicy -n webhook -o yaml

# RBAC確認
kubectl auth can-i --list --as=system:serviceaccount:webhook:default
```

### 月次運用

#### 1. 災害復旧テスト
```bash
#!/bin/bash
# monthly-dr-test.sh

echo "=== Disaster Recovery Test ==="
date

# バックアップ確認
echo "Database Backup Status:"
# 実際の環境に応じてバックアップ確認コマンドを実装

# 復旧手順テスト（非本番環境）
echo "Testing restore procedure..."
# 復旧手順の自動テスト実装

# RTO/RPO メトリクス測定
echo "Recovery Metrics:"
echo "RTO Target: 1 hour"
echo "RPO Target: 15 minutes"
# 実際のメトリクス測定ロジック実装
```

#### 2. キャパシティレビュー
```bash
#!/bin/bash
# monthly-capacity-review.sh

echo "=== Monthly Capacity Review ==="
date

# 月間統計
echo "Monthly Statistics:"
curl -s "http://prometheus.monitoring.svc.cluster.local:9090/api/v1/query?query=increase(webhook_requests_total[30d])" | jq

# リソース使用傾向
echo "Resource Usage Trends:"
kubectl top nodes --sort-by=cpu
kubectl top pods -n webhook --sort-by=cpu

# スケーリング推奨事項
echo "Scaling Recommendations:"
# 実際のスケーリング分析ロジック実装
```

## 🔧 トラブルシューティング

### 一般的な問題と解決法

#### 1. Webhook受信エラー

**症状**: GitHubからのWebhookが受信されない

**原因と解決法**:

```bash
# DNS解決確認
nslookup webhook.sas-com.internal

# SSL証明書確認
openssl s_client -servername webhook.sas-com.internal -connect webhook.sas-com.internal:443

# Ingress確認
kubectl get ingress -n webhook -o yaml
kubectl describe ingress webhook-ingress -n webhook

# Service確認
kubectl get svc -n webhook
kubectl describe svc webhook-service -n webhook

# Pod確認
kubectl get pods -n webhook
kubectl describe pod webhook-nodejs-xxx -n webhook
kubectl logs webhook-nodejs-xxx -n webhook
```

#### 2. 署名検証エラー

**症状**: `INVALID_SIGNATURE` エラーが発生

**原因と解決法**:

```bash
# Webhook秘密鍵確認
kubectl get secret webhook-secrets -n webhook -o yaml | grep WEBHOOK_SECRET | base64 -d

# GitHubのWebhook設定確認
# 1. GitHub > Settings > Webhooks
# 2. Secret値が一致するか確認
# 3. Content typeが application/json になっているか確認

# ログでペイロードと署名を確認
kubectl logs -n webhook -l app=webhook-nodejs | grep signature
```

#### 3. Rate Limit超過

**症状**: `RATE_LIMIT_EXCEEDED` エラーが頻発

**原因と解決法**:

```bash
# 現在のRate Limit設定確認
kubectl get configmap webhook-config -n webhook -o yaml

# メトリクス確認
curl -s "http://prometheus.monitoring.svc.cluster.local:9090/api/v1/query?query=rate(webhook_requests_total[5m])"

# Rate Limit調整（必要に応じて）
kubectl patch configmap webhook-config -n webhook --type merge -p '{"data":{"RATE_LIMIT_PER_IP":"120"}}'
kubectl rollout restart deployment webhook-nodejs -n webhook
```

#### 4. メモリ不足

**症状**: Pod が `OOMKilled` でクラッシュする

**原因と解決法**:

```bash
# メモリ使用状況確認
kubectl top pods -n webhook --containers

# リソース制限確認
kubectl describe pod webhook-nodejs-xxx -n webhook | grep -A 10 "Limits:"

# メモリ制限を調整
kubectl patch deployment webhook-nodejs -n webhook --type merge -p '{"spec":{"template":{"spec":{"containers":[{"name":"webhook-nodejs","resources":{"limits":{"memory":"8Gi"},"requests":{"memory":"2Gi"}}}]}}}}'
```

### 緊急対応手順

#### 1. 緊急停止手順

```bash
#!/bin/bash
# emergency-stop.sh

echo "=== EMERGENCY STOP PROCEDURE ==="
echo "Timestamp: $(date)"
echo "Operator: $USER"
read -p "Confirm emergency stop? (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
    # トラフィック遮断
    kubectl scale deployment webhook-nodejs -n webhook --replicas=0
    
    # Ingress無効化
    kubectl patch ingress webhook-ingress -n webhook --type json -p='[{"op": "replace", "path": "/spec/rules", "value": []}]'
    
    # 通知
    curl -X POST "$SLACK_WEBHOOK_URL" -d '{"text": "🚨 EMERGENCY STOP: Webhook service has been stopped"}'
    
    echo "Emergency stop completed"
else
    echo "Emergency stop cancelled"
fi
```

#### 2. 緊急復旧手順

```bash
#!/bin/bash
# emergency-recovery.sh

echo "=== EMERGENCY RECOVERY PROCEDURE ==="
echo "Timestamp: $(date)"
echo "Operator: $USER"

# ヘルスチェック
kubectl get nodes
kubectl get pods -n webhook

# サービス復旧
kubectl scale deployment webhook-nodejs -n webhook --replicas=3
kubectl rollout status deployment webhook-nodejs -n webhook

# Ingress復旧
kubectl apply -f ingress.yaml

# 疎通確認
sleep 30
curl -f https://webhook.sas-com.internal/health

# 通知
curl -X POST "$SLACK_WEBHOOK_URL" -d '{"text": "✅ RECOVERY: Webhook service has been restored"}'

echo "Emergency recovery completed"
```

## 🛡️ セキュリティ運用

### セキュリティ監査

#### 1. 定期セキュリティスキャン

```bash
#!/bin/bash
# security-scan.sh

echo "=== Security Scan ==="
date

# コンテナ脆弱性スキャン
echo "Container Vulnerability Scan:"
trivy image sas-com/webhook-nodejs:latest --severity HIGH,CRITICAL --format json

# Kubernetes設定スキャン
echo "Kubernetes Security Scan:"
kube-bench --targets node,policies,managedservices

# Network Policy監査
echo "Network Policy Audit:"
kubectl get networkpolicy -A -o yaml | grep -A 10 -B 5 "policyTypes"

# RBAC監査
echo "RBAC Audit:"
kubectl auth can-i --list --as=system:serviceaccount:webhook:default

# Secret監査
echo "Secret Audit:"
kubectl get secrets -n webhook -o custom-columns="NAME:.metadata.name,TYPE:.type,DATA:.data"
```

#### 2. アクセス監査

```bash
#!/bin/bash
# access-audit.sh

echo "=== Access Audit ==="
date

# 異常なアクセスパターン検出
curl -s "http://elasticsearch.logging.svc.cluster.local:9200/webhook-logs-*/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "bool": {
        "must": [
          {"range": {"@timestamp": {"gte": "now-24h"}}},
          {"terms": {"level": ["error", "warn"]}}
        ]
      }
    },
    "aggs": {
      "top_error_ips": {
        "terms": {"field": "client_ip", "size": 20}
      },
      "error_types": {
        "terms": {"field": "fields.error_type", "size": 10}
      }
    }
  }'

# 地理的アクセス分析
echo "Geographic Access Analysis:"
# GeoIP分析実装

# 時間パターン分析
echo "Time Pattern Analysis:"
# アクセス時間パターン分析実装
```

### インシデント対応

#### 1. セキュリティインシデント検知

```bash
#!/bin/bash
# incident-detection.sh

# リアルタイム脅威検知
echo "=== Real-time Threat Detection ==="

# 異常な大量リクエスト
CURRENT_RATE=$(curl -s "http://prometheus.monitoring.svc.cluster.local:9090/api/v1/query?query=rate(webhook_requests_total[1m])" | jq '.data.result[0].value[1] | tonumber')

if (( $(echo "$CURRENT_RATE > 100" | bc -l) )); then
    echo "🚨 ALERT: Abnormally high request rate detected: $CURRENT_RATE req/s"
    # アラート通知実装
fi

# 不審なペイロードパターン
SUSPICIOUS_PATTERNS=$(curl -s "http://elasticsearch.logging.svc.cluster.local:9200/webhook-logs-*/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "bool": {
        "must": [
          {"range": {"@timestamp": {"gte": "now-5m"}}},
          {"term": {"fields.sensitive_data_detected": true}}
        ]
      }
    }
  }' | jq '.hits.total.value')

if [ "$SUSPICIOUS_PATTERNS" -gt "0" ]; then
    echo "🚨 ALERT: Sensitive data patterns detected: $SUSPICIOUS_PATTERNS events"
    # インシデント対応手順実行
fi
```

#### 2. 自動対応アクション

```bash
#!/bin/bash
# auto-response.sh

# IP自動ブロック機能
block_suspicious_ip() {
    local IP=$1
    echo "Blocking suspicious IP: $IP"
    
    # iptables ルール追加（実際の環境に応じて調整）
    # kubectl exec -n kube-system iptables-pod -- iptables -A INPUT -s $IP -j DROP
    
    # または Ingress Controller レベルでブロック
    kubectl patch configmap nginx-configuration -n ingress-nginx --type merge -p "{\"data\":{\"block-cidrs\":\"$IP\"}}"
}

# Rate Limit動的調整
adjust_rate_limit() {
    local NEW_LIMIT=$1
    echo "Adjusting rate limit to: $NEW_LIMIT"
    
    kubectl patch configmap webhook-config -n webhook --type merge -p "{\"data\":{\"RATE_LIMIT_PER_IP\":\"$NEW_LIMIT\"}}"
    kubectl rollout restart deployment webhook-nodejs -n webhook
}

# 緊急メンテナンスモード
emergency_maintenance_mode() {
    echo "Activating emergency maintenance mode"
    
    # メンテナンス用のPodをデプロイ
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: maintenance-page
  namespace: webhook
spec:
  replicas: 1
  selector:
    matchLabels:
      app: maintenance-page
  template:
    metadata:
      labels:
        app: maintenance-page
    spec:
      containers:
      - name: maintenance
        image: nginx:alpine
        ports:
        - containerPort: 80
        volumeMounts:
        - name: maintenance-config
          mountPath: /etc/nginx/conf.d
      volumes:
      - name: maintenance-config
        configMap:
          name: maintenance-config
EOF

    # Ingress を maintenance page に切り替え
    kubectl patch ingress webhook-ingress -n webhook --type json -p='[{"op": "replace", "path": "/spec/rules/0/http/paths/0/backend/service/name", "value": "maintenance-page"}]'
}
```

## 🔄 災害復旧

### RTO/RPO目標

| 災害レベル | RTO (復旧時間目標) | RPO (データ損失許容) | 対応手順 |
|-----------|-------------------|---------------------|----------|
| **レベル1** | 5分 | 0分 | 自動フェイルオーバー |
| **レベル2** | 30分 | 5分 | 手動切り替え |
| **レベル3** | 4時間 | 30分 | 完全復旧 |
| **レベル4** | 24時間 | 4時間 | 完全再構築 |

### バックアップ戦略

#### 1. データバックアップ

```yaml
# PostgreSQL バックアップ設定
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: webhook
spec:
  schedule: "0 2 * * *"  # 毎日午前2時
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: postgres-backup
            image: postgres:13
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
            command:
            - /bin/bash
            - -c
            - |
              BACKUP_FILE="webhook-db-$(date +%Y%m%d-%H%M%S).sql"
              pg_dump -h postgres.webhook.svc.cluster.local -U webhook webhook > /backup/$BACKUP_FILE
              # S3/Azure Blob/GCS にアップロード
              aws s3 cp /backup/$BACKUP_FILE s3://sas-webhook-backups/database/
            volumeMounts:
            - name: backup-storage
              mountPath: /backup
          volumes:
          - name: backup-storage
            emptyDir: {}
          restartPolicy: OnFailure
```

#### 2. 設定バックアップ

```bash
#!/bin/bash
# backup-config.sh

echo "=== Configuration Backup ==="
date

BACKUP_DIR="/backup/config-$(date +%Y%m%d-%H%M%S)"
mkdir -p $BACKUP_DIR

# Kubernetes設定バックアップ
kubectl get all -n webhook -o yaml > $BACKUP_DIR/webhook-resources.yaml
kubectl get configmap -n webhook -o yaml > $BACKUP_DIR/configmaps.yaml
kubectl get secret -n webhook -o yaml > $BACKUP_DIR/secrets.yaml
kubectl get ingress -n webhook -o yaml > $BACKUP_DIR/ingress.yaml
kubectl get networkpolicy -n webhook -o yaml > $BACKUP_DIR/network-policies.yaml

# Helm values バックアップ
helm get values prometheus -n monitoring > $BACKUP_DIR/prometheus-values.yaml
helm get values grafana -n monitoring > $BACKUP_DIR/grafana-values.yaml

# 設定ファイル圧縮
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR

# クラウドストレージにアップロード
aws s3 cp $BACKUP_DIR.tar.gz s3://sas-webhook-backups/config/

echo "Configuration backup completed: $BACKUP_DIR.tar.gz"
```

### 復旧手順

#### 1. 完全災害復旧

```bash
#!/bin/bash
# disaster-recovery.sh

echo "=== DISASTER RECOVERY PROCEDURE ==="
echo "Timestamp: $(date)"
echo "Operator: $USER"

# 前提条件確認
echo "Checking prerequisites..."
kubectl cluster-info
aws sts get-caller-identity

# 1. インフラ復旧
echo "Step 1: Infrastructure Recovery"

# Kubernetes クラスター復旧
if ! kubectl get nodes; then
    echo "Creating new Kubernetes cluster..."
    eksctl create cluster -f cluster-config.yaml
    aws eks update-kubeconfig --region ap-northeast-1 --name sas-webhook-cluster
fi

# 必須コンポーネント復旧
echo "Installing essential components..."
helm install nginx-ingress ingress-nginx/ingress-nginx --namespace ingress-nginx --create-namespace
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# 2. データベース復旧
echo "Step 2: Database Recovery"

# 最新バックアップを取得
LATEST_BACKUP=$(aws s3 ls s3://sas-webhook-backups/database/ | sort | tail -n 1 | awk '{print $4}')
echo "Restoring from backup: $LATEST_BACKUP"

# PostgreSQL復旧
kubectl apply -f postgres-deployment.yaml
kubectl wait --for=condition=ready pod -l app=postgres -n webhook --timeout=300s

# データ復元
kubectl exec -n webhook postgres-0 -- psql -U webhook -c "DROP DATABASE IF EXISTS webhook;"
kubectl exec -n webhook postgres-0 -- psql -U webhook -c "CREATE DATABASE webhook;"
aws s3 cp s3://sas-webhook-backups/database/$LATEST_BACKUP /tmp/
kubectl cp /tmp/$LATEST_BACKUP webhook/postgres-0:/tmp/
kubectl exec -n webhook postgres-0 -- psql -U webhook webhook < /tmp/$LATEST_BACKUP

# 3. アプリケーション復旧
echo "Step 3: Application Recovery"

# 設定復旧
LATEST_CONFIG=$(aws s3 ls s3://sas-webhook-backups/config/ | sort | tail -n 1 | awk '{print $4}')
aws s3 cp s3://sas-webhook-backups/config/$LATEST_CONFIG /tmp/
tar -xzf /tmp/$LATEST_CONFIG -C /tmp/

# Kubernetes リソース復旧
kubectl apply -f /tmp/config-*/webhook-resources.yaml
kubectl apply -f /tmp/config-*/configmaps.yaml
kubectl apply -f /tmp/config-*/secrets.yaml
kubectl apply -f /tmp/config-*/ingress.yaml

# 4. 監視システム復旧
echo "Step 4: Monitoring Recovery"

helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --values /tmp/config-*/prometheus-values.yaml

helm install grafana grafana/grafana \
  --namespace monitoring \
  --values /tmp/config-*/grafana-values.yaml

# 5. 疎通確認
echo "Step 5: Verification"

# Pod確認
kubectl get pods -n webhook
kubectl wait --for=condition=ready pod -l app=webhook-nodejs -n webhook --timeout=300s

# サービス確認
sleep 60
WEBHOOK_URL="https://webhook.sas-com.internal"
if curl -f $WEBHOOK_URL/health; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    exit 1
fi

# 6. 通知
echo "Step 6: Notification"

curl -X POST "$SLACK_WEBHOOK_URL" -d "{\"text\": \"✅ DISASTER RECOVERY COMPLETED\\nTimestamp: $(date)\\nOperator: $USER\\nRTO: $(date -d \"$START_TIME\" '+%H:%M:%S')\"}"

echo "=== DISASTER RECOVERY COMPLETED ==="
```

#### 2. データセンター切り替え

```bash
#!/bin/bash
# datacenter-failover.sh

echo "=== DATACENTER FAILOVER ==="

# プライマリDC停止確認
PRIMARY_DC="ap-northeast-1"
SECONDARY_DC="ap-southeast-1"

echo "Checking primary DC: $PRIMARY_DC"
if ! aws ec2 describe-availability-zones --region $PRIMARY_DC 2>/dev/null; then
    echo "Primary DC is unavailable, initiating failover to $SECONDARY_DC"
    
    # DNS切り替え
    aws route53 change-resource-record-sets --hosted-zone-id Z123456789 --change-batch '{
        "Changes": [{
            "Action": "UPSERT",
            "ResourceRecordSet": {
                "Name": "webhook.sas-com.internal",
                "Type": "CNAME",
                "TTL": 60,
                "ResourceRecords": [{"Value": "webhook-secondary.sas-com.internal"}]
            }
        }]
    }'
    
    # セカンダリDCでサービス開始
    aws eks update-kubeconfig --region $SECONDARY_DC --name sas-webhook-cluster-secondary
    kubectl scale deployment webhook-nodejs -n webhook --replicas=3
    
    echo "Failover completed to secondary DC: $SECONDARY_DC"
else
    echo "Primary DC is available, no failover needed"
fi
```

---

## 📞 緊急連絡先

### エスカレーション体制

| レベル | 対象 | 連絡先 | 対応時間 |
|--------|------|--------|----------|
| **L1 (Critical)** | 即座 | github@sas-com.com<br>090-xxxx-xxxx (オンコール) | 24/7 |
| **L2 (High)** | 1時間以内 | github@sas-com.com | 平日 9-18時 |
| **L3 (Medium)** | 4時間以内 | github@sas-com.com | 平日 9-18時 |
| **L4 (Low)** | 翌営業日 | github@sas-com.com | 平日 9-18時 |

### 外部ベンダー連絡先

- **AWS Support**: Enterprise サポート
- **GitHub Support**: Premium サポート
- **セキュリティベンダー**: SOC 24/7対応

---

**更新履歴**:
- 2025-09-10: 初版作成
- セキュリティレビュー: 承認待ち
- 次回更新予定: 2025-12-10

**関連ドキュメント**:
- [GITHUB_WEBHOOK_SECURITY_GUIDE.md](./GITHUB_WEBHOOK_SECURITY_GUIDE.md)
- [WEBHOOK_API_SPECIFICATION.md](./WEBHOOK_API_SPECIFICATION.md)

**担当者**:
- 運用設計: GitHub管理チーム
- セキュリティレビュー: セキュリティチーム
- 承認: CTO Office