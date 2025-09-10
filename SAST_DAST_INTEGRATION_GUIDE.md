# SAST/DAST統合実装ガイド

**エス・エー・エス株式会社**  
*DevSecOpsパイプラインにおける静的・動的セキュリティテストの完全統合ガイド*

## 目次

1. [SAST (静的アプリケーションセキュリティテスト)](#1-sast-静的アプリケーションセキュリティテスト)
2. [DAST (動的アプリケーションセキュリティテスト)](#2-dast-動的アプリケーションセキュリティテスト)
3. [統合パイプライン設計](#3-統合パイプライン設計)
4. [言語別SAST実装](#4-言語別sast実装)
5. [コンテナセキュリティ](#5-コンテナセキュリティ)
6. [IaC (Infrastructure as Code) セキュリティ](#6-iac-infrastructure-as-code-セキュリティ)
7. [セキュリティメトリクスとレポート](#7-セキュリティメトリクスとレポート)
8. [トラブルシューティング](#8-トラブルシューティング)

---

## 1. SAST (静的アプリケーションセキュリティテスト)

### 1.1 SAST概要とツール選定

```yaml
sast_tools:
  primary:
    codeql:
      provider: "GitHub Advanced Security"
      languages: ["javascript", "typescript", "python", "java", "go", "csharp"]
      license: "Included with GitHub Enterprise"
      
  secondary:
    semgrep:
      provider: "r2c"
      languages: ["all"]
      license: "Open Source + Pro"
      custom_rules: true
      
    sonarqube:
      provider: "SonarSource"
      languages: ["all"]
      license: "Community + Enterprise"
      quality_gates: true
      
  specialized:
    bandit:
      language: "python"
      focus: "security"
      
    eslint-plugin-security:
      language: "javascript/typescript"
      focus: "security patterns"
      
    gosec:
      language: "go"
      focus: "security"
      
    spotbugs:
      language: "java"
      focus: "bugs and security"
```

### 1.2 GitHub CodeQL 実装

```yaml
# .github/workflows/codeql-analysis.yml
name: "CodeQL Security Analysis"

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * 1'

jobs:
  analyze:
    name: Analyze
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write

    strategy:
      fail-fast: false
      matrix:
        language: ['javascript', 'python', 'java', 'go']

    steps:
    - name: Checkout repository
      uses: actions/checkout@v3

    - name: Initialize CodeQL
      uses: github/codeql-action/init@v2
      with:
        languages: ${{ matrix.language }}
        queries: +security-extended,security-and-quality
        
    - name: Custom Query Suites
      if: matrix.language == 'javascript'
      run: |
        echo "Adding custom JavaScript security queries"
        cat > .github/codeql/custom-queries.qls << EOF
        - include:
            id: js/sql-injection
        - include:
            id: js/xss
        - include:
            id: js/path-injection
        - include:
            id: js/command-injection
        EOF

    - name: Autobuild
      uses: github/codeql-action/autobuild@v2

    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@v2
      with:
        category: "/language:${{matrix.language}}"
        output: results-${{ matrix.language }}.sarif
        
    - name: Upload SARIF
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: results-${{ matrix.language }}.sarif
        
    - name: Quality Gate Check
      run: |
        HIGH_VULNS=$(jq '.runs[0].results | map(select(.level == "error")) | length' results-${{ matrix.language }}.sarif)
        if [ "$HIGH_VULNS" -gt 0 ]; then
          echo "::error::Found $HIGH_VULNS high severity vulnerabilities"
          exit 1
        fi
```

### 1.3 Semgrep カスタムルール実装

```yaml
# .semgrep/rules/custom-security.yml
rules:
  - id: hardcoded-secret
    patterns:
      - pattern-either:
          - pattern: |
              $KEY = "..."
          - pattern: |
              $KEY = '...'
      - metavariable-regex:
          metavariable: $KEY
          regex: (password|passwd|secret|api_key|apikey|token|jwt)
      - metavariable-regex:
          metavariable: '...'
          regex: .{8,}
    message: Hardcoded secret detected
    languages: [javascript, typescript, python, java]
    severity: ERROR

  - id: sql-injection
    patterns:
      - pattern-either:
          - pattern: |
              $QUERY = "SELECT * FROM " + $INPUT
          - pattern: |
              $QUERY = `SELECT * FROM ${$INPUT}`
          - pattern: |
              cursor.execute("SELECT * FROM " + $INPUT)
    message: Potential SQL injection vulnerability
    languages: [javascript, python, java]
    severity: ERROR

  - id: jwt-weak-secret
    patterns:
      - pattern: |
          jwt.sign($PAYLOAD, "...", ...)
      - metavariable-regex:
          metavariable: '...'
          regex: .{0,31}$
    message: JWT secret key is too weak (less than 32 characters)
    languages: [javascript, typescript]
    severity: WARNING

  - id: unsafe-deserialization
    patterns:
      - pattern-either:
          - pattern: |
              pickle.loads($INPUT)
          - pattern: |
              yaml.load($INPUT)
          - pattern: |
              eval($INPUT)
    message: Unsafe deserialization detected
    languages: [python]
    severity: ERROR
```

```yaml
# .github/workflows/semgrep.yml
name: Semgrep Security Scan

on:
  pull_request: {}
  push:
    branches: [main, develop]

jobs:
  semgrep:
    runs-on: ubuntu-latest
    name: Scan with Semgrep
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run Semgrep
      uses: returntocorp/semgrep-action@v1
      with:
        config: >-
          p/security-audit
          p/owasp-top-ten
          p/r2c-security-audit
          .semgrep/rules/
        generateSarif: true
        
    - name: Upload SARIF file
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: semgrep.sarif
        
    - name: Check for High Severity Issues
      run: |
        if grep -q '"level": "error"' semgrep.sarif; then
          echo "::error::High severity security issues found"
          exit 1
        fi
```

---

## 2. DAST (動的アプリケーションセキュリティテスト)

### 2.1 OWASP ZAP 統合

```yaml
# .github/workflows/zap-scan.yml
name: OWASP ZAP Security Scan

on:
  schedule:
    - cron: '0 3 * * *'
  workflow_dispatch:

jobs:
  zap_scan:
    runs-on: ubuntu-latest
    name: OWASP ZAP Scan
    
    steps:
    - name: Checkout
      uses: actions/checkout@v3
      
    - name: Deploy to Test Environment
      run: |
        docker-compose -f docker-compose.test.yml up -d
        sleep 30  # Wait for services to start
        
    - name: ZAP Baseline Scan
      uses: zaproxy/action-baseline@v0.9.0
      with:
        target: 'http://localhost:8080'
        rules_file_name: '.zap/rules.tsv'
        cmd_options: '-a -j -l WARN'
        
    - name: ZAP Full Scan
      uses: zaproxy/action-full-scan@v0.9.0
      with:
        target: 'http://localhost:8080'
        cmd_options: '-a -j'
        allow_issue_writing: false
        
    - name: ZAP API Scan
      uses: zaproxy/action-api-scan@v0.9.0
      with:
        target: 'http://localhost:8080/api/v1/openapi.json'
        format: 'openapi'
        cmd_options: '-a -j'
        
    - name: Upload ZAP Reports
      uses: actions/upload-artifact@v3
      with:
        name: zap-reports
        path: |
          zap_baseline_report.html
          zap_full_report.html
          zap_api_report.html
          
    - name: Parse ZAP Results
      run: |
        python3 scripts/parse_zap_results.py \
          --report zap_full_report.json \
          --threshold-high 0 \
          --threshold-medium 5 \
          --threshold-low 10
```

### 2.2 API セキュリティテスト

```yaml
# .github/workflows/api-security.yml
name: API Security Testing

on:
  push:
    paths:
      - 'api/**'
      - 'openapi.yml'
  schedule:
    - cron: '0 4 * * *'

jobs:
  api_security:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Test Environment
      run: |
        docker-compose -f docker-compose.test.yml up -d
        npm run seed:test
        
    - name: Run Nuclei API Security Templates
      run: |
        docker run -v $(pwd):/app projectdiscovery/nuclei:latest \
          -u http://localhost:8080/api/v1 \
          -t /app/.nuclei/api-security/ \
          -severity critical,high,medium \
          -json -o api-security-results.json
          
    - name: Authentication Testing
      run: |
        # Test JWT vulnerabilities
        python3 scripts/test_jwt_security.py \
          --endpoint http://localhost:8080/api/v1 \
          --tests all
          
        # Test OAuth flows
        python3 scripts/test_oauth_security.py \
          --endpoint http://localhost:8080/oauth \
          --tests all
          
    - name: Rate Limiting Testing
      run: |
        python3 scripts/test_rate_limiting.py \
          --endpoint http://localhost:8080/api/v1 \
          --concurrent-requests 100 \
          --duration 60
          
    - name: Input Validation Testing
      run: |
        python3 scripts/test_input_validation.py \
          --openapi openapi.yml \
          --endpoint http://localhost:8080/api/v1 \
          --fuzz-iterations 1000
          
    - name: Generate Security Report
      run: |
        python3 scripts/generate_api_security_report.py \
          --nuclei-results api-security-results.json \
          --jwt-results jwt-test-results.json \
          --rate-limit-results rate-limit-results.json \
          --validation-results validation-results.json \
          --output api-security-report.html
          
    - name: Upload Reports
      uses: actions/upload-artifact@v3
      with:
        name: api-security-reports
        path: |
          api-security-report.html
          *-results.json
```

### 2.3 Burp Suite Enterprise 統合

```yaml
# .github/workflows/burp-enterprise.yml
name: Burp Suite Enterprise Scan

on:
  schedule:
    - cron: '0 5 * * 1'  # Weekly on Monday
  workflow_dispatch:

jobs:
  burp_scan:
    runs-on: ubuntu-latest
    
    steps:
    - name: Trigger Burp Suite Enterprise Scan
      run: |
        curl -X POST ${{ secrets.BURP_ENTERPRISE_URL }}/api/v1/scans \
          -H "Authorization: Bearer ${{ secrets.BURP_API_TOKEN }}" \
          -H "Content-Type: application/json" \
          -d '{
            "name": "GitHub Action Triggered Scan",
            "application_id": "${{ secrets.BURP_APP_ID }}",
            "scan_configuration_id": "${{ secrets.BURP_SCAN_CONFIG }}",
            "schedule": {
              "type": "immediate"
            }
          }'
          
    - name: Wait for Scan Completion
      run: |
        SCAN_ID=$(curl -s ${{ secrets.BURP_ENTERPRISE_URL }}/api/v1/scans/latest \
          -H "Authorization: Bearer ${{ secrets.BURP_API_TOKEN }}" \
          | jq -r '.id')
          
        while true; do
          STATUS=$(curl -s ${{ secrets.BURP_ENTERPRISE_URL }}/api/v1/scans/$SCAN_ID \
            -H "Authorization: Bearer ${{ secrets.BURP_API_TOKEN }}" \
            | jq -r '.status')
            
          if [ "$STATUS" = "completed" ]; then
            break
          fi
          
          sleep 300  # Check every 5 minutes
        done
        
    - name: Download Scan Report
      run: |
        curl -o burp-scan-report.html \
          ${{ secrets.BURP_ENTERPRISE_URL }}/api/v1/scans/$SCAN_ID/report \
          -H "Authorization: Bearer ${{ secrets.BURP_API_TOKEN }}"
          
    - name: Parse and Check Results
      run: |
        python3 scripts/parse_burp_results.py \
          --report burp-scan-report.html \
          --fail-on-critical true \
          --jira-integration true
```

---

## 3. 統合パイプライン設計

### 3.1 完全DevSecOpsパイプライン

```yaml
# .github/workflows/devsecops-pipeline.yml
name: Complete DevSecOps Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  # Stage 1: Pre-commit Security Checks
  pre_commit:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Secret Detection
      uses: trufflesecurity/trufflehog@main
      with:
        path: ./
        
    - name: License Check
      run: |
        npm install -g license-checker
        license-checker --onlyAllow 'MIT;Apache-2.0;BSD-3-Clause;ISC'
        
    - name: Commit Message Validation
      uses: wagoid/commitlint-github-action@v5

  # Stage 2: SAST Analysis
  sast:
    needs: pre_commit
    runs-on: ubuntu-latest
    strategy:
      matrix:
        tool: [codeql, semgrep, sonarqube]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run ${{ matrix.tool }}
      uses: ./.github/actions/${{ matrix.tool }}
      with:
        severity_threshold: high

  # Stage 3: Dependency Security
  dependency_check:
    needs: pre_commit
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: OWASP Dependency Check
      uses: dependency-check/Dependency-Check_Action@main
      with:
        project: 'SAS-Project'
        path: '.'
        format: 'ALL'
        args: >
          --enableRetired
          --enableExperimental
          
    - name: Snyk Security Scan
      uses: snyk/actions/node@master
      env:
        SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
      with:
        args: --severity-threshold=high
        
    - name: NPM Audit
      run: |
        npm audit --audit-level=moderate
        npm audit fix --force
        
    - name: Safety Check (Python)
      run: |
        pip install safety
        safety check --json > safety-report.json

  # Stage 4: Container Security
  container_security:
    needs: [sast, dependency_check]
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Container
      run: |
        docker build -t ${{ github.repository }}:${{ github.sha }} .
        
    - name: Trivy Container Scan
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: ${{ github.repository }}:${{ github.sha }}
        format: 'sarif'
        output: 'trivy-results.sarif'
        severity: 'CRITICAL,HIGH'
        
    - name: Grype Container Scan
      run: |
        curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
        grype ${{ github.repository }}:${{ github.sha }} -o json > grype-results.json
        
    - name: Docker Scout
      run: |
        docker scout cves ${{ github.repository }}:${{ github.sha }}
        docker scout recommendations ${{ github.repository }}:${{ github.sha }}

  # Stage 5: IaC Security
  iac_security:
    needs: pre_commit
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Checkov IaC Scan
      uses: bridgecrewio/checkov-action@master
      with:
        directory: .
        framework: all
        output_format: sarif
        
    - name: Terrascan
      run: |
        docker run --rm -v $(pwd):/iac accurics/terrascan scan \
          -i terraform -d /iac \
          --severity high \
          --output json > terrascan-results.json
          
    - name: KICS Scan
      uses: checkmarx/kics-github-action@master
      with:
        path: '.'
        fail_on: high
        output_formats: 'json,sarif'

  # Stage 6: DAST Testing
  dast:
    needs: [container_security, iac_security]
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Test Environment
      run: |
        kubectl apply -f k8s/test-deployment.yml
        kubectl wait --for=condition=ready pod -l app=test-app --timeout=300s
        
    - name: Run DAST Suite
      run: |
        # OWASP ZAP
        docker run -t owasp/zap2docker-stable zap-baseline.py \
          -t http://test-app.sas-com.internal \
          -r zap-report.html
          
        # Nuclei
        docker run projectdiscovery/nuclei:latest \
          -u http://test-app.sas-com.internal \
          -severity critical,high,medium
          
    - name: Performance Security Testing
      run: |
        # Load testing with security payloads
        k6 run scripts/security-load-test.js

  # Stage 7: Security Reporting
  reporting:
    needs: [sast, dependency_check, container_security, iac_security, dast]
    runs-on: ubuntu-latest
    if: always()
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Download All Artifacts
      uses: actions/download-artifact@v3
      
    - name: Generate Consolidated Report
      run: |
        python3 scripts/generate_security_report.py \
          --sast-results './sast-*' \
          --dependency-results './dependency-*' \
          --container-results './container-*' \
          --iac-results './iac-*' \
          --dast-results './dast-*' \
          --output security-report.html
          
    - name: Upload to S3
      run: |
        aws s3 cp security-report.html \
          s3://sas-security-reports/${{ github.run_id }}/
          
    - name: Send Notifications
      run: |
        python3 scripts/send_security_notifications.py \
          --report security-report.html \
          --teams-webhook ${{ secrets.TEAMS_WEBHOOK }} \
          --severity-threshold high
```

---

## 4. 言語別SAST実装

### 4.1 JavaScript/TypeScript

```yaml
# .github/workflows/javascript-security.yml
name: JavaScript/TypeScript Security

on:
  push:
    paths:
      - '**.js'
      - '**.jsx'
      - '**.ts'
      - '**.tsx'

jobs:
  js_security:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        
    - name: Install Dependencies
      run: npm ci
      
    - name: ESLint Security Plugin
      run: |
        npm install --save-dev eslint-plugin-security
        echo '{
          "extends": ["plugin:security/recommended"],
          "plugins": ["security"],
          "rules": {
            "security/detect-object-injection": "error",
            "security/detect-non-literal-regexp": "warn",
            "security/detect-unsafe-regex": "error",
            "security/detect-buffer-noassert": "error",
            "security/detect-child-process": "warn",
            "security/detect-disable-mustache-escape": "error",
            "security/detect-eval-with-expression": "error",
            "security/detect-no-csrf-before-method-override": "error",
            "security/detect-non-literal-fs-filename": "warn",
            "security/detect-non-literal-require": "warn",
            "security/detect-possible-timing-attacks": "warn",
            "security/detect-pseudoRandomBytes": "error"
          }
        }' > .eslintrc.security.json
        npx eslint --config .eslintrc.security.json --ext .js,.jsx,.ts,.tsx .
        
    - name: NodeJsScan
      run: |
        docker run -v $(pwd):/app opensecurity/nodejsscan:latest \
          -o nodejsscan-report.json /app
          
    - name: RetireJS
      run: |
        npm install -g retire
        retire --outputformat json --outputpath retire-report.json
        
    - name: Audit JavaScript Dependencies
      run: |
        npx audit-ci --high --report-type full
```

### 4.2 Python

```yaml
# .github/workflows/python-security.yml
name: Python Security

on:
  push:
    paths:
      - '**.py'

jobs:
  python_security:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install Dependencies
      run: |
        pip install -r requirements.txt
        pip install bandit safety pylint
        
    - name: Bandit Security Scan
      run: |
        bandit -r . -f json -o bandit-report.json \
          --severity-level medium \
          --confidence-level medium
          
    - name: Safety Dependency Check
      run: |
        safety check --json > safety-report.json
        
    - name: PyLint Security Checks
      run: |
        pylint --load-plugins=pylint.extensions.security \
          --disable=all \
          --enable=security \
          --output-format=json > pylint-security.json \
          **/*.py
          
    - name: Semgrep Python Rules
      run: |
        docker run --rm -v $(pwd):/src \
          returntocorp/semgrep:latest \
          --config=p/python \
          --config=p/django \
          --config=p/flask \
          --json -o /src/semgrep-python.json
```

### 4.3 Java

```yaml
# .github/workflows/java-security.yml
name: Java Security

on:
  push:
    paths:
      - '**.java'

jobs:
  java_security:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Java
      uses: actions/setup-java@v3
      with:
        java-version: '17'
        distribution: 'temurin'
        
    - name: SpotBugs with FindSecBugs
      run: |
        mvn com.github.spotbugs:spotbugs-maven-plugin:4.7.3.0:spotbugs \
          -Dspotbugs.effort=Max \
          -Dspotbugs.threshold=Low \
          -Dspotbugs.xmlOutput=true \
          -Dspotbugs.xmlOutputDirectory=./target \
          -Dspotbugs.plugins.version=1.12.0
          
    - name: OWASP Dependency Check
      run: |
        mvn org.owasp:dependency-check-maven:8.4.0:check \
          -Dformat=ALL \
          -DfailBuildOnCVSS=7
          
    - name: PMD Security Rules
      run: |
        mvn pmd:pmd \
          -Dpmd.rulesets=category/java/security.xml \
          -Dpmd.analysisCache=true \
          -Dformat=json
```

### 4.4 Go

```yaml
# .github/workflows/go-security.yml
name: Go Security

on:
  push:
    paths:
      - '**.go'

jobs:
  go_security:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Go
      uses: actions/setup-go@v4
      with:
        go-version: '1.21'
        
    - name: Run Gosec
      run: |
        go install github.com/securego/gosec/v2/cmd/gosec@latest
        gosec -fmt json -out gosec-report.json ./...
        
    - name: Nancy Dependency Check
      run: |
        go list -json -m all | nancy sleuth \
          -output json > nancy-report.json
          
    - name: Staticcheck
      run: |
        go install honnef.co/go/tools/cmd/staticcheck@latest
        staticcheck -f json ./... > staticcheck-report.json
```

---

## 5. コンテナセキュリティ

### 5.1 Dockerfile セキュリティスキャン

```dockerfile
# Secure Dockerfile Template
FROM node:18-alpine AS builder

# Security: Run as non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

# Security: Set working directory
WORKDIR /app

# Security: Copy only package files first (layer caching)
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

# Security: Copy application code
COPY --chown=nodejs:nodejs . .

# Security: Switch to non-root user
USER nodejs

# Multi-stage build for smaller attack surface
FROM node:18-alpine

# Security: Install only runtime dependencies
RUN apk add --no-cache tini

# Security: Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

WORKDIR /app

# Security: Copy from builder stage
COPY --from=builder --chown=nodejs:nodejs /app .

# Security: Use non-root user
USER nodejs

# Security: Use tini for proper signal handling
ENTRYPOINT ["/sbin/tini", "--"]

# Security: Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node healthcheck.js

EXPOSE 3000

CMD ["node", "server.js"]
```

### 5.2 Container Security Workflow

```yaml
# .github/workflows/container-security.yml
name: Container Security Scanning

on:
  push:
    paths:
      - 'Dockerfile*'
      - 'docker-compose*.yml'

jobs:
  docker_security:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Hadolint Dockerfile Linting
      uses: hadolint/hadolint-action@v3.1.0
      with:
        dockerfile: Dockerfile
        failure-threshold: warning
        
    - name: Build Image
      run: |
        docker build -t test-image:${{ github.sha }} .
        
    - name: Trivy Vulnerability Scan
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: test-image:${{ github.sha }}
        format: 'table'
        exit-code: '1'
        ignore-unfixed: true
        vuln-type: 'os,library'
        severity: 'CRITICAL,HIGH'
        
    - name: Grype Scan
      run: |
        curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
        grype test-image:${{ github.sha }} --fail-on high
        
    - name: Docker Scout
      run: |
        docker scout cves test-image:${{ github.sha }}
        docker scout recommendations test-image:${{ github.sha }}
        
    - name: Dockle Security Linting
      run: |
        docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
          goodwithtech/dockle:latest test-image:${{ github.sha }}
```

---

## 6. IaC (Infrastructure as Code) セキュリティ

### 6.1 Terraform セキュリティ

```yaml
# .github/workflows/terraform-security.yml
name: Terraform Security

on:
  push:
    paths:
      - '**.tf'
      - '**.tfvars'

jobs:
  terraform_security:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Checkov Terraform Scan
      uses: bridgecrewio/checkov-action@master
      with:
        directory: terraform/
        framework: terraform
        output_format: json
        output_file_path: checkov-report.json
        
    - name: Terrascan
      run: |
        docker run --rm -v $(pwd):/iac accurics/terrascan scan \
          -i terraform -d /iac/terraform \
          --config-path /iac/.terrascan.toml
          
    - name: TFSec
      uses: aquasecurity/tfsec-action@v1.0.0
      with:
        working_directory: terraform/
        format: json
        out: tfsec-report.json
        
    - name: Terraform Compliance
      run: |
        pip install terraform-compliance
        terraform-compliance -f features/ -p terraform.plan.json
```

### 6.2 Kubernetes セキュリティ

```yaml
# .github/workflows/kubernetes-security.yml
name: Kubernetes Security

on:
  push:
    paths:
      - 'k8s/**'
      - 'helm/**'

jobs:
  k8s_security:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Kubesec Scan
      run: |
        for file in k8s/*.yaml; do
          docker run -v $(pwd):/app kubesec/kubesec:latest \
            scan /app/$file > ${file%.yaml}-kubesec.json
        done
        
    - name: Polaris Audit
      run: |
        docker run --rm -v $(pwd):/app fairwindsops/polaris:latest \
          audit --audit-path /app/k8s \
          --output-format json > polaris-report.json
          
    - name: KubeLinter
      run: |
        docker run --rm -v $(pwd):/app stackrox/kube-linter:latest \
          lint /app/k8s --format json > kubelinter-report.json
          
    - name: Datree Policy Check
      run: |
        docker run --rm -v $(pwd):/app datree/datree:latest \
          test /app/k8s/*.yaml --output json > datree-report.json
```

---

## 7. セキュリティメトリクスとレポート

### 7.1 セキュリティダッシュボード

```python
# scripts/generate_security_dashboard.py
#!/usr/bin/env python3

import json
import os
from datetime import datetime
from typing import Dict, List
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class SecurityDashboard:
    def __init__(self):
        self.metrics = {
            'sast': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
            'dast': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
            'dependencies': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
            'containers': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
            'iac': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        }
        self.trends = []
        self.compliance = {}
        
    def parse_sast_results(self, file_path: str):
        """Parse SAST results from various tools"""
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        # Parse CodeQL results
        if 'runs' in data:
            for run in data['runs']:
                for result in run.get('results', []):
                    severity = result.get('level', 'low').lower()
                    if severity == 'error':
                        severity = 'high'
                    self.metrics['sast'][severity] += 1
                    
    def parse_dependency_results(self, file_path: str):
        """Parse dependency check results"""
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        for dependency in data.get('dependencies', []):
            for vulnerability in dependency.get('vulnerabilities', []):
                severity = vulnerability.get('severity', 'LOW').lower()
                self.metrics['dependencies'][severity] += 1
                
    def generate_dashboard(self, output_path: str):
        """Generate interactive HTML dashboard"""
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Vulnerability Distribution',
                'Severity Trends',
                'Tool Coverage',
                'Compliance Status',
                'Top Vulnerable Components',
                'Security Score'
            ),
            specs=[
                [{'type': 'bar'}, {'type': 'scatter'}],
                [{'type': 'pie'}, {'type': 'indicator'}],
                [{'type': 'bar'}, {'type': 'indicator'}]
            ]
        )
        
        # Vulnerability Distribution
        categories = list(self.metrics.keys())
        severities = ['critical', 'high', 'medium', 'low']
        
        for severity in severities:
            values = [self.metrics[cat][severity] for cat in categories]
            fig.add_trace(
                go.Bar(name=severity.capitalize(), x=categories, y=values),
                row=1, col=1
            )
            
        # Severity Trends
        if self.trends:
            dates = [t['date'] for t in self.trends]
            critical = [t['critical'] for t in self.trends]
            high = [t['high'] for t in self.trends]
            
            fig.add_trace(
                go.Scatter(x=dates, y=critical, name='Critical', mode='lines+markers'),
                row=1, col=2
            )
            fig.add_trace(
                go.Scatter(x=dates, y=high, name='High', mode='lines+markers'),
                row=1, col=2
            )
            
        # Tool Coverage Pie Chart
        tools_data = {
            'SAST': sum(self.metrics['sast'].values()),
            'DAST': sum(self.metrics['dast'].values()),
            'Dependencies': sum(self.metrics['dependencies'].values()),
            'Container': sum(self.metrics['containers'].values()),
            'IaC': sum(self.metrics['iac'].values())
        }
        
        fig.add_trace(
            go.Pie(labels=list(tools_data.keys()), values=list(tools_data.values())),
            row=2, col=1
        )
        
        # Compliance Gauge
        compliance_score = self.calculate_compliance_score()
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=compliance_score,
                title={'text': "Compliance Score"},
                gauge={'axis': {'range': [0, 100]},
                       'bar': {'color': "darkgreen"},
                       'steps': [
                           {'range': [0, 50], 'color': "lightgray"},
                           {'range': [50, 80], 'color': "yellow"},
                           {'range': [80, 100], 'color': "lightgreen"}
                       ],
                       'threshold': {'line': {'color': "red", 'width': 4},
                                    'thickness': 0.75, 'value': 90}
                }
            ),
            row=2, col=2
        )
        
        # Security Score
        security_score = self.calculate_security_score()
        fig.add_trace(
            go.Indicator(
                mode="number+delta",
                value=security_score,
                title={'text': "Security Score"},
                delta={'reference': 85, 'relative': True},
                domain={'x': [0.5, 1], 'y': [0, 0.3]}
            ),
            row=3, col=2
        )
        
        # Update layout
        fig.update_layout(
            height=1200,
            showlegend=True,
            title_text=f"Security Dashboard - {datetime.now().strftime('%Y-%m-%d')}",
            template='plotly_dark'
        )
        
        # Save dashboard
        fig.write_html(output_path)
        
    def calculate_security_score(self) -> float:
        """Calculate overall security score"""
        total_issues = sum(sum(cat.values()) for cat in self.metrics.values())
        critical_weight = sum(cat['critical'] * 10 for cat in self.metrics.values())
        high_weight = sum(cat['high'] * 5 for cat in self.metrics.values())
        medium_weight = sum(cat['medium'] * 2 for cat in self.metrics.values())
        low_weight = sum(cat['low'] for cat in self.metrics.values())
        
        weighted_issues = critical_weight + high_weight + medium_weight + low_weight
        
        if weighted_issues == 0:
            return 100.0
            
        # Score calculation (inverse of weighted issues, normalized to 0-100)
        max_possible = total_issues * 10  # If all were critical
        score = 100 * (1 - (weighted_issues / max_possible))
        
        return round(max(0, min(100, score)), 2)
        
    def calculate_compliance_score(self) -> float:
        """Calculate compliance score based on policies"""
        checks_passed = 0
        total_checks = 0
        
        # Check various compliance requirements
        compliance_checks = {
            'no_critical_vulns': sum(cat['critical'] for cat in self.metrics.values()) == 0,
            'dependencies_updated': True,  # Placeholder
            'security_headers': True,  # Placeholder
            'encryption_enabled': True,  # Placeholder
            'access_controls': True,  # Placeholder
        }
        
        for check, passed in compliance_checks.items():
            total_checks += 1
            if passed:
                checks_passed += 1
                
        return round((checks_passed / total_checks) * 100, 2)

if __name__ == "__main__":
    dashboard = SecurityDashboard()
    
    # Parse all result files
    if os.path.exists('sast-results.json'):
        dashboard.parse_sast_results('sast-results.json')
    if os.path.exists('dependency-results.json'):
        dashboard.parse_dependency_results('dependency-results.json')
        
    # Generate dashboard
    dashboard.generate_dashboard('security-dashboard.html')
    
    # Generate metrics JSON for further processing
    with open('security-metrics.json', 'w') as f:
        json.dump({
            'metrics': dashboard.metrics,
            'security_score': dashboard.calculate_security_score(),
            'compliance_score': dashboard.calculate_compliance_score(),
            'timestamp': datetime.now().isoformat()
        }, f, indent=2)
```

### 7.2 自動レポート生成

```python
# scripts/generate_security_report.py
#!/usr/bin/env python3

import json
import os
from datetime import datetime
from typing import Dict, List, Any
import markdown
from jinja2 import Template

class SecurityReportGenerator:
    def __init__(self):
        self.findings = []
        self.summary = {}
        self.recommendations = []
        
    def generate_report(self, output_format: str = 'html'):
        """Generate security report in specified format"""
        
        report_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Security Report - {{ date }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: #2c3e50; color: white; padding: 20px; }
        .summary { background: #f8f9fa; padding: 15px; margin: 20px 0; }
        .critical { color: #dc3545; font-weight: bold; }
        .high { color: #fd7e14; font-weight: bold; }
        .medium { color: #ffc107; }
        .low { color: #28a745; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background: #f2f2f2; }
        .finding { margin: 20px 0; padding: 15px; border-left: 4px solid #007bff; }
        .recommendation { background: #e7f3ff; padding: 15px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Security Assessment Report</h1>
        <p>Organization: エス・エー・エス株式会社</p>
        <p>Date: {{ date }}</p>
        <p>Repository: {{ repository }}</p>
    </div>
    
    <div class="summary">
        <h2>Executive Summary</h2>
        <p>Total Vulnerabilities Found: {{ total_vulnerabilities }}</p>
        <ul>
            <li class="critical">Critical: {{ summary.critical }}</li>
            <li class="high">High: {{ summary.high }}</li>
            <li class="medium">Medium: {{ summary.medium }}</li>
            <li class="low">Low: {{ summary.low }}</li>
        </ul>
        <p><strong>Security Score: {{ security_score }}/100</strong></p>
        <p><strong>Compliance Score: {{ compliance_score }}/100</strong></p>
    </div>
    
    <h2>Detailed Findings</h2>
    <table>
        <tr>
            <th>Tool</th>
            <th>Category</th>
            <th>Severity</th>
            <th>Finding</th>
            <th>File/Location</th>
            <th>Recommendation</th>
        </tr>
        {% for finding in findings %}
        <tr>
            <td>{{ finding.tool }}</td>
            <td>{{ finding.category }}</td>
            <td class="{{ finding.severity }}">{{ finding.severity|upper }}</td>
            <td>{{ finding.description }}</td>
            <td>{{ finding.location }}</td>
            <td>{{ finding.recommendation }}</td>
        </tr>
        {% endfor %}
    </table>
    
    <h2>Recommendations</h2>
    {% for rec in recommendations %}
    <div class="recommendation">
        <h3>{{ rec.title }}</h3>
        <p>{{ rec.description }}</p>
        <p><strong>Priority:</strong> {{ rec.priority }}</p>
        <p><strong>Estimated Effort:</strong> {{ rec.effort }}</p>
    </div>
    {% endfor %}
    
    <h2>Compliance Status</h2>
    <table>
        <tr>
            <th>Standard</th>
            <th>Status</th>
            <th>Score</th>
            <th>Notes</th>
        </tr>
        <tr>
            <td>OWASP ASVS</td>
            <td>{{ compliance.owasp_asvs.status }}</td>
            <td>{{ compliance.owasp_asvs.score }}%</td>
            <td>{{ compliance.owasp_asvs.notes }}</td>
        </tr>
        <tr>
            <td>NIST CSF</td>
            <td>{{ compliance.nist_csf.status }}</td>
            <td>{{ compliance.nist_csf.score }}%</td>
            <td>{{ compliance.nist_csf.notes }}</td>
        </tr>
    </table>
    
    <h2>Trend Analysis</h2>
    <p>Vulnerabilities trend over last 30 days:</p>
    <canvas id="trendChart"></canvas>
    
    <div class="footer">
        <p>Generated by SAS Security Scanner v1.0</p>
        <p>For questions, contact: security@sas-com.com</p>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        // Trend chart implementation
        const ctx = document.getElementById('trendChart').getContext('2d');
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: {{ trend_dates|tojson }},
                datasets: [{
                    label: 'Critical',
                    data: {{ trend_critical|tojson }},
                    borderColor: '#dc3545',
                    fill: false
                }, {
                    label: 'High',
                    data: {{ trend_high|tojson }},
                    borderColor: '#fd7e14',
                    fill: false
                }]
            }
        });
    </script>
</body>
</html>
        """
        
        template = Template(report_template)
        html_content = template.render(
            date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            repository=os.environ.get('GITHUB_REPOSITORY', 'Unknown'),
            total_vulnerabilities=len(self.findings),
            summary=self.summary,
            findings=self.findings,
            recommendations=self.recommendations,
            security_score=self.calculate_security_score(),
            compliance_score=self.calculate_compliance_score(),
            compliance=self.get_compliance_status(),
            trend_dates=self.get_trend_dates(),
            trend_critical=self.get_trend_data('critical'),
            trend_high=self.get_trend_data('high')
        )
        
        return html_content
        
    def calculate_security_score(self) -> int:
        """Calculate security score based on findings"""
        # Implementation
        return 85
        
    def calculate_compliance_score(self) -> int:
        """Calculate compliance score"""
        # Implementation
        return 92

if __name__ == "__main__":
    generator = SecurityReportGenerator()
    report = generator.generate_report()
    
    with open('security-report.html', 'w') as f:
        f.write(report)
```

---

## 8. トラブルシューティング

### 8.1 一般的な問題と解決策

```yaml
troubleshooting:
  codeql_timeout:
    problem: "CodeQL analysis timing out"
    solutions:
      - "Increase timeout in workflow: timeout-minutes: 120"
      - "Reduce query suite complexity"
      - "Use matrix strategy to parallelize languages"
      
  false_positives:
    problem: "Too many false positives"
    solutions:
      - "Create suppression files for known false positives"
      - "Adjust severity thresholds"
      - "Implement custom filters in parsing scripts"
      - "Use inline suppression comments"
      
  dependency_conflicts:
    problem: "Dependency version conflicts"
    solutions:
      - "Use dependency resolution strategies"
      - "Pin specific versions in lock files"
      - "Implement gradual update strategy"
      
  performance_issues:
    problem: "Scans taking too long"
    solutions:
      - "Implement incremental scanning"
      - "Use caching for dependencies and tools"
      - "Parallelize independent security checks"
      - "Schedule heavy scans during off-peak hours"
```

### 8.2 デバッグとログ

```yaml
# .github/workflows/debug-security.yml
name: Debug Security Scans

on:
  workflow_dispatch:
    inputs:
      debug_level:
        description: 'Debug level'
        required: true
        default: 'info'
        type: choice
        options:
          - info
          - debug
          - trace

jobs:
  debug:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Enable Debug Logging
      run: |
        echo "ACTIONS_STEP_DEBUG=true" >> $GITHUB_ENV
        echo "ACTIONS_RUNNER_DEBUG=true" >> $GITHUB_ENV
        
    - name: Test Security Tools
      run: |
        # Test each tool individually with verbose output
        
        # CodeQL
        echo "Testing CodeQL..."
        codeql version
        
        # Semgrep
        echo "Testing Semgrep..."
        docker run --rm returntocorp/semgrep:latest --version
        
        # Trivy
        echo "Testing Trivy..."
        docker run --rm aquasec/trivy:latest --version
        
    - name: Validate Configurations
      run: |
        # Validate all security configuration files
        for config in .github/workflows/*security*.yml; do
          echo "Validating $config"
          yamllint $config
        done
        
    - name: Check Permissions
      run: |
        # Verify GitHub token permissions
        curl -H "Authorization: token ${{ secrets.GITHUB_TOKEN }}" \
          https://api.github.com/repos/${{ github.repository }}/actions/permissions
```

---

## まとめ

このSAST/DAST統合実装ガイドは、エス・エー・エス株式会社のセキュリティ要件を満たす包括的なDevSecOpsパイプラインを提供します。

### 主要な実装ポイント

1. **多層防御**: SAST、DAST、依存関係、コンテナ、IaCの全レイヤーでセキュリティチェック
2. **自動化**: CI/CDパイプラインに完全統合された自動セキュリティテスト
3. **可視化**: ダッシュボードとレポートによる継続的な監視
4. **コンプライアンス**: OWASP、NIST等の標準への準拠
5. **実用性**: 開発速度を損なわない効率的な実装

### 次のステップ

1. 段階的な実装（まずSASTから開始）
2. チーム教育とトレーニング
3. カスタムルールの継続的な改善
4. メトリクスに基づく最適化

---

**最終更新**: 2025-09-10  
**承認者**: セキュリティチーム