#!/usr/bin/env python3
"""
GitHub Actions ワークフロー検証ツール
エス・エー・エス株式会社
バージョン: 1.0.0

高度なワークフロー分析と検証を実行
"""

import os
import sys
import yaml
import json
import argparse
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging


class Severity(Enum):
    """問題の重要度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ValidationIssue:
    """検証で見つかった問題"""
    severity: Severity
    category: str
    message: str
    file_path: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    suggestion: Optional[str] = None
    rule_id: Optional[str] = None


@dataclass
class ValidationResult:
    """検証結果"""
    passed: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)


class WorkflowValidator:
    """GitHub Actionsワークフロー検証クラス"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)
        
        # セキュリティパターン
        self.security_patterns = {
            'hardcoded_secrets': [
                r'(password|token|key|secret|api[_-]?key)\s*[:=]\s*["\'][^"\']{8,}["\']',
                r'(aws[_-]?access[_-]?key|aws[_-]?secret|github[_-]?token)\s*[:=]',
            ],
            'dangerous_commands': [
                r'curl\s+.*\|\s*(bash|sh|zsh)',
                r'wget\s+.*-O.*\|\s*(bash|sh|zsh)',
                r'eval\s*\$\(',
                r'\$\{.*\}.*\|\s*(bash|sh|zsh)',
            ],
            'unsafe_checkout': [
                r'actions/checkout@(main|master|HEAD)',
                r'checkout@v[0-9]+(?:\.[0-9]+)*$',  # 最新バージョンでない場合
            ],
        }
        
        # パフォーマンスチェック用の設定
        self.performance_thresholds = {
            'max_jobs': 50,
            'max_steps_per_job': 30,
            'max_workflow_timeout': 360,  # 6時間
            'recommended_cache_actions': [
                'actions/cache',
                'actions/setup-node',
                'actions/setup-python',
                'actions/setup-java',
            ],
        }

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        default_config = {
            'rules': {
                'require_timeout': True,
                'require_name': True,
                'check_security': True,
                'check_performance': True,
                'check_best_practices': True,
            },
            'severity_levels': {
                'missing_timeout': 'medium',
                'hardcoded_secrets': 'critical',
                'unsafe_actions': 'high',
                'performance_issues': 'medium',
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                default_config.update(user_config)
            except Exception as e:
                self.logger.warning(f"設定ファイル読み込みエラー: {e}")
        
        return default_config

    def validate_directory(self, directory_path: str) -> ValidationResult:
        """ディレクトリ内のすべてのワークフローを検証"""
        workflows_path = Path(directory_path) / '.github' / 'workflows'
        
        if not workflows_path.exists():
            return ValidationResult(
                passed=False,
                issues=[ValidationIssue(
                    severity=Severity.CRITICAL,
                    category="structure",
                    message="workflows ディレクトリが存在しません",
                    file_path=str(workflows_path),
                    rule_id="MISSING_WORKFLOWS_DIR"
                )]
            )
        
        all_issues = []
        all_warnings = []
        stats = {
            'total_workflows': 0,
            'valid_workflows': 0,
            'invalid_workflows': 0,
            'total_jobs': 0,
            'total_steps': 0,
        }
        
        # ワークフローファイルを検索
        workflow_files = list(workflows_path.glob('*.yml')) + list(workflows_path.glob('*.yaml'))
        stats['total_workflows'] = len(workflow_files)
        
        for workflow_file in workflow_files:
            result = self.validate_workflow(str(workflow_file))
            
            if result.passed:
                stats['valid_workflows'] += 1
            else:
                stats['invalid_workflows'] += 1
            
            all_issues.extend(result.issues)
            all_warnings.extend(result.warnings)
            
            # 統計情報を更新
            if 'jobs_count' in result.stats:
                stats['total_jobs'] += result.stats['jobs_count']
            if 'steps_count' in result.stats:
                stats['total_steps'] += result.stats['steps_count']
        
        # 全体的なチェック
        all_issues.extend(self._check_overall_structure(directory_path))
        
        return ValidationResult(
            passed=len([i for i in all_issues if i.severity in [Severity.CRITICAL, Severity.HIGH]]) == 0,
            issues=all_issues,
            warnings=all_warnings,
            stats=stats
        )

    def validate_workflow(self, file_path: str) -> ValidationResult:
        """単一のワークフローファイルを検証"""
        issues = []
        warnings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                workflow_data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            return ValidationResult(
                passed=False,
                issues=[ValidationIssue(
                    severity=Severity.CRITICAL,
                    category="syntax",
                    message=f"YAML構文エラー: {str(e)}",
                    file_path=file_path,
                    rule_id="YAML_SYNTAX_ERROR"
                )]
            )
        except Exception as e:
            return ValidationResult(
                passed=False,
                issues=[ValidationIssue(
                    severity=Severity.CRITICAL,
                    category="file",
                    message=f"ファイル読み込みエラー: {str(e)}",
                    file_path=file_path,
                    rule_id="FILE_READ_ERROR"
                )]
            )
        
        if not isinstance(workflow_data, dict):
            return ValidationResult(
                passed=False,
                issues=[ValidationIssue(
                    severity=Severity.CRITICAL,
                    category="structure",
                    message="無効なワークフロー構造",
                    file_path=file_path,
                    rule_id="INVALID_STRUCTURE"
                )]
            )
        
        # 各種チェックを実行
        issues.extend(self._check_required_fields(workflow_data, file_path))
        issues.extend(self._check_security(workflow_data, file_path, content))
        issues.extend(self._check_performance(workflow_data, file_path))
        issues.extend(self._check_best_practices(workflow_data, file_path))
        
        warnings.extend(self._check_recommendations(workflow_data, file_path))
        
        # 統計情報を収集
        stats = self._collect_stats(workflow_data)
        
        # 結果判定
        critical_issues = [i for i in issues if i.severity == Severity.CRITICAL]
        
        return ValidationResult(
            passed=len(critical_issues) == 0,
            issues=issues,
            warnings=warnings,
            stats=stats
        )

    def _check_required_fields(self, workflow: Dict[str, Any], file_path: str) -> List[ValidationIssue]:
        """必須フィールドのチェック"""
        issues = []
        
        # 必須フィールド
        required_fields = ['on', 'jobs']
        for field in required_fields:
            if field not in workflow:
                issues.append(ValidationIssue(
                    severity=Severity.CRITICAL,
                    category="structure",
                    message=f"必須フィールド '{field}' がありません",
                    file_path=file_path,
                    suggestion=f"ワークフローに '{field}' フィールドを追加してください",
                    rule_id=f"MISSING_{field.upper()}"
                ))
        
        # 名前フィールドの推奨
        if 'name' not in workflow and self.config['rules']['require_name']:
            issues.append(ValidationIssue(
                severity=Severity.MEDIUM,
                category="structure",
                message="ワークフロー名が指定されていません",
                file_path=file_path,
                suggestion="わかりやすい 'name' を指定することを推奨します",
                rule_id="MISSING_NAME"
            ))
        
        return issues

    def _check_security(self, workflow: Dict[str, Any], file_path: str, content: str) -> List[ValidationIssue]:
        """セキュリティチェック"""
        issues = []
        
        if not self.config['rules']['check_security']:
            return issues
        
        # ハードコードされたシークレットの検出
        for pattern_name, patterns in self.security_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    issues.append(ValidationIssue(
                        severity=Severity.CRITICAL,
                        category="security",
                        message=f"セキュリティリスク: {pattern_name}が検出されました",
                        file_path=file_path,
                        line_number=line_num,
                        suggestion="シークレットはGitHub Secretsを使用してください",
                        rule_id=f"SECURITY_{pattern_name.upper()}"
                    ))
        
        # permissions の検証
        if 'permissions' in workflow:
            perms = workflow['permissions']
            if perms == 'write-all' or (isinstance(perms, dict) and 'write-all' in perms.values()):
                issues.append(ValidationIssue(
                    severity=Severity.HIGH,
                    category="security",
                    message="過剰な権限が設定されています (write-all)",
                    file_path=file_path,
                    suggestion="必要最小限の権限のみを指定してください",
                    rule_id="EXCESSIVE_PERMISSIONS"
                ))
        
        # pull_request_target の安全性チェック
        if 'on' in workflow:
            triggers = workflow['on']
            if isinstance(triggers, dict) and 'pull_request_target' in triggers:
                # 安全なガードの確認
                safe_guard_found = False
                if 'jobs' in workflow:
                    for job in workflow['jobs'].values():
                        if isinstance(job, dict) and 'if' in job:
                            if 'github.event.pull_request.head.repo.full_name' in str(job['if']):
                                safe_guard_found = True
                                break
                
                if not safe_guard_found:
                    issues.append(ValidationIssue(
                        severity=Severity.CRITICAL,
                        category="security",
                        message="pull_request_targetの安全でない使用",
                        file_path=file_path,
                        suggestion="フォークからのPRに対する安全ガードを追加してください",
                        rule_id="UNSAFE_PR_TARGET"
                    ))
        
        # アクションのバージョン固定チェック
        self._check_action_versions(workflow, file_path, issues)
        
        return issues

    def _check_action_versions(self, workflow: Dict[str, Any], file_path: str, issues: List[ValidationIssue]):
        """アクションのバージョン固定をチェック"""
        if 'jobs' not in workflow:
            return
        
        for job_name, job in workflow['jobs'].items():
            if not isinstance(job, dict) or 'steps' not in job:
                continue
            
            for step_idx, step in enumerate(job['steps']):
                if not isinstance(step, dict) or 'uses' not in step:
                    continue
                
                uses = step['uses']
                # メジャーバージョンのみの指定（危険）
                if re.match(r'^[^@]+@v\d+$', uses):
                    issues.append(ValidationIssue(
                        severity=Severity.HIGH,
                        category="security",
                        message=f"アクション '{uses}' がメジャーバージョンのみ固定",
                        file_path=file_path,
                        suggestion="セミナーバージョンまで固定することを推奨 (例: @v1.2.3)",
                        rule_id="ACTION_VERSION_PINNING"
                    ))
                
                # ブランチ指定（危険）
                elif re.match(r'^[^@]+@(main|master|develop|HEAD)$', uses):
                    issues.append(ValidationIssue(
                        severity=Severity.CRITICAL,
                        category="security",
                        message=f"アクション '{uses}' が不安定なブランチを参照",
                        file_path=file_path,
                        suggestion="具体的なバージョンタグを指定してください",
                        rule_id="ACTION_BRANCH_REFERENCE"
                    ))

    def _check_performance(self, workflow: Dict[str, Any], file_path: str) -> List[ValidationIssue]:
        """パフォーマンスチェック"""
        issues = []
        
        if not self.config['rules']['check_performance']:
            return issues
        
        if 'jobs' not in workflow:
            return issues
        
        jobs = workflow['jobs']
        
        # ジョブ数のチェック
        if len(jobs) > self.performance_thresholds['max_jobs']:
            issues.append(ValidationIssue(
                severity=Severity.MEDIUM,
                category="performance",
                message=f"ジョブ数が多すぎます ({len(jobs)} > {self.performance_thresholds['max_jobs']})",
                file_path=file_path,
                suggestion="ジョブをより効率的に統合することを検討してください",
                rule_id="TOO_MANY_JOBS"
            ))
        
        for job_name, job in jobs.items():
            if not isinstance(job, dict):
                continue
            
            # タイムアウトチェック
            if 'timeout-minutes' not in job and self.config['rules']['require_timeout']:
                issues.append(ValidationIssue(
                    severity=Severity.MEDIUM,
                    category="performance",
                    message=f"ジョブ '{job_name}' にタイムアウトが設定されていません",
                    file_path=file_path,
                    suggestion="timeout-minutesを設定してリソース使用量を制御してください",
                    rule_id="MISSING_TIMEOUT"
                ))
            elif 'timeout-minutes' in job:
                timeout = job['timeout-minutes']
                if timeout > self.performance_thresholds['max_workflow_timeout']:
                    issues.append(ValidationIssue(
                        severity=Severity.MEDIUM,
                        category="performance",
                        message=f"ジョブ '{job_name}' のタイムアウトが長すぎます ({timeout}分)",
                        file_path=file_path,
                        suggestion=f"{self.performance_thresholds['max_workflow_timeout']}分以下に設定することを推奨",
                        rule_id="LONG_TIMEOUT"
                    ))
            
            # ステップ数チェック
            if 'steps' in job:
                steps_count = len(job['steps'])
                if steps_count > self.performance_thresholds['max_steps_per_job']:
                    issues.append(ValidationIssue(
                        severity=Severity.MEDIUM,
                        category="performance",
                        message=f"ジョブ '{job_name}' のステップ数が多すぎます ({steps_count})",
                        file_path=file_path,
                        suggestion="ジョブを分割するか、ステップを統合することを検討してください",
                        rule_id="TOO_MANY_STEPS"
                    ))
                
                # キャッシュ使用の確認
                self._check_cache_usage(job, job_name, file_path, issues)
        
        return issues

    def _check_cache_usage(self, job: Dict[str, Any], job_name: str, file_path: str, issues: List[ValidationIssue]):
        """キャッシュ使用の確認"""
        if 'steps' not in job:
            return
        
        # 依存関係管理ツールの使用を検出
        package_managers = []
        cache_used = False
        
        for step in job['steps']:
            if not isinstance(step, dict):
                continue
            
            # run コマンドから依存関係管理ツールを検出
            if 'run' in step:
                run_command = step['run'].lower()
                if any(pm in run_command for pm in ['npm install', 'yarn install', 'pip install', 'mvn', 'gradle']):
                    if 'npm' in run_command:
                        package_managers.append('npm')
                    if 'yarn' in run_command:
                        package_managers.append('yarn')
                    if 'pip' in run_command:
                        package_managers.append('pip')
                    if 'mvn' in run_command:
                        package_managers.append('maven')
                    if 'gradle' in run_command:
                        package_managers.append('gradle')
            
            # キャッシュアクションの使用を確認
            if 'uses' in step:
                uses = step['uses']
                if any(cache_action in uses for cache_action in self.performance_thresholds['recommended_cache_actions']):
                    cache_used = True
        
        # 依存関係管理ツールを使用しているがキャッシュを使用していない場合
        if package_managers and not cache_used:
            issues.append(ValidationIssue(
                severity=Severity.MEDIUM,
                category="performance",
                message=f"ジョブ '{job_name}' で依存関係キャッシュの使用を検討してください",
                file_path=file_path,
                suggestion=f"検出された依存関係管理ツール: {', '.join(set(package_managers))}",
                rule_id="MISSING_CACHE"
            ))

    def _check_best_practices(self, workflow: Dict[str, Any], file_path: str) -> List[ValidationIssue]:
        """ベストプラクティスチェック"""
        issues = []
        
        if not self.config['rules']['check_best_practices']:
            return issues
        
        # 環境変数の設定方法チェック
        if 'env' in workflow:
            for key, value in workflow['env'].items():
                if isinstance(value, str) and len(value) > 100:
                    issues.append(ValidationIssue(
                        severity=Severity.LOW,
                        category="best_practices",
                        message=f"環境変数 '{key}' の値が長すぎます",
                        file_path=file_path,
                        suggestion="長い値はSecretsまたはファイルから読み込むことを検討してください",
                        rule_id="LONG_ENV_VALUE"
                    ))
        
        # concurrency の使用推奨
        if 'concurrency' not in workflow:
            # PRワークフローの場合は concurrency を推奨
            if self._is_pr_workflow(workflow):
                issues.append(ValidationIssue(
                    severity=Severity.LOW,
                    category="best_practices",
                    message="PRワークフローにconcurrencyの設定を推奨",
                    file_path=file_path,
                    suggestion="同じPRに対する複数実行を制御するためconcurrencyを設定してください",
                    rule_id="MISSING_CONCURRENCY"
                ))
        
        return issues

    def _check_recommendations(self, workflow: Dict[str, Any], file_path: str) -> List[ValidationIssue]:
        """推奨事項チェック（警告レベル）"""
        warnings = []
        
        # デフォルトブランチ以外での実行チェック
        if 'on' in workflow:
            triggers = workflow['on']
            if isinstance(triggers, dict):
                if 'push' in triggers:
                    push_config = triggers['push']
                    if isinstance(push_config, dict) and 'branches' not in push_config:
                        warnings.append(ValidationIssue(
                            severity=Severity.INFO,
                            category="recommendations",
                            message="pushトリガーでブランチ制限の設定を推奨",
                            file_path=file_path,
                            suggestion="不要なワークフロー実行を避けるため、ブランチを指定してください",
                            rule_id="UNRESTRICTED_PUSH"
                        ))
        
        return warnings

    def _check_overall_structure(self, directory_path: str) -> List[ValidationIssue]:
        """全体構造のチェック"""
        issues = []
        path = Path(directory_path)
        
        # 基本的なファイル構造チェック
        recommended_files = {
            '.github/CODEOWNERS': "コードオーナーシップの明確化",
            '.github/dependabot.yml': "自動依存関係更新",
            '.github/ISSUE_TEMPLATE': "Issue テンプレート",
            '.github/PULL_REQUEST_TEMPLATE.md': "PR テンプレート",
        }
        
        for file_path, description in recommended_files.items():
            full_path = path / file_path
            if not full_path.exists():
                # ディレクトリの場合は、任意のファイルが存在するかチェック
                if file_path.endswith('TEMPLATE'):
                    if not any(full_path.parent.glob(f"{full_path.name}*")):
                        issues.append(ValidationIssue(
                            severity=Severity.LOW,
                            category="structure",
                            message=f"推奨ファイル/ディレクトリが存在しません: {file_path}",
                            file_path=str(full_path),
                            suggestion=description,
                            rule_id="MISSING_RECOMMENDED_FILE"
                        ))
                else:
                    issues.append(ValidationIssue(
                        severity=Severity.LOW,
                        category="structure",
                        message=f"推奨ファイルが存在しません: {file_path}",
                        file_path=str(full_path),
                        suggestion=description,
                        rule_id="MISSING_RECOMMENDED_FILE"
                    ))
        
        return issues

    def _collect_stats(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """統計情報を収集"""
        stats = {
            'jobs_count': 0,
            'steps_count': 0,
            'uses_actions': [],
            'triggers': [],
        }
        
        if 'jobs' in workflow:
            stats['jobs_count'] = len(workflow['jobs'])
            
            for job in workflow['jobs'].values():
                if isinstance(job, dict) and 'steps' in job:
                    stats['steps_count'] += len(job['steps'])
                    
                    for step in job['steps']:
                        if isinstance(step, dict) and 'uses' in step:
                            action = step['uses'].split('@')[0]
                            if action not in stats['uses_actions']:
                                stats['uses_actions'].append(action)
        
        if 'on' in workflow:
            triggers = workflow['on']
            if isinstance(triggers, list):
                stats['triggers'] = triggers
            elif isinstance(triggers, dict):
                stats['triggers'] = list(triggers.keys())
            else:
                stats['triggers'] = [str(triggers)]
        
        return stats

    def _is_pr_workflow(self, workflow: Dict[str, Any]) -> bool:
        """PRワークフローかどうかを判定"""
        if 'on' not in workflow:
            return False
        
        triggers = workflow['on']
        if isinstance(triggers, dict):
            return 'pull_request' in triggers or 'pull_request_target' in triggers
        elif isinstance(triggers, list):
            return 'pull_request' in triggers or 'pull_request_target' in triggers
        
        return False

    def generate_report(self, result: ValidationResult, format_type: str = 'text') -> str:
        """レポート生成"""
        if format_type == 'json':
            return self._generate_json_report(result)
        elif format_type == 'junit':
            return self._generate_junit_report(result)
        else:
            return self._generate_text_report(result)

    def _generate_text_report(self, result: ValidationResult) -> str:
        """テキスト形式のレポート生成"""
        lines = []
        lines.append("=" * 60)
        lines.append("GitHub Actions ワークフロー検証レポート")
        lines.append("=" * 60)
        lines.append("")
        
        # 統計情報
        if result.stats:
            lines.append("📊 統計情報:")
            for key, value in result.stats.items():
                lines.append(f"  {key}: {value}")
            lines.append("")
        
        # 問題のサマリー
        critical = len([i for i in result.issues if i.severity == Severity.CRITICAL])
        high = len([i for i in result.issues if i.severity == Severity.HIGH])
        medium = len([i for i in result.issues if i.severity == Severity.MEDIUM])
        low = len([i for i in result.issues if i.severity == Severity.LOW])
        
        lines.append("🔍 検証結果:")
        lines.append(f"  総合判定: {'✅ 合格' if result.passed else '❌ 不合格'}")
        lines.append(f"  Critical: {critical}")
        lines.append(f"  High:     {high}")
        lines.append(f"  Medium:   {medium}")
        lines.append(f"  Low:      {low}")
        lines.append(f"  警告:     {len(result.warnings)}")
        lines.append("")
        
        # 問題詳細
        if result.issues:
            lines.append("🚨 検出された問題:")
            lines.append("")
            
            # 重要度順にソート
            sorted_issues = sorted(result.issues, key=lambda x: ['critical', 'high', 'medium', 'low'].index(x.severity.value))
            
            for issue in sorted_issues:
                severity_icon = {
                    Severity.CRITICAL: "🔴",
                    Severity.HIGH: "🟠",
                    Severity.MEDIUM: "🟡",
                    Severity.LOW: "⚪",
                }.get(issue.severity, "❓")
                
                lines.append(f"{severity_icon} [{issue.severity.value.upper()}] {issue.message}")
                lines.append(f"   📁 ファイル: {issue.file_path}")
                if issue.line_number:
                    lines.append(f"   📍 行: {issue.line_number}")
                if issue.suggestion:
                    lines.append(f"   💡 提案: {issue.suggestion}")
                if issue.rule_id:
                    lines.append(f"   🏷️  ルール: {issue.rule_id}")
                lines.append("")
        
        # 警告
        if result.warnings:
            lines.append("⚠️  警告:")
            lines.append("")
            
            for warning in result.warnings:
                lines.append(f"⚠️  {warning.message}")
                lines.append(f"   📁 ファイル: {warning.file_path}")
                if warning.suggestion:
                    lines.append(f"   💡 提案: {warning.suggestion}")
                lines.append("")
        
        return "\n".join(lines)

    def _generate_json_report(self, result: ValidationResult) -> str:
        """JSON形式のレポート生成"""
        report_data = {
            'passed': result.passed,
            'stats': result.stats,
            'summary': {
                'total_issues': len(result.issues),
                'critical': len([i for i in result.issues if i.severity == Severity.CRITICAL]),
                'high': len([i for i in result.issues if i.severity == Severity.HIGH]),
                'medium': len([i for i in result.issues if i.severity == Severity.MEDIUM]),
                'low': len([i for i in result.issues if i.severity == Severity.LOW]),
                'warnings': len(result.warnings),
            },
            'issues': [
                {
                    'severity': issue.severity.value,
                    'category': issue.category,
                    'message': issue.message,
                    'file_path': issue.file_path,
                    'line_number': issue.line_number,
                    'column_number': issue.column_number,
                    'suggestion': issue.suggestion,
                    'rule_id': issue.rule_id,
                }
                for issue in result.issues
            ],
            'warnings': [
                {
                    'severity': warning.severity.value,
                    'category': warning.category,
                    'message': warning.message,
                    'file_path': warning.file_path,
                    'line_number': warning.line_number,
                    'column_number': warning.column_number,
                    'suggestion': warning.suggestion,
                    'rule_id': warning.rule_id,
                }
                for warning in result.warnings
            ],
        }
        
        return json.dumps(report_data, indent=2, ensure_ascii=False)

    def _generate_junit_report(self, result: ValidationResult) -> str:
        """JUnit XML形式のレポート生成"""
        from xml.etree.ElementTree import Element, SubElement, tostring
        from xml.dom import minidom
        
        testsuites = Element('testsuites')
        testsuite = SubElement(testsuites, 'testsuite')
        testsuite.set('name', 'GitHub Actions Validation')
        testsuite.set('tests', str(len(result.issues) + len(result.warnings)))
        testsuite.set('failures', str(len(result.issues)))
        testsuite.set('errors', '0')
        testsuite.set('skipped', str(len(result.warnings)))
        
        for issue in result.issues:
            testcase = SubElement(testsuite, 'testcase')
            testcase.set('classname', f"{issue.category}.{issue.rule_id or 'unknown'}")
            testcase.set('name', issue.message)
            
            failure = SubElement(testcase, 'failure')
            failure.set('message', issue.message)
            failure.text = f"File: {issue.file_path}\nLine: {issue.line_number or 'N/A'}\nSuggestion: {issue.suggestion or 'N/A'}"
        
        for warning in result.warnings:
            testcase = SubElement(testsuite, 'testcase')
            testcase.set('classname', f"{warning.category}.{warning.rule_id or 'unknown'}")
            testcase.set('name', warning.message)
            
            skipped = SubElement(testcase, 'skipped')
            skipped.set('message', warning.message)
        
        # XML文字列を整形
        rough_string = tostring(testsuites, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='GitHub Actions ワークフロー検証ツール',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  %(prog)s /path/to/repository
  %(prog)s --format json --output report.json .
  %(prog)s --config custom-rules.yml /path/to/repo
        """
    )
    
    parser.add_argument('path', nargs='?', default='.',
                        help='検証するリポジトリのパス (デフォルト: 現在のディレクトリ)')
    parser.add_argument('-c', '--config', type=str,
                        help='カスタム設定ファイルのパス')
    parser.add_argument('-f', '--format', choices=['text', 'json', 'junit'],
                        default='text', help='出力形式 (デフォルト: text)')
    parser.add_argument('-o', '--output', type=str,
                        help='結果を出力するファイルパス')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='詳細な出力を表示')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0.0')
    
    args = parser.parse_args()
    
    # ログレベル設定
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')
    
    # バリデーター初期化
    validator = WorkflowValidator(args.config)
    
    # 検証実行
    try:
        if os.path.isfile(args.path) and args.path.endswith(('.yml', '.yaml')):
            # 単一ファイルの検証
            result = validator.validate_workflow(args.path)
        else:
            # ディレクトリの検証
            result = validator.validate_directory(args.path)
        
        # レポート生成
        report = validator.generate_report(result, args.format)
        
        # 出力
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"結果を {args.output} に出力しました")
        else:
            print(report)
        
        # 終了コード
        sys.exit(0 if result.passed else 1)
        
    except Exception as e:
        logging.error(f"エラーが発生しました: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(2)


if __name__ == '__main__':
    main()