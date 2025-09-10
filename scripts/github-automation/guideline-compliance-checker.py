#!/usr/bin/env python3
"""
GitHub ガイドライン準拠チェックツール
エス・エー・エス株式会社

用途: GitHub組織・リポジトリのガイドライン準拠状況をチェック
"""

import json
import logging
import os
import sys
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import requests
from dataclasses import dataclass, asdict
from pathlib import Path
import yaml
import re

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ComplianceResult:
    """準拠チェック結果"""
    check_name: str
    status: str  # PASS, FAIL, WARN, SKIP
    message: str
    severity: str  # HIGH, MEDIUM, LOW
    details: Optional[Dict] = None

@dataclass
class RepositoryCompliance:
    """リポジトリ準拠状況"""
    repository: str
    overall_score: float
    checks: List[ComplianceResult]
    recommendations: List[str]
    timestamp: datetime

class GitHubComplianceChecker:
    """GitHub ガイドライン準拠チェッカー"""
    
    def __init__(self, token: str, org: str, config_path: str = './config/compliance-rules.yml'):
        self.token = token
        self.org = org
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = 'https://api.github.com'
        
        # 準拠ルール読み込み
        self.rules = self._load_compliance_rules(config_path)
        
    def _load_compliance_rules(self, config_path: str) -> Dict:
        """準拠ルール設定読み込み"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"設定ファイルが見つかりません: {config_path}")
            return self._get_default_rules()
    
    def _get_default_rules(self) -> Dict:
        """デフォルト準拠ルール"""
        return {
            'organization': {
                'required_settings': {
                    'members_can_create_repositories': False,
                    'members_can_delete_repositories': False,
                    'web_commit_signoff_required': True,
                    'advanced_security_enabled_for_new_repositories': True
                },
                'required_teams': ['developers', 'devops', 'security'],
                'security_features': {
                    'dependabot_alerts': True,
                    'dependabot_security_updates': True,
                    'dependency_review': True,
                    'secret_scanning': True
                }
            },
            'repository': {
                'branch_protection': {
                    'required_status_checks': True,
                    'enforce_admins': True,
                    'required_pull_request_reviews': {
                        'required_approving_review_count': 2,
                        'dismiss_stale_reviews': True,
                        'require_code_owner_reviews': True
                    },
                    'required_conversation_resolution': True,
                    'allow_force_pushes': False,
                    'allow_deletions': False
                },
                'security_features': {
                    'vulnerability_alerts': True,
                    'automated_security_fixes': True,
                    'secret_scanning': True,
                    'code_scanning': True
                },
                'required_files': [
                    'README.md',
                    '.gitignore',
                    'CODEOWNERS',
                    '.github/pull_request_template.md'
                ],
                'naming_convention': {
                    'pattern': '^[a-z0-9][a-z0-9-]*[a-z0-9]$',
                    'max_length': 50
                },
                'commit_convention': {
                    'pattern': '^(feat|fix|docs|style|refactor|test|chore)(\\(.+\\))?: .+',
                    'enforce': True
                }
            },
            'pull_request': {
                'required_checks': ['ci/build', 'ci/test', 'security/scan'],
                'minimum_reviews': 2,
                'require_up_to_date': True,
                'require_conversation_resolution': True
            }
        }
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """GitHub API リクエスト"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
    
    def check_organization_compliance(self) -> List[ComplianceResult]:
        """組織レベル準拠チェック"""
        results = []
        logger.info("組織レベルの準拠チェック開始...")
        
        try:
            # 組織設定チェック
            org_data = self._make_request(f"orgs/{self.org}")
            results.extend(self._check_org_settings(org_data))
            
            # チーム存在チェック
            results.extend(self._check_required_teams())
            
            # セキュリティ機能チェック
            results.extend(self._check_org_security_features())
            
        except Exception as e:
            results.append(ComplianceResult(
                check_name="organization_access",
                status="FAIL",
                message=f"組織情報にアクセスできません: {e}",
                severity="HIGH"
            ))
        
        return results
    
    def _check_org_settings(self, org_data: Dict) -> List[ComplianceResult]:
        """組織設定チェック"""
        results = []
        required_settings = self.rules['organization']['required_settings']
        
        for setting, expected_value in required_settings.items():
            actual_value = org_data.get(setting)
            
            if actual_value == expected_value:
                results.append(ComplianceResult(
                    check_name=f"org_setting_{setting}",
                    status="PASS",
                    message=f"組織設定 '{setting}' が適切に設定されています",
                    severity="MEDIUM"
                ))
            else:
                results.append(ComplianceResult(
                    check_name=f"org_setting_{setting}",
                    status="FAIL",
                    message=f"組織設定 '{setting}' が不適切です (期待値: {expected_value}, 実際: {actual_value})",
                    severity="HIGH",
                    details={'expected': expected_value, 'actual': actual_value}
                ))
        
        return results
    
    def _check_required_teams(self) -> List[ComplianceResult]:
        """必須チームチェック"""
        results = []
        required_teams = self.rules['organization']['required_teams']
        
        try:
            teams_data = self._make_request(f"orgs/{self.org}/teams")
            existing_teams = [team['slug'] for team in teams_data]
            
            for team in required_teams:
                if team in existing_teams:
                    results.append(ComplianceResult(
                        check_name=f"team_exists_{team}",
                        status="PASS",
                        message=f"必須チーム '{team}' が存在します",
                        severity="MEDIUM"
                    ))
                else:
                    results.append(ComplianceResult(
                        check_name=f"team_exists_{team}",
                        status="FAIL",
                        message=f"必須チーム '{team}' が存在しません",
                        severity="HIGH"
                    ))
                    
        except Exception as e:
            results.append(ComplianceResult(
                check_name="teams_access",
                status="FAIL",
                message=f"チーム情報にアクセスできません: {e}",
                severity="MEDIUM"
            ))
        
        return results
    
    def _check_org_security_features(self) -> List[ComplianceResult]:
        """組織セキュリティ機能チェック"""
        results = []
        # GitHub APIの制限により、一部機能は推定またはスキップ
        
        results.append(ComplianceResult(
            check_name="org_security_features",
            status="SKIP",
            message="組織セキュリティ機能のチェックは手動で確認してください",
            severity="LOW"
        ))
        
        return results
    
    def check_repository_compliance(self, repo_name: str) -> RepositoryCompliance:
        """リポジトリ準拠チェック"""
        logger.info(f"リポジトリ '{repo_name}' の準拠チェック開始...")
        
        checks = []
        
        try:
            # 基本情報取得
            repo_data = self._make_request(f"repos/{self.org}/{repo_name}")
            
            # 各種チェック実行
            checks.extend(self._check_repository_settings(repo_data))
            checks.extend(self._check_branch_protection(repo_name))
            checks.extend(self._check_repository_security(repo_name))
            checks.extend(self._check_required_files(repo_name))
            checks.extend(self._check_naming_convention(repo_data))
            checks.extend(self._check_commit_convention(repo_name))
            
        except Exception as e:
            checks.append(ComplianceResult(
                check_name="repository_access",
                status="FAIL",
                message=f"リポジトリにアクセスできません: {e}",
                severity="HIGH"
            ))
        
        # 総合スコア計算
        score = self._calculate_compliance_score(checks)
        
        # 推奨事項生成
        recommendations = self._generate_recommendations(checks)
        
        return RepositoryCompliance(
            repository=repo_name,
            overall_score=score,
            checks=checks,
            recommendations=recommendations,
            timestamp=datetime.now()
        )
    
    def _check_repository_settings(self, repo_data: Dict) -> List[ComplianceResult]:
        """リポジトリ設定チェック"""
        results = []
        
        # プライベートリポジトリチェック
        if repo_data.get('private', False):
            results.append(ComplianceResult(
                check_name="repo_privacy",
                status="PASS",
                message="リポジトリが適切にプライベートに設定されています",
                severity="HIGH"
            ))
        else:
            results.append(ComplianceResult(
                check_name="repo_privacy",
                status="WARN",
                message="リポジトリがパブリックです。機密情報が含まれていないか確認してください",
                severity="MEDIUM"
            ))
        
        # Issues, Wiki, Projects設定
        settings_check = {
            'has_issues': ('Issues機能', 'MEDIUM'),
            'has_wiki': ('Wiki機能', 'LOW'),
            'has_projects': ('Projects機能', 'LOW')
        }
        
        for setting, (name, severity) in settings_check.items():
            if repo_data.get(setting, False):
                results.append(ComplianceResult(
                    check_name=f"repo_{setting}",
                    status="PASS",
                    message=f"{name}が有効です",
                    severity=severity
                ))
        
        return results
    
    def _check_branch_protection(self, repo_name: str) -> List[ComplianceResult]:
        """ブランチ保護チェック"""
        results = []
        
        try:
            # mainブランチの保護設定取得
            protection_data = self._make_request(
                f"repos/{self.org}/{repo_name}/branches/main/protection"
            )
            
            bp_rules = self.rules['repository']['branch_protection']
            
            # 必須ステータスチェック
            if protection_data.get('required_status_checks'):
                results.append(ComplianceResult(
                    check_name="branch_protection_status_checks",
                    status="PASS",
                    message="必須ステータスチェックが設定されています",
                    severity="HIGH"
                ))
            else:
                results.append(ComplianceResult(
                    check_name="branch_protection_status_checks",
                    status="FAIL",
                    message="必須ステータスチェックが設定されていません",
                    severity="HIGH"
                ))
            
            # PR必須レビュー
            pr_reviews = protection_data.get('required_pull_request_reviews', {})
            required_count = bp_rules['required_pull_request_reviews']['required_approving_review_count']
            
            if pr_reviews.get('required_approving_review_count', 0) >= required_count:
                results.append(ComplianceResult(
                    check_name="branch_protection_reviews",
                    status="PASS",
                    message=f"必要なレビュー数({required_count})が設定されています",
                    severity="HIGH"
                ))
            else:
                results.append(ComplianceResult(
                    check_name="branch_protection_reviews",
                    status="FAIL",
                    message=f"レビュー数が不足しています (必要: {required_count})",
                    severity="HIGH"
                ))
            
            # 管理者適用
            if protection_data.get('enforce_admins', {}).get('enabled', False):
                results.append(ComplianceResult(
                    check_name="branch_protection_enforce_admins",
                    status="PASS",
                    message="管理者にもブランチ保護が適用されています",
                    severity="MEDIUM"
                ))
            else:
                results.append(ComplianceResult(
                    check_name="branch_protection_enforce_admins",
                    status="WARN",
                    message="管理者にブランチ保護が適用されていません",
                    severity="MEDIUM"
                ))
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                results.append(ComplianceResult(
                    check_name="branch_protection",
                    status="FAIL",
                    message="mainブランチに保護設定がありません",
                    severity="HIGH"
                ))
            else:
                results.append(ComplianceResult(
                    check_name="branch_protection",
                    status="FAIL",
                    message=f"ブランチ保護設定の確認中にエラー: {e}",
                    severity="MEDIUM"
                ))
        
        return results
    
    def _check_repository_security(self, repo_name: str) -> List[ComplianceResult]:
        """リポジトリセキュリティチェック"""
        results = []
        
        # セキュリティアラート
        try:
            self._make_request(f"repos/{self.org}/{repo_name}/vulnerability-alerts")
            results.append(ComplianceResult(
                check_name="security_vulnerability_alerts",
                status="PASS",
                message="脆弱性アラートが有効です",
                severity="HIGH"
            ))
        except requests.exceptions.HTTPError:
            results.append(ComplianceResult(
                check_name="security_vulnerability_alerts",
                status="FAIL",
                message="脆弱性アラートが無効です",
                severity="HIGH"
            ))
        
        # 自動セキュリティ修正
        try:
            self._make_request(f"repos/{self.org}/{repo_name}/automated-security-fixes")
            results.append(ComplianceResult(
                check_name="security_automated_fixes",
                status="PASS",
                message="自動セキュリティ修正が有効です",
                severity="MEDIUM"
            ))
        except requests.exceptions.HTTPError:
            results.append(ComplianceResult(
                check_name="security_automated_fixes",
                status="WARN",
                message="自動セキュリティ修正が無効です",
                severity="MEDIUM"
            ))
        
        return results
    
    def _check_required_files(self, repo_name: str) -> List[ComplianceResult]:
        """必須ファイルチェック"""
        results = []
        required_files = self.rules['repository']['required_files']
        
        for file_path in required_files:
            try:
                self._make_request(f"repos/{self.org}/{repo_name}/contents/{file_path}")
                results.append(ComplianceResult(
                    check_name=f"required_file_{file_path.replace('/', '_')}",
                    status="PASS",
                    message=f"必須ファイル '{file_path}' が存在します",
                    severity="MEDIUM"
                ))
            except requests.exceptions.HTTPError:
                results.append(ComplianceResult(
                    check_name=f"required_file_{file_path.replace('/', '_')}",
                    status="FAIL",
                    message=f"必須ファイル '{file_path}' が存在しません",
                    severity="MEDIUM"
                ))
        
        return results
    
    def _check_naming_convention(self, repo_data: Dict) -> List[ComplianceResult]:
        """命名規約チェック"""
        results = []
        repo_name = repo_data.get('name', '')
        
        naming_rules = self.rules['repository']['naming_convention']
        pattern = naming_rules['pattern']
        max_length = naming_rules['max_length']
        
        # パターンチェック
        if re.match(pattern, repo_name):
            results.append(ComplianceResult(
                check_name="naming_pattern",
                status="PASS",
                message="リポジトリ名が命名規約に準拠しています",
                severity="LOW"
            ))
        else:
            results.append(ComplianceResult(
                check_name="naming_pattern",
                status="FAIL",
                message=f"リポジトリ名が命名規約に準拠していません (パターン: {pattern})",
                severity="MEDIUM",
                details={'pattern': pattern, 'name': repo_name}
            ))
        
        # 長さチェック
        if len(repo_name) <= max_length:
            results.append(ComplianceResult(
                check_name="naming_length",
                status="PASS",
                message="リポジトリ名の長さが適切です",
                severity="LOW"
            ))
        else:
            results.append(ComplianceResult(
                check_name="naming_length",
                status="FAIL",
                message=f"リポジトリ名が長すぎます (上限: {max_length}, 実際: {len(repo_name)})",
                severity="MEDIUM"
            ))
        
        return results
    
    def _check_commit_convention(self, repo_name: str) -> List[ComplianceResult]:
        """コミット規約チェック"""
        results = []
        
        try:
            # 最近のコミット取得（10件）
            commits_data = self._make_request(
                f"repos/{self.org}/{repo_name}/commits",
                params={'per_page': 10}
            )
            
            if not commits_data:
                results.append(ComplianceResult(
                    check_name="commit_convention",
                    status="SKIP",
                    message="コミット履歴が取得できませんでした",
                    severity="LOW"
                ))
                return results
            
            pattern = self.rules['repository']['commit_convention']['pattern']
            compliant_commits = 0
            
            for commit in commits_data:
                message = commit.get('commit', {}).get('message', '')
                first_line = message.split('\n')[0]
                
                if re.match(pattern, first_line):
                    compliant_commits += 1
            
            compliance_rate = compliant_commits / len(commits_data)
            
            if compliance_rate >= 0.8:  # 80%以上で合格
                results.append(ComplianceResult(
                    check_name="commit_convention",
                    status="PASS",
                    message=f"コミットメッセージの規約準拠率: {compliance_rate:.1%}",
                    severity="MEDIUM",
                    details={'compliant_rate': compliance_rate}
                ))
            elif compliance_rate >= 0.5:  # 50%以上で警告
                results.append(ComplianceResult(
                    check_name="commit_convention",
                    status="WARN",
                    message=f"コミットメッセージの規約準拠率が低いです: {compliance_rate:.1%}",
                    severity="MEDIUM",
                    details={'compliant_rate': compliance_rate}
                ))
            else:
                results.append(ComplianceResult(
                    check_name="commit_convention",
                    status="FAIL",
                    message=f"コミットメッセージの規約準拠率が非常に低いです: {compliance_rate:.1%}",
                    severity="HIGH",
                    details={'compliant_rate': compliance_rate}
                ))
                
        except Exception as e:
            results.append(ComplianceResult(
                check_name="commit_convention",
                status="FAIL",
                message=f"コミット規約チェック中にエラー: {e}",
                severity="LOW"
            ))
        
        return results
    
    def _calculate_compliance_score(self, checks: List[ComplianceResult]) -> float:
        """準拠スコア計算"""
        if not checks:
            return 0.0
        
        total_weight = 0
        weighted_score = 0
        
        weight_map = {
            'HIGH': 3,
            'MEDIUM': 2,
            'LOW': 1
        }
        
        status_score = {
            'PASS': 1.0,
            'WARN': 0.5,
            'FAIL': 0.0,
            'SKIP': None  # スコア計算から除外
        }
        
        for check in checks:
            if check.status == 'SKIP':
                continue
                
            weight = weight_map.get(check.severity, 1)
            score = status_score.get(check.status, 0.0)
            
            total_weight += weight
            weighted_score += weight * score
        
        return (weighted_score / total_weight * 100) if total_weight > 0 else 0.0
    
    def _generate_recommendations(self, checks: List[ComplianceResult]) -> List[str]:
        """推奨事項生成"""
        recommendations = []
        
        high_priority_fails = [c for c in checks if c.status == 'FAIL' and c.severity == 'HIGH']
        medium_priority_fails = [c for c in checks if c.status == 'FAIL' and c.severity == 'MEDIUM']
        warnings = [c for c in checks if c.status == 'WARN']
        
        if high_priority_fails:
            recommendations.append(f"重要な問題({len(high_priority_fails)}件)を優先的に修正してください")
            
        if medium_priority_fails:
            recommendations.append(f"中程度の問題({len(medium_priority_fails)}件)を計画的に修正してください")
            
        if warnings:
            recommendations.append(f"警告事項({len(warnings)}件)を確認し、必要に応じて対応してください")
        
        # 具体的な推奨事項
        failed_checks = [c.check_name for c in checks if c.status == 'FAIL']
        
        if 'branch_protection' in ' '.join(failed_checks):
            recommendations.append("ブランチ保護設定を適切に構成してください")
        
        if any('security' in check for check in failed_checks):
            recommendations.append("セキュリティ機能を有効化してください")
        
        if any('required_file' in check for check in failed_checks):
            recommendations.append("必須ファイル（README.md、CODEOWNERS等）を作成してください")
        
        return recommendations

