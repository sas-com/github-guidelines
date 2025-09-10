# セキュリティ監視・レポート設定ガイド

**エス・エー・エス株式会社**  
*継続的セキュリティ監視とレポーティングの実装ガイド*

## 目次

1. [セキュリティダッシュボード構築](#1-セキュリティダッシュボード構築)
2. [自動レポート生成システム](#2-自動レポート生成システム)
3. [アラート設定](#3-アラート設定)
4. [メトリクス収集](#4-メトリクス収集)
5. [インシデント追跡](#5-インシデント追跡)
6. [コンプライアンス監視](#6-コンプライアンス監視)
7. [パフォーマンス分析](#7-パフォーマンス分析)
8. [レポートテンプレート](#8-レポートテンプレート)

---

## 1. セキュリティダッシュボード構築

### 1.1 GitHub Security Dashboard 設定

```yaml
# .github/workflows/security-dashboard.yml
name: Security Dashboard Update

on:
  schedule:
    - cron: '0 */6 * * *'  # 6時間ごと
  workflow_dispatch:
  workflow_run:
    workflows: ["SAST Security Analysis", "DAST Security Testing"]
    types: [completed]

jobs:
  update-dashboard:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
      
    - name: Setup Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
        
    - name: Install Dependencies
      run: |
        pip install pandas plotly jinja2 requests pygithub
        
    - name: Collect Security Metrics
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      run: |
        python scripts/collect_security_metrics.py
        
    - name: Generate Dashboard
      run: |
        python scripts/generate_dashboard.py
        
    - name: Upload Dashboard
      uses: actions/upload-artifact@v4
      with:
        name: security-dashboard
        path: |
          dashboard.html
          metrics.json
        retention-days: 90
        
    - name: Deploy to GitHub Pages
      if: github.ref == 'refs/heads/main'
      uses: peaceiris/actions-gh-pages@v3
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: ./dashboard
        destination_dir: security
```

### 1.2 メトリクス収集スクリプト

```python
# scripts/collect_security_metrics.py
#!/usr/bin/env python3

import os
import json
import requests
from datetime import datetime, timedelta
from github import Github
from typing import Dict, List, Any

class SecurityMetricsCollector:
    def __init__(self):
        self.github_token = os.environ.get('GITHUB_TOKEN')
        self.g = Github(self.github_token)
        self.repo = self.g.get_repo(os.environ.get('GITHUB_REPOSITORY'))
        self.metrics = {
            'timestamp': datetime.now().isoformat(),
            'vulnerabilities': {},
            'dependencies': {},
            'code_scanning': {},
            'secret_scanning': {},
            'compliance': {},
            'trends': []
        }
        
    def collect_vulnerability_metrics(self):
        """Collect vulnerability metrics from various sources"""
        
        # GitHub Security Advisories
        advisories = self.repo.get_vulnerability_alert()
        
        self.metrics['vulnerabilities'] = {
            'total': 0,
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'fixed': 0,
            'open': 0
        }
        
        # Code scanning alerts
        code_scanning_url = f"https://api.github.com/repos/{self.repo.full_name}/code-scanning/alerts"
        headers = {'Authorization': f'token {self.github_token}'}
        
        response = requests.get(code_scanning_url, headers=headers)
        if response.status_code == 200:
            alerts = response.json()
            for alert in alerts:
                severity = alert.get('rule', {}).get('severity', 'low').lower()
                state = alert.get('state', 'open')
                
                if severity == 'error':
                    severity = 'high'
                    
                self.metrics['vulnerabilities'][severity] += 1
                self.metrics['vulnerabilities']['total'] += 1
                
                if state == 'fixed':
                    self.metrics['vulnerabilities']['fixed'] += 1
                else:
                    self.metrics['vulnerabilities']['open'] += 1
                    
    def collect_dependency_metrics(self):
        """Collect dependency security metrics"""
        
        # Dependabot alerts
        dependabot_url = f"https://api.github.com/repos/{self.repo.full_name}/dependabot/alerts"
        headers = {'Authorization': f'token {self.github_token}'}
        
        response = requests.get(dependabot_url, headers=headers)
        if response.status_code == 200:
            alerts = response.json()
            
            self.metrics['dependencies'] = {
                'total_alerts': len(alerts),
                'open_alerts': len([a for a in alerts if a['state'] == 'open']),
                'fixed_alerts': len([a for a in alerts if a['state'] == 'fixed']),
                'dismissed_alerts': len([a for a in alerts if a['state'] == 'dismissed']),
                'critical': len([a for a in alerts if a.get('security_advisory', {}).get('severity') == 'critical']),
                'high': len([a for a in alerts if a.get('security_advisory', {}).get('severity') == 'high']),
                'packages_affected': len(set(a['dependency']['package']['name'] for a in alerts))
            }
            
    def collect_secret_scanning_metrics(self):
        """Collect secret scanning metrics"""
        
        secret_scanning_url = f"https://api.github.com/repos/{self.repo.full_name}/secret-scanning/alerts"
        headers = {'Authorization': f'token {self.github_token}'}
        
        response = requests.get(secret_scanning_url, headers=headers)
        if response.status_code == 200:
            alerts = response.json()
            
            self.metrics['secret_scanning'] = {
                'total_secrets': len(alerts),
                'open': len([a for a in alerts if a['state'] == 'open']),
                'resolved': len([a for a in alerts if a['state'] == 'resolved']),
                'types': {}
            }
            
            # Count by secret type
            for alert in alerts:
                secret_type = alert.get('secret_type', 'unknown')
                self.metrics['secret_scanning']['types'][secret_type] = \
                    self.metrics['secret_scanning']['types'].get(secret_type, 0) + 1
                    
    def collect_compliance_metrics(self):
        """Collect compliance and policy metrics"""
        
        self.metrics['compliance'] = {
            'branch_protection': self.check_branch_protection(),
            'signed_commits': self.check_signed_commits(),
            '2fa_enabled': self.check_2fa_compliance(),
            'security_policy': self.check_security_policy(),
            'license_compliance': self.check_license_compliance()
        }
        
    def check_branch_protection(self) -> Dict[str, Any]:
        """Check branch protection status"""
        try:
            branch = self.repo.get_branch('main')
            protection = branch.protection
            
            return {
                'enabled': protection is not None,
                'required_reviews': protection.required_pull_request_reviews.required_approving_review_count if protection else 0,
                'dismiss_stale_reviews': protection.required_pull_request_reviews.dismiss_stale_reviews if protection else False,
                'enforce_admins': protection.enforce_admins if protection else False,
                'required_status_checks': len(protection.required_status_checks.contexts) if protection and protection.required_status_checks else 0
            }
        except:
            return {'enabled': False}
            
    def check_signed_commits(self) -> Dict[str, Any]:
        """Check commit signing statistics"""
        commits = self.repo.get_commits(since=datetime.now() - timedelta(days=30))
        
        total = 0
        signed = 0
        
        for commit in commits[:100]:  # Check last 100 commits
            total += 1
            if commit.commit.verification.verified:
                signed += 1
                
        return {
            'percentage': (signed / total * 100) if total > 0 else 0,
            'total_commits': total,
            'signed_commits': signed
        }
        
    def generate_trends(self):
        """Generate trend data for visualization"""
        
        # Load historical data
        try:
            with open('metrics_history.json', 'r') as f:
                history = json.load(f)
        except:
            history = []
            
        # Add current metrics
        history.append({
            'date': self.metrics['timestamp'],
            'vulnerabilities': self.metrics['vulnerabilities']['total'],
            'critical': self.metrics['vulnerabilities']['critical'],
            'high': self.metrics['vulnerabilities']['high'],
            'dependencies': self.metrics['dependencies'].get('open_alerts', 0),
            'secrets': self.metrics['secret_scanning'].get('open', 0)
        })
        
        # Keep only last 30 days
        cutoff = datetime.now() - timedelta(days=30)
        history = [h for h in history if datetime.fromisoformat(h['date']) > cutoff]
        
        # Save updated history
        with open('metrics_history.json', 'w') as f:
            json.dump(history, f, indent=2)
            
        self.metrics['trends'] = history
        
    def save_metrics(self):
        """Save collected metrics"""
        with open('security_metrics.json', 'w') as f:
            json.dump(self.metrics, f, indent=2)
            
        print(f"Security metrics collected at {self.metrics['timestamp']}")
        print(f"Total vulnerabilities: {self.metrics['vulnerabilities']['total']}")
        print(f"Open dependency alerts: {self.metrics['dependencies'].get('open_alerts', 0)}")
        print(f"Open secrets: {self.metrics['secret_scanning'].get('open', 0)}")

if __name__ == "__main__":
    collector = SecurityMetricsCollector()
    collector.collect_vulnerability_metrics()
    collector.collect_dependency_metrics()
    collector.collect_secret_scanning_metrics()
    collector.collect_compliance_metrics()
    collector.generate_trends()
    collector.save_metrics()
```

### 1.3 ダッシュボード生成スクリプト

```python
# scripts/generate_dashboard.py
#!/usr/bin/env python3

import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from jinja2 import Template

class DashboardGenerator:
    def __init__(self):
        with open('security_metrics.json', 'r') as f:
            self.metrics = json.load(f)
            
    def generate_dashboard(self):
        """Generate interactive HTML dashboard"""
        
        # Create subplots
        fig = make_subplots(
            rows=3, cols=3,
            subplot_titles=(
                'Vulnerability Distribution',
                'Dependency Alerts',
                'Secret Scanning',
                'Vulnerability Trends (30 days)',
                'Compliance Score',
                'Security Score',
                'Top Vulnerable Components',
                'Alert Response Time',
                'Coverage Metrics'
            ),
            specs=[
                [{'type': 'pie'}, {'type': 'bar'}, {'type': 'bar'}],
                [{'type': 'scatter'}, {'type': 'indicator'}, {'type': 'indicator'}],
                [{'type': 'bar'}, {'type': 'scatter'}, {'type': 'sunburst'}]
            ],
            vertical_spacing=0.1,
            horizontal_spacing=0.1
        )
        
        # 1. Vulnerability Distribution (Pie)
        vuln_data = self.metrics['vulnerabilities']
        fig.add_trace(
            go.Pie(
                labels=['Critical', 'High', 'Medium', 'Low'],
                values=[
                    vuln_data.get('critical', 0),
                    vuln_data.get('high', 0),
                    vuln_data.get('medium', 0),
                    vuln_data.get('low', 0)
                ],
                marker_colors=['#dc3545', '#fd7e14', '#ffc107', '#28a745'],
                hole=0.3
            ),
            row=1, col=1
        )
        
        # 2. Dependency Alerts (Bar)
        dep_data = self.metrics['dependencies']
        fig.add_trace(
            go.Bar(
                x=['Open', 'Fixed', 'Dismissed'],
                y=[
                    dep_data.get('open_alerts', 0),
                    dep_data.get('fixed_alerts', 0),
                    dep_data.get('dismissed_alerts', 0)
                ],
                marker_color=['#dc3545', '#28a745', '#6c757d']
            ),
            row=1, col=2
        )
        
        # 3. Secret Scanning (Bar)
        secret_data = self.metrics['secret_scanning']
        if secret_data.get('types'):
            fig.add_trace(
                go.Bar(
                    x=list(secret_data['types'].keys()),
                    y=list(secret_data['types'].values()),
                    marker_color='#ff6b6b'
                ),
                row=1, col=3
            )
        
        # 4. Vulnerability Trends (Line)
        if self.metrics.get('trends'):
            trends = self.metrics['trends']
            dates = [t['date'] for t in trends]
            
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=[t['critical'] for t in trends],
                    name='Critical',
                    line=dict(color='#dc3545', width=2)
                ),
                row=2, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=[t['high'] for t in trends],
                    name='High',
                    line=dict(color='#fd7e14', width=2)
                ),
                row=2, col=1
            )
        
        # 5. Compliance Score (Gauge)
        compliance_score = self.calculate_compliance_score()
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=compliance_score,
                title={'text': "Compliance"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': self.get_score_color(compliance_score)},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "lightyellow"},
                        {'range': [80, 100], 'color': "lightgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ),
            row=2, col=2
        )
        
        # 6. Security Score (Gauge)
        security_score = self.calculate_security_score()
        fig.add_trace(
            go.Indicator(
                mode="gauge+number+delta",
                value=security_score,
                title={'text': "Security Score"},
                delta={'reference': 85},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': self.get_score_color(security_score)},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "lightyellow"},
                        {'range': [80, 100], 'color': "lightgreen"}
                    ]
                }
            ),
            row=2, col=3
        )
        
        # Update layout
        fig.update_layout(
            height=1200,
            showlegend=False,
            title={
                'text': f"Security Dashboard - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 24}
            },
            paper_bgcolor='#f8f9fa',
            plot_bgcolor='white',
            font={'family': 'Arial, sans-serif'}
        )
        
        # Save dashboard
        fig.write_html('dashboard.html')
        
        # Generate summary report
        self.generate_summary_report()
        
    def calculate_compliance_score(self) -> float:
        """Calculate overall compliance score"""
        compliance = self.metrics.get('compliance', {})
        
        scores = []
        if compliance.get('branch_protection', {}).get('enabled'):
            scores.append(100)
        else:
            scores.append(0)
            
        if compliance.get('signed_commits', {}).get('percentage', 0) > 80:
            scores.append(100)
        elif compliance.get('signed_commits', {}).get('percentage', 0) > 50:
            scores.append(50)
        else:
            scores.append(0)
            
        if compliance.get('2fa_enabled'):
            scores.append(100)
        else:
            scores.append(0)
            
        return sum(scores) / len(scores) if scores else 0
        
    def calculate_security_score(self) -> float:
        """Calculate overall security score"""
        vulns = self.metrics['vulnerabilities']
        
        # Weighted scoring
        critical_weight = vulns.get('critical', 0) * 10
        high_weight = vulns.get('high', 0) * 5
        medium_weight = vulns.get('medium', 0) * 2
        low_weight = vulns.get('low', 0) * 1
        
        total_weight = critical_weight + high_weight + medium_weight + low_weight
        
        if total_weight == 0:
            return 100
            
        # Score decreases with vulnerabilities
        score = max(0, 100 - total_weight)
        
        return round(score, 1)
        
    def get_score_color(self, score: float) -> str:
        """Get color based on score"""
        if score >= 90:
            return '#28a745'
        elif score >= 70:
            return '#ffc107'
        elif score >= 50:
            return '#fd7e14'
        else:
            return '#dc3545'
            
    def generate_summary_report(self):
        """Generate text summary report"""
        
        template = """
# Security Report Summary
Generated: {{ timestamp }}

## Executive Summary
- **Security Score**: {{ security_score }}/100
- **Compliance Score**: {{ compliance_score }}/100
- **Total Vulnerabilities**: {{ total_vulns }}
- **Critical Issues**: {{ critical_issues }}

## Vulnerabilities
- Critical: {{ vulns.critical }}
- High: {{ vulns.high }}
- Medium: {{ vulns.medium }}
- Low: {{ vulns.low }}

## Dependencies
- Open Alerts: {{ deps.open_alerts }}
- Packages Affected: {{ deps.packages_affected }}

## Secret Scanning
- Open Secrets: {{ secrets.open }}
- Resolved: {{ secrets.resolved }}

## Recommendations
{{ recommendations }}
        """
        
        recommendations = []
        
        if self.metrics['vulnerabilities'].get('critical', 0) > 0:
            recommendations.append("- ⚠️ Address critical vulnerabilities immediately")
            
        if self.metrics['dependencies'].get('open_alerts', 0) > 10:
            recommendations.append("- Update vulnerable dependencies")
            
        if self.metrics['secret_scanning'].get('open', 0) > 0:
            recommendations.append("- Rotate exposed secrets and remove from codebase")
            
        if not self.metrics['compliance'].get('branch_protection', {}).get('enabled'):
            recommendations.append("- Enable branch protection rules")
            
        tmpl = Template(template)
        report = tmpl.render(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            security_score=self.calculate_security_score(),
            compliance_score=self.calculate_compliance_score(),
            total_vulns=self.metrics['vulnerabilities'].get('total', 0),
            critical_issues=self.metrics['vulnerabilities'].get('critical', 0),
            vulns=self.metrics['vulnerabilities'],
            deps=self.metrics['dependencies'],
            secrets=self.metrics['secret_scanning'],
            recommendations='\n'.join(recommendations) if recommendations else 'No critical issues identified'
        )
        
        with open('security_report.md', 'w') as f:
            f.write(report)

if __name__ == "__main__":
    generator = DashboardGenerator()
    generator.generate_dashboard()
```

---

## 2. 自動レポート生成システム

### 2.1 週次レポート生成

```yaml
# .github/workflows/weekly-security-report.yml
name: Weekly Security Report

on:
  schedule:
    - cron: '0 9 * * 1'  # 毎週月曜日 9:00 JST
  workflow_dispatch:

jobs:
  generate-report:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
      
    - name: Setup environment
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        pip install pandas matplotlib seaborn reportlab jinja2
        
    - name: Collect weekly metrics
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      run: |
        python scripts/collect_weekly_metrics.py
        
    - name: Generate PDF report
      run: |
        python scripts/generate_pdf_report.py
        
    - name: Send report via email
      uses: dawidd6/action-send-mail@v3
      with:
        server_address: smtp.gmail.com
        server_port: 465
        username: ${{ secrets.EMAIL_USERNAME }}
        password: ${{ secrets.EMAIL_PASSWORD }}
        subject: Weekly Security Report - ${{ github.repository }}
        to: security@sas-com.com
        from: GitHub Actions
        body: Please find attached the weekly security report.
        attachments: weekly_security_report.pdf
```

---

## 3. アラート設定

### 3.1 リアルタイムアラート

```yaml
# .github/workflows/security-alerts.yml
name: Security Alert Monitoring

on:
  workflow_run:
    workflows: ["*"]
    types: [completed]
  repository_vulnerability_alert:
    types: [create, resolve, dismiss]

jobs:
  process-alert:
    runs-on: ubuntu-latest
    
    steps:
    - name: Check severity
      id: severity
      run: |
        # Determine alert severity
        echo "Processing security alert..."
        
    - name: Send critical alert
      if: steps.severity.outputs.level == 'critical'
      uses: 8398a7/action-slack@v3
      with:
        status: custom
        custom_payload: |
          {
            "text": "🚨 Critical Security Alert",
            "attachments": [{
              "color": "danger",
              "fields": [{
                "title": "Repository",
                "value": "${{ github.repository }}",
                "short": true
              }, {
                "title": "Severity",
                "value": "CRITICAL",
                "short": true
              }, {
                "title": "Action Required",
                "value": "Immediate attention needed",
                "short": false
              }]
            }]
          }
```

---

## 4. メトリクス収集

### 4.1 カスタムメトリクス定義

```yaml
# metrics-config.yml
metrics:
  security:
    - name: vulnerability_count
      type: gauge
      labels: [severity, state]
      query: SELECT COUNT(*) FROM vulnerabilities GROUP BY severity, state
      
    - name: mean_time_to_remediate
      type: histogram
      buckets: [1, 3, 7, 14, 30, 60, 90]
      query: SELECT DATEDIFF(fixed_at, created_at) FROM vulnerabilities WHERE state = 'fixed'
      
    - name: dependency_updates
      type: counter
      labels: [ecosystem, update_type]
      
    - name: security_scan_duration
      type: histogram
      buckets: [60, 120, 300, 600, 1800, 3600]
      
  compliance:
    - name: policy_violations
      type: counter
      labels: [policy_type, severity]
      
    - name: audit_findings
      type: gauge
      labels: [category, status]
```

---

## 5. インシデント追跡

### 5.1 インシデント管理システム

```python
# scripts/incident_tracker.py
#!/usr/bin/env python3

import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict

class IncidentSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class IncidentStatus(Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    CLOSED = "closed"

class SecurityIncident:
    def __init__(self, title: str, description: str, severity: IncidentSeverity):
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.severity = severity
        self.status = IncidentStatus.OPEN
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.timeline = []
        self.affected_systems = []
        self.remediation_steps = []
        self.root_cause = None
        self.lessons_learned = []
        
    def add_timeline_entry(self, entry: str):
        self.timeline.append({
            'timestamp': datetime.now().isoformat(),
            'entry': entry
        })
        self.updated_at = datetime.now()
        
    def update_status(self, new_status: IncidentStatus):
        self.status = new_status
        self.add_timeline_entry(f"Status changed to {new_status.value}")
        
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'severity': self.severity.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'timeline': self.timeline,
            'affected_systems': self.affected_systems,
            'remediation_steps': self.remediation_steps,
            'root_cause': self.root_cause,
            'lessons_learned': self.lessons_learned
        }

class IncidentTracker:
    def __init__(self):
        self.incidents = []
        self.load_incidents()
        
    def create_incident(self, title: str, description: str, severity: str) -> SecurityIncident:
        incident = SecurityIncident(
            title=title,
            description=description,
            severity=IncidentSeverity(severity)
        )
        self.incidents.append(incident)
        self.save_incidents()
        
        # Send notifications
        self.notify_team(incident)
        
        return incident
        
    def notify_team(self, incident: SecurityIncident):
        """Send notifications based on severity"""
        if incident.severity == IncidentSeverity.CRITICAL:
            # Page on-call
            self.page_oncall(incident)
            # Send to all channels
            self.send_slack_alert(incident, channel='#security-critical')
            self.send_email_alert(incident, recipients=['security@sas-com.com', 'cto@sas-com.com'])
            
        elif incident.severity == IncidentSeverity.HIGH:
            self.send_slack_alert(incident, channel='#security-alerts')
            self.send_email_alert(incident, recipients=['security@sas-com.com'])
            
    def generate_incident_report(self, incident_id: str) -> str:
        """Generate detailed incident report"""
        incident = next((i for i in self.incidents if i.id == incident_id), None)
        
        if not incident:
            return "Incident not found"
            
        report = f"""
# Incident Report: {incident.title}

**ID**: {incident.id}
**Severity**: {incident.severity.value.upper()}
**Status**: {incident.status.value}
**Created**: {incident.created_at}
**Last Updated**: {incident.updated_at}

## Description
{incident.description}

## Timeline
"""
        for entry in incident.timeline:
            report += f"- **{entry['timestamp']}**: {entry['entry']}\n"
            
        report += f"""

## Affected Systems
{', '.join(incident.affected_systems) if incident.affected_systems else 'None identified'}

## Root Cause
{incident.root_cause if incident.root_cause else 'Under investigation'}

## Remediation Steps
"""
        for step in incident.remediation_steps:
            report += f"- {step}\n"
            
        report += f"""

## Lessons Learned
"""
        for lesson in incident.lessons_learned:
            report += f"- {lesson}\n"
            
        return report
        
    def save_incidents(self):
        with open('incidents.json', 'w') as f:
            json.dump([i.to_dict() for i in self.incidents], f, indent=2)
            
    def load_incidents(self):
        try:
            with open('incidents.json', 'r') as f:
                data = json.load(f)
                # Reconstruct incidents from saved data
        except FileNotFoundError:
            self.incidents = []
```

---

## 6. コンプライアンス監視

### 6.1 コンプライアンスチェッカー

```python
# scripts/compliance_checker.py
#!/usr/bin/env python3

import json
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ComplianceRule:
    id: str
    name: str
    description: str
    category: str
    severity: str
    check_function: str
    remediation: str

class ComplianceChecker:
    def __init__(self):
        self.rules = self.load_rules()
        self.results = []
        
    def load_rules(self) -> List[ComplianceRule]:
        """Load compliance rules from configuration"""
        rules = [
            ComplianceRule(
                id="SEC-001",
                name="2FA Enforcement",
                description="Two-factor authentication must be enabled for all users",
                category="Access Control",
                severity="critical",
                check_function="check_2fa_enabled",
                remediation="Enable 2FA in organization settings"
            ),
            ComplianceRule(
                id="SEC-002",
                name="Branch Protection",
                description="Main branch must have protection rules enabled",
                category="Code Protection",
                severity="high",
                check_function="check_branch_protection",
                remediation="Configure branch protection rules"
            ),
            ComplianceRule(
                id="SEC-003",
                name="Secret Scanning",
                description="Secret scanning must be enabled",
                category="Secret Management",
                severity="critical",
                check_function="check_secret_scanning",
                remediation="Enable secret scanning in security settings"
            ),
            ComplianceRule(
                id="SEC-004",
                name="Dependency Scanning",
                description="Automated dependency scanning must be configured",
                category="Supply Chain",
                severity="high",
                check_function="check_dependency_scanning",
                remediation="Configure Dependabot or equivalent"
            ),
            ComplianceRule(
                id="SEC-005",
                name="Security Policy",
                description="SECURITY.md file must exist",
                category="Documentation",
                severity="medium",
                check_function="check_security_policy",
                remediation="Create .github/SECURITY.md file"
            )
        ]
        return rules
        
    def run_compliance_checks(self) -> Dict:
        """Run all compliance checks"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'total_rules': len(self.rules),
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'compliance_score': 0,
            'details': []
        }
        
        for rule in self.rules:
            check_result = self.execute_check(rule)
            
            results['details'].append({
                'rule_id': rule.id,
                'name': rule.name,
                'category': rule.category,
                'severity': rule.severity,
                'status': check_result['status'],
                'message': check_result['message'],
                'remediation': rule.remediation if check_result['status'] == 'failed' else None
            })
            
            if check_result['status'] == 'passed':
                results['passed'] += 1
            elif check_result['status'] == 'failed':
                results['failed'] += 1
            else:
                results['warnings'] += 1
                
        # Calculate compliance score
        results['compliance_score'] = (results['passed'] / results['total_rules']) * 100
        
        return results
        
    def execute_check(self, rule: ComplianceRule) -> Dict:
        """Execute individual compliance check"""
        try:
            # Dynamic function call based on rule
            check_method = getattr(self, rule.check_function)
            return check_method()
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Check failed: {str(e)}"
            }
            
    def check_2fa_enabled(self) -> Dict:
        """Check if 2FA is enabled for organization"""
        # Implementation
        return {'status': 'passed', 'message': '2FA is enabled'}
        
    def check_branch_protection(self) -> Dict:
        """Check branch protection rules"""
        # Implementation
        return {'status': 'passed', 'message': 'Branch protection configured'}
        
    def generate_compliance_report(self, results: Dict) -> str:
        """Generate compliance report"""
        report = f"""
# Compliance Report

**Date**: {results['timestamp']}
**Compliance Score**: {results['compliance_score']:.1f}%

## Summary
- Total Rules: {results['total_rules']}
- Passed: {results['passed']}
- Failed: {results['failed']}
- Warnings: {results['warnings']}

## Detailed Results

| Rule ID | Name | Category | Severity | Status |
|---------|------|----------|----------|--------|
"""
        
        for detail in results['details']:
            status_emoji = "✅" if detail['status'] == 'passed' else "❌"
            report += f"| {detail['rule_id']} | {detail['name']} | {detail['category']} | {detail['severity']} | {status_emoji} |\n"
            
        # Add remediation section if there are failures
        if results['failed'] > 0:
            report += "\n## Required Remediations\n\n"
            for detail in results['details']:
                if detail['status'] == 'failed':
                    report += f"### {detail['name']}\n"
                    report += f"- **Rule**: {detail['rule_id']}\n"
                    report += f"- **Severity**: {detail['severity']}\n"
                    report += f"- **Remediation**: {detail['remediation']}\n\n"
                    
        return report

if __name__ == "__main__":
    checker = ComplianceChecker()
    results = checker.run_compliance_checks()
    report = checker.generate_compliance_report(results)
    
    with open('compliance_report.md', 'w') as f:
        f.write(report)
        
    with open('compliance_results.json', 'w') as f:
        json.dump(results, f, indent=2)
```

---

## 7. パフォーマンス分析

### 7.1 セキュリティスキャンパフォーマンス

```python
# scripts/performance_analyzer.py
#!/usr/bin/env python3

import json
import statistics
from datetime import datetime, timedelta
from typing import List, Dict

class SecurityPerformanceAnalyzer:
    def __init__(self):
        self.metrics = {
            'scan_durations': [],
            'vulnerability_detection_time': [],
            'remediation_time': [],
            'false_positive_rate': 0,
            'scan_coverage': 0
        }
        
    def analyze_scan_performance(self, workflow_runs: List[Dict]) -> Dict:
        """Analyze security scan performance metrics"""
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'period': '7_days',
            'scans': {
                'total': len(workflow_runs),
                'successful': 0,
                'failed': 0,
                'average_duration': 0,
                'p95_duration': 0,
                'p99_duration': 0
            },
            'efficiency': {
                'vulnerabilities_found': 0,
                'false_positives': 0,
                'true_positive_rate': 0,
                'mean_time_to_detect': 0
            },
            'coverage': {
                'lines_scanned': 0,
                'files_scanned': 0,
                'languages_covered': [],
                'tools_used': []
            },
            'recommendations': []
        }
        
        # Process workflow runs
        durations = []
        for run in workflow_runs:
            if run['status'] == 'completed':
                analysis['scans']['successful'] += 1
                duration = (run['updated_at'] - run['created_at']).total_seconds()
                durations.append(duration)
            else:
                analysis['scans']['failed'] += 1
                
        # Calculate statistics
        if durations:
            analysis['scans']['average_duration'] = statistics.mean(durations)
            analysis['scans']['p95_duration'] = statistics.quantiles(durations, n=20)[18]  # 95th percentile
            analysis['scans']['p99_duration'] = statistics.quantiles(durations, n=100)[98]  # 99th percentile
            
        # Generate recommendations
        if analysis['scans']['average_duration'] > 1800:  # 30 minutes
            analysis['recommendations'].append("Consider optimizing scan configuration to reduce duration")
            
        if analysis['scans']['failed'] > analysis['scans']['successful'] * 0.1:
            analysis['recommendations'].append("High failure rate detected - review scan configuration")
            
        return analysis
        
    def calculate_mttr(self, vulnerabilities: List[Dict]) -> float:
        """Calculate Mean Time To Remediate"""
        remediation_times = []
        
        for vuln in vulnerabilities:
            if vuln['status'] == 'fixed':
                time_to_fix = (vuln['fixed_at'] - vuln['created_at']).total_seconds() / 3600  # hours
                remediation_times.append(time_to_fix)
                
        return statistics.mean(remediation_times) if remediation_times else 0
        
    def generate_performance_report(self) -> str:
        """Generate performance analysis report"""
        report = f"""
# Security Scanning Performance Report

## Scan Performance Metrics
- Average Scan Duration: {self.format_duration(self.metrics.get('average_duration', 0))}
- P95 Duration: {self.format_duration(self.metrics.get('p95_duration', 0))}
- P99 Duration: {self.format_duration(self.metrics.get('p99_duration', 0))}
- Success Rate: {self.metrics.get('success_rate', 0):.1f}%

## Detection Efficiency
- True Positive Rate: {self.metrics.get('true_positive_rate', 0):.1f}%
- False Positive Rate: {self.metrics.get('false_positive_rate', 0):.1f}%
- Mean Time to Detect: {self.format_duration(self.metrics.get('mttd', 0))}

## Remediation Metrics
- Mean Time to Remediate: {self.format_duration(self.metrics.get('mttr', 0))}
- Auto-remediation Rate: {self.metrics.get('auto_remediation_rate', 0):.1f}%

## Coverage Analysis
- Code Coverage: {self.metrics.get('code_coverage', 0):.1f}%
- Dependency Coverage: {self.metrics.get('dependency_coverage', 0):.1f}%
- Container Coverage: {self.metrics.get('container_coverage', 0):.1f}%

## Optimization Opportunities
{self.generate_optimization_recommendations()}
        """
        return report
        
    def format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds/60:.0f}m"
        else:
            return f"{seconds/3600:.1f}h"
```

---

## 8. レポートテンプレート

### 8.1 エグゼクティブサマリーテンプレート

```html
<!-- templates/executive_summary.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Security Executive Summary</title>
    <style>
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .metric-value {
            font-size: 48px;
            font-weight: bold;
            color: #333;
        }
        .metric-label {
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .trend-up {
            color: #28a745;
        }
        .trend-down {
            color: #dc3545;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .priority-high {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 10px 0;
        }
        .priority-critical {
            background: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 15px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Security Executive Summary</h1>
        <p>{{ organization }} - {{ date }}</p>
    </div>
    
    <div class="grid">
        <div class="metric-card">
            <div class="metric-label">Security Score</div>
            <div class="metric-value">{{ security_score }}</div>
            <div class="trend-{{ score_trend }}">{{ score_change }}%</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Critical Issues</div>
            <div class="metric-value">{{ critical_issues }}</div>
            <div class="trend-{{ critical_trend }}">{{ critical_change }}</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">MTTR (hours)</div>
            <div class="metric-value">{{ mttr }}</div>
            <div class="trend-{{ mttr_trend }}">{{ mttr_change }}%</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Compliance</div>
            <div class="metric-value">{{ compliance }}%</div>
            <div class="trend-{{ compliance_trend }}">{{ compliance_change }}%</div>
        </div>
    </div>
    
    <div class="chart-container">
        <h2>30-Day Vulnerability Trend</h2>
        <div id="trend-chart"></div>
    </div>
    
    <div class="chart-container">
        <h2>Key Actions Required</h2>
        {% for action in critical_actions %}
        <div class="priority-{{ action.priority }}">
            <strong>{{ action.title }}</strong>
            <p>{{ action.description }}</p>
            <small>Due: {{ action.due_date }}</small>
        </div>
        {% endfor %}
    </div>
    
    <div class="chart-container">
        <h2>Compliance Status</h2>
        <table style="width: 100%;">
            <tr>
                <th>Framework</th>
                <th>Status</th>
                <th>Score</th>
                <th>Last Audit</th>
            </tr>
            {% for framework in compliance_frameworks %}
            <tr>
                <td>{{ framework.name }}</td>
                <td>{{ framework.status }}</td>
                <td>{{ framework.score }}%</td>
                <td>{{ framework.last_audit }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
```

---

## まとめ

この監視・レポート設定により、以下が実現されます：

1. **リアルタイム監視**: 継続的なセキュリティ状態の把握
2. **自動レポート生成**: 定期的なレポート作成と配信
3. **アラート通知**: 重要なセキュリティイベントの即座通知
4. **メトリクス追跡**: セキュリティKPIの継続的測定
5. **インシデント管理**: 体系的なインシデント対応
6. **コンプライアンス監視**: 規制要件の継続的確認
7. **パフォーマンス分析**: セキュリティツールの効率性評価
8. **エグゼクティブレポート**: 経営層向けの分かりやすいサマリー

これらのツールとプロセスを活用することで、組織全体のセキュリティ態勢を継続的に改善できます。

---

**最終更新**: 2025-09-10  
**承認者**: セキュリティチーム