def generate_html_report(results: Dict, output_path: str):
    """HTML形式のレポート生成"""
    html_template = """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GitHub ガイドライン準拠レポート</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; }
            .header { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
            .metric { background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #007bff; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .metric-value { font-size: 2em; font-weight: bold; color: #007bff; }
            .metric-label { color: #6c757d; font-size: 0.9em; }
            .repository { margin: 20px 0; padding: 20px; border: 1px solid #dee2e6; border-radius: 8px; }
            .score { font-size: 1.5em; font-weight: bold; }
            .score.high { color: #28a745; }
            .score.medium { color: #ffc107; }
            .score.low { color: #dc3545; }
            .check { margin: 10px 0; padding: 10px; border-radius: 4px; }
            .check.pass { background: #d4edda; border-left: 4px solid #28a745; }
            .check.warn { background: #fff3cd; border-left: 4px solid #ffc107; }
            .check.fail { background: #f8d7da; border-left: 4px solid #dc3545; }
            .check.skip { background: #e2e3e5; border-left: 4px solid #6c757d; }
            .recommendations { background: #e7f3ff; padding: 15px; border-radius: 8px; margin-top: 15px; }
            .recommendations ul { margin: 0; padding-left: 20px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>GitHub ガイドライン準拠レポート</h1>
            <p><strong>組織:</strong> {org}</p>
            <p><strong>生成日時:</strong> {timestamp}</p>
        </div>
        
        <div class="summary">
            <div class="metric">
                <div class="metric-value">{total_repos}</div>
                <div class="metric-label">総リポジトリ数</div>
            </div>
            <div class="metric">
                <div class="metric-value">{avg_score:.1f}%</div>
                <div class="metric-label">平均準拠スコア</div>
            </div>
            <div class="metric">
                <div class="metric-value">{high_score_repos}</div>
                <div class="metric-label">高スコアリポジトリ (80%+)</div>
            </div>
            <div class="metric">
                <div class="metric-value">{low_score_repos}</div>
                <div class="metric-label">要改善リポジトリ (60%未満)</div>
            </div>
        </div>
        
        {repo_sections}
    </body>
    </html>
    """
    
    # リポジトリセクション生成
    repo_sections = ""
    for repo_result in results['repositories']:
        score = repo_result['overall_score']
        score_class = 'high' if score >= 80 else 'medium' if score >= 60 else 'low'
        
        checks_html = ""
        for check in repo_result['checks']:
            checks_html += f"""
                <div class="check {check['status'].lower()}">
                    <strong>{check['check_name']}</strong> ({check['severity']})
                    <br>{check['message']}
                </div>
            """
        
        recommendations_html = ""
        if repo_result['recommendations']:
            recommendations_html = f"""
                <div class="recommendations">
                    <h4>推奨事項</h4>
                    <ul>
                        {''.join(f'<li>{rec}</li>' for rec in repo_result['recommendations'])}
                    </ul>
                </div>
            """
        
        repo_sections += f"""
            <div class="repository">
                <h3>{repo_result['repository']}</h3>
                <div class="score {score_class}">準拠スコア: {score:.1f}%</div>
                {checks_html}
                {recommendations_html}
            </div>
        """
    
    # 統計計算
    scores = [r['overall_score'] for r in results['repositories']]
    avg_score = sum(scores) / len(scores) if scores else 0
    high_score_repos = len([s for s in scores if s >= 80])
    low_score_repos = len([s for s in scores if s < 60])
    
    html_content = html_template.format(
        org=results['organization'],
        timestamp=results['timestamp'],
        total_repos=len(results['repositories']),
        avg_score=avg_score,
        high_score_repos=high_score_repos,
        low_score_repos=low_score_repos,
        repo_sections=repo_sections
    )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='GitHub ガイドライン準拠チェック')
    parser.add_argument('--org', required=True, help='GitHub組織名')
    parser.add_argument('--token', help='GitHub API トークン (環境変数 GITHUB_TOKEN を使用可能)')
    parser.add_argument('--repos', nargs='*', help='特定のリポジトリのみチェック')
    parser.add_argument('--config', default='./config/compliance-rules.yml', 
                       help='準拠ルール設定ファイル')
    parser.add_argument('--output', default='./reports', help='出力ディレクトリ')
    parser.add_argument('--format', choices=['json', 'html', 'both'], 
                       default='both', help='出力形式')
    
    args = parser.parse_args()
    
    # GitHub token 取得
    token = args.token or os.getenv('GITHUB_TOKEN')
    if not token:
        logger.error("GitHub API token が必要です。")
        sys.exit(1)
    
    # 出力ディレクトリ作成
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # コンプライアンスチェッカー初期化
    checker = GitHubComplianceChecker(token, args.org, args.config)
    
    try:
        # 組織レベルチェック
        org_results = checker.check_organization_compliance()
        
        # リポジトリチェック
        if args.repos:
            repo_names = args.repos
        else:
            # 全リポジトリ取得
            repos_data = checker._make_request(f"orgs/{args.org}/repos")
            repo_names = [repo['name'] for repo in repos_data]
        
        logger.info(f"準拠チェック開始: {len(repo_names)} リポジトリ")
        
        repo_results = []
        for repo_name in repo_names:
            try:
                result = checker.check_repository_compliance(repo_name)
                repo_results.append({
                    'repository': result.repository,
                    'overall_score': result.overall_score,
                    'checks': [asdict(check) for check in result.checks],
                    'recommendations': result.recommendations,
                    'timestamp': result.timestamp.isoformat()
                })
                logger.info(f"完了: {repo_name} (スコア: {result.overall_score:.1f}%)")
                
            except Exception as e:
                logger.error(f"チェックエラー ({repo_name}): {e}")
                continue
        
        # レポート生成
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        
        report_data = {
            'organization': args.org,
            'timestamp': datetime.now().isoformat(),
            'organization_checks': [asdict(check) for check in org_results],
            'repositories': repo_results
        }
        
        # JSON出力
        if args.format in ['json', 'both']:
            json_file = output_dir / f'compliance-report-{timestamp}.json'
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            logger.info(f"JSONレポート生成: {json_file}")
        
        # HTML出力
        if args.format in ['html', 'both']:
            html_file = output_dir / f'compliance-report-{timestamp}.html'
            generate_html_report(report_data, html_file)
            logger.info(f"HTMLレポート生成: {html_file}")
        
        # サマリー表示
        scores = [r['overall_score'] for r in repo_results]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        print(f"\n=== 準拠チェック結果サマリー ===")
        print(f"組織: {args.org}")
        print(f"チェック対象リポジトリ: {len(repo_results)}")
        print(f"平均準拠スコア: {avg_score:.1f}%")
        print(f"高スコア(80%+): {len([s for s in scores if s >= 80])}リポジトリ")
        print(f"要改善(60%未満): {len([s for s in scores if s < 60])}リポジトリ")
        
        logger.info("GitHub ガイドライン準拠チェック完了")
        
    except KeyboardInterrupt:
        logger.info("処理が中断されました")
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()