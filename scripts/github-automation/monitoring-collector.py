#!/usr/bin/env python3
"""
GitHub Analytics データ収集パイプライン
エス・エー・エス株式会社

用途: GitHub組織のメトリクス収集、分析、レポート生成
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests
import argparse
from dataclasses import dataclass, asdict
import sqlite3
import pandas as pd
from pathlib import Path

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/github-monitoring.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class GitHubMetrics:
    """GitHub メトリクスデータクラス"""
    repository: str
    timestamp: datetime
    commits_count: int
    pull_requests_open: int
    pull_requests_closed: int
    issues_open: int
    issues_closed: int
    contributors: int
    stars: int
    forks: int
    security_alerts: int
    deployment_frequency: float
    lead_time_hours: float
    change_failure_rate: float
    recovery_time_minutes: float
    
class GitHubCollector:
    """GitHub API データコレクター"""
    
    def __init__(self, token: str, org: str):
        self.token = token
        self.org = org
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = 'https://api.github.com'
        self.rate_limit_remaining = 5000
        
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """GitHub API リクエスト実行"""
        url = f"{self.base_url}/{endpoint}"
        
        # Rate limit チェック
        if self.rate_limit_remaining < 100:
            logger.warning("API rate limit が少ないです。1時間待機します...")
            time.sleep(3600)
            
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            # Rate limit 情報を更新
            self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
            
    def get_repositories(self) -> List[Dict]:
        """組織のリポジトリ一覧取得"""
        logger.info(f"組織 {self.org} のリポジトリを取得中...")
        
        repos = []
        page = 1
        per_page = 100
        
        while True:
            data = self._make_request(
                f"orgs/{self.org}/repos",
                params={'page': page, 'per_page': per_page, 'sort': 'updated'}
            )
            
            if not data:
                break
                
            repos.extend(data)
            
            if len(data) < per_page:
                break
                
            page += 1
            
        logger.info(f"取得したリポジトリ数: {len(repos)}")
        return repos
    
    def get_repository_metrics(self, repo_name: str) -> GitHubMetrics:
        """リポジトリのメトリクス取得"""
        logger.debug(f"リポジトリ {repo_name} のメトリクスを取得中...")
        
        # 基本情報
        repo_data = self._make_request(f"repos/{self.org}/{repo_name}")
        
        # コミット数（過去30日）
        since = (datetime.now() - timedelta(days=30)).isoformat()
        commits_data = self._make_request(
            f"repos/{self.org}/{repo_name}/commits",
            params={'since': since, 'per_page': 100}
        )
        commits_count = len(commits_data) if isinstance(commits_data, list) else 0
        
        # プルリクエスト
        pr_open = self._make_request(
            f"repos/{self.org}/{repo_name}/pulls",
            params={'state': 'open'}
        )
        pr_closed = self._make_request(
            f"repos/{self.org}/{repo_name}/pulls",
            params={'state': 'closed', 'since': since}
        )
        
        # Issues
        issues_open = self._make_request(
            f"repos/{self.org}/{repo_name}/issues",
            params={'state': 'open'}
        )
        issues_closed = self._make_request(
            f"repos/{self.org}/{repo_name}/issues",
            params={'state': 'closed', 'since': since}
        )
        
        # 貢献者
        contributors = self._make_request(f"repos/{self.org}/{repo_name}/contributors")
        
        # セキュリティアラート
        try:
            security_alerts = self._make_request(
                f"repos/{self.org}/{repo_name}/vulnerability-alerts"
            )
        except:
            security_alerts = []
            
        # DORA メトリクス（簡易版）
        deployment_frequency = self._calculate_deployment_frequency(repo_name)
        lead_time_hours = self._calculate_lead_time(repo_name)
        change_failure_rate = self._calculate_change_failure_rate(repo_name)
        recovery_time_minutes = self._calculate_recovery_time(repo_name)
        
        return GitHubMetrics(
            repository=repo_name,
            timestamp=datetime.now(),
            commits_count=commits_count,
            pull_requests_open=len(pr_open) if isinstance(pr_open, list) else 0,
            pull_requests_closed=len(pr_closed) if isinstance(pr_closed, list) else 0,
            issues_open=len(issues_open) if isinstance(issues_open, list) else 0,
            issues_closed=len(issues_closed) if isinstance(issues_closed, list) else 0,
            contributors=len(contributors) if isinstance(contributors, list) else 0,
            stars=repo_data.get('stargazers_count', 0),
            forks=repo_data.get('forks_count', 0),
            security_alerts=len(security_alerts) if isinstance(security_alerts, list) else 0,
            deployment_frequency=deployment_frequency,
            lead_time_hours=lead_time_hours,
            change_failure_rate=change_failure_rate,
            recovery_time_minutes=recovery_time_minutes
        )
    
    def _calculate_deployment_frequency(self, repo_name: str) -> float:
        """デプロイメント頻度計算（週次）"""
        try:
            # GitHub Environments または Releases をベースに計算
            releases = self._make_request(f"repos/{self.org}/{repo_name}/releases")
            
            if not isinstance(releases, list) or len(releases) == 0:
                return 0.0
                
            # 過去30日のリリース数を週次頻度に変換
            recent_releases = [
                r for r in releases[:10] 
                if datetime.fromisoformat(r['published_at'].replace('Z', '+00:00')) 
                > datetime.now() - timedelta(days=30)
            ]
            
            return len(recent_releases) / 4.0  # 週次頻度
            
        except Exception as e:
            logger.warning(f"デプロイメント頻度計算エラー ({repo_name}): {e}")
            return 0.0
    
    def _calculate_lead_time(self, repo_name: str) -> float:
        """リードタイム計算（PR作成からマージまでの時間）"""
        try:
            since = (datetime.now() - timedelta(days=30)).isoformat()
            closed_prs = self._make_request(
                f"repos/{self.org}/{repo_name}/pulls",
                params={'state': 'closed', 'since': since}
            )
            
            if not isinstance(closed_prs, list) or len(closed_prs) == 0:
                return 0.0
                
            lead_times = []
            for pr in closed_prs[:20]:  # 最新20件
                if pr.get('merged_at'):
                    created = datetime.fromisoformat(pr['created_at'].replace('Z', '+00:00'))
                    merged = datetime.fromisoformat(pr['merged_at'].replace('Z', '+00:00'))
                    lead_times.append((merged - created).total_seconds() / 3600)
            
            return sum(lead_times) / len(lead_times) if lead_times else 0.0
            
        except Exception as e:
            logger.warning(f"リードタイム計算エラー ({repo_name}): {e}")
            return 0.0
    
    def _calculate_change_failure_rate(self, repo_name: str) -> float:
        """変更失敗率計算"""
        try:
            # Hotfix/Bugfix PRの比率で簡易計算
            since = (datetime.now() - timedelta(days=30)).isoformat()
            all_prs = self._make_request(
                f"repos/{self.org}/{repo_name}/pulls",
                params={'state': 'closed', 'since': since}
            )
            
            if not isinstance(all_prs, list) or len(all_prs) == 0:
                return 0.0
                
            bug_fix_prs = [
                pr for pr in all_prs 
                if any(keyword in pr.get('title', '').lower() 
                      for keyword in ['hotfix', 'bugfix', 'fix:', 'bug:'])
            ]
            
            return len(bug_fix_prs) / len(all_prs)
            
        except Exception as e:
            logger.warning(f"変更失敗率計算エラー ({repo_name}): {e}")
            return 0.0
    
    def _calculate_recovery_time(self, repo_name: str) -> float:
        """復旧時間計算（分）"""
        try:
            # Issue の解決時間を基に簡易計算
            since = (datetime.now() - timedelta(days=30)).isoformat()
            closed_issues = self._make_request(
                f"repos/{self.org}/{repo_name}/issues",
                params={'state': 'closed', 'since': since, 'labels': 'bug,critical'}
            )
            
            if not isinstance(closed_issues, list) or len(closed_issues) == 0:
                return 0.0
                
            recovery_times = []
            for issue in closed_issues[:10]:
                if issue.get('closed_at'):
                    created = datetime.fromisoformat(issue['created_at'].replace('Z', '+00:00'))
                    closed = datetime.fromisoformat(issue['closed_at'].replace('Z', '+00:00'))
                    recovery_times.append((closed - created).total_seconds() / 60)
            
            return sum(recovery_times) / len(recovery_times) if recovery_times else 0.0
            
        except Exception as e:
            logger.warning(f"復旧時間計算エラー ({repo_name}): {e}")
            return 0.0

class MetricsDatabase:
    """メトリクスデータベース管理"""
    
    def __init__(self, db_path: str = './data/github-metrics.db'):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """データベース初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repository TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    commits_count INTEGER,
                    pull_requests_open INTEGER,
                    pull_requests_closed INTEGER,
                    issues_open INTEGER,
                    issues_closed INTEGER,
                    contributors INTEGER,
                    stars INTEGER,
                    forks INTEGER,
                    security_alerts INTEGER,
                    deployment_frequency REAL,
                    lead_time_hours REAL,
                    change_failure_rate REAL,
                    recovery_time_minutes REAL,
                    UNIQUE(repository, timestamp)
                )
            """)
            conn.commit()
    
    def save_metrics(self, metrics: GitHubMetrics):
        """メトリクス保存"""
        with sqlite3.connect(self.db_path) as conn:
            data = asdict(metrics)
            data['timestamp'] = data['timestamp'].isoformat()
            
            placeholders = ', '.join(['?' for _ in data])
            columns = ', '.join(data.keys())
            
            conn.execute(
                f"INSERT OR REPLACE INTO metrics ({columns}) VALUES ({placeholders})",
                list(data.values())
            )
            conn.commit()
    
    def get_metrics_history(self, repository: str, days: int = 30) -> pd.DataFrame:
        """メトリクス履歴取得"""
        since = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT * FROM metrics 
                WHERE repository = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            """
            return pd.read_sql_query(query, conn, params=[repository, since.isoformat()])

class ReportGenerator:
    """レポート生成器"""
    
    def __init__(self, db: MetricsDatabase):
        self.db = db
    
    def generate_dora_report(self, org: str, days: int = 30) -> Dict:
        """DORA メトリクスレポート生成"""
        logger.info("DORA メトリクスレポートを生成中...")
        
        # 全リポジトリのメトリクス取得
        with sqlite3.connect(self.db.db_path) as conn:
            since = datetime.now() - timedelta(days=days)
            
            query = """
                SELECT 
                    repository,
                    AVG(deployment_frequency) as avg_deployment_frequency,
                    AVG(lead_time_hours) as avg_lead_time_hours,
                    AVG(change_failure_rate) as avg_change_failure_rate,
                    AVG(recovery_time_minutes) as avg_recovery_time_minutes
                FROM metrics 
                WHERE timestamp >= ?
                GROUP BY repository
            """
            
            df = pd.read_sql_query(query, conn, params=[since.isoformat()])
        
        # DORA レベル判定
        def get_dora_level(freq, lead_time, failure_rate, recovery_time):
            # 簡化された判定ロジック
            if freq >= 3 and lead_time <= 1 and failure_rate <= 0.05 and recovery_time <= 60:
                return "Elite"
            elif freq >= 1 and lead_time <= 24 and failure_rate <= 0.10 and recovery_time <= 240:
                return "High"
            elif freq >= 0.2 and lead_time <= 168 and failure_rate <= 0.15 and recovery_time <= 1440:
                return "Medium"
            else:
                return "Low"
        
        results = []
        for _, row in df.iterrows():
            level = get_dora_level(
                row['avg_deployment_frequency'],
                row['avg_lead_time_hours'],
                row['avg_change_failure_rate'],
                row['avg_recovery_time_minutes']
            )
            results.append({
                'repository': row['repository'],
                'deployment_frequency': row['avg_deployment_frequency'],
                'lead_time_hours': row['avg_lead_time_hours'],
                'change_failure_rate': row['avg_change_failure_rate'],
                'recovery_time_minutes': row['avg_recovery_time_minutes'],
                'dora_level': level
            })
        
        # 集約統計
        total_repos = len(results)
        level_distribution = {}
        for level in ['Elite', 'High', 'Medium', 'Low']:
            level_distribution[level] = len([r for r in results if r['dora_level'] == level])
        
        return {
            'organization': org,
            'period_days': days,
            'total_repositories': total_repos,
            'level_distribution': level_distribution,
            'repository_details': results,
            'generated_at': datetime.now().isoformat()
        }
    
    def generate_security_report(self, org: str, days: int = 30) -> Dict:
        """セキュリティレポート生成"""
        logger.info("セキュリティレポートを生成中...")
        
        with sqlite3.connect(self.db.db_path) as conn:
            since = datetime.now() - timedelta(days=days)
            
            # セキュリティアラート統計
            query = """
                SELECT 
                    repository,
                    MAX(security_alerts) as current_alerts,
                    AVG(security_alerts) as avg_alerts
                FROM metrics 
                WHERE timestamp >= ?
                GROUP BY repository
                ORDER BY current_alerts DESC
            """
            
            df = pd.read_sql_query(query, conn, params=[since.isoformat()])
        
        results = df.to_dict('records')
        
        return {
            'organization': org,
            'period_days': days,
            'total_repositories': len(results),
            'total_active_alerts': sum(r['current_alerts'] for r in results),
            'high_risk_repositories': [r for r in results if r['current_alerts'] > 5],
            'repository_details': results,
            'generated_at': datetime.now().isoformat()
        }

def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='GitHub Analytics データ収集')
    parser.add_argument('--org', required=True, help='GitHub組織名')
    parser.add_argument('--token', help='GitHub API トークン (環境変数 GITHUB_TOKEN を使用可能)')
    parser.add_argument('--repos', nargs='*', help='特定のリポジトリのみ収集')
    parser.add_argument('--report', choices=['dora', 'security', 'all'], 
                       default='all', help='生成するレポート種別')
    parser.add_argument('--days', type=int, default=30, help='分析期間（日数）')
    parser.add_argument('--output', default='./reports', help='出力ディレクトリ')
    
    args = parser.parse_args()
    
    # GitHub token 取得
    token = args.token or os.getenv('GITHUB_TOKEN')
    if not token:
        logger.error("GitHub API token が必要です。--token または GITHUB_TOKEN 環境変数を設定してください。")
        sys.exit(1)
    
    # 出力ディレクトリ作成
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # コンポーネント初期化
    collector = GitHubCollector(token, args.org)
    database = MetricsDatabase()
    report_generator = ReportGenerator(database)
    
    try:
        # データ収集
        if args.repos:
            repositories = [{'name': repo} for repo in args.repos]
        else:
            repositories = collector.get_repositories()
        
        logger.info(f"メトリクス収集開始: {len(repositories)} リポジトリ")
        
        for repo in repositories:
            repo_name = repo['name']
            try:
                metrics = collector.get_repository_metrics(repo_name)
                database.save_metrics(metrics)
                logger.info(f"収集完了: {repo_name}")
                
                # API rate limit 対策
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"収集エラー ({repo_name}): {e}")
                continue
        
        # レポート生成
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        
        if args.report in ['dora', 'all']:
            dora_report = report_generator.generate_dora_report(args.org, args.days)
            dora_file = output_dir / f'dora-report-{timestamp}.json'
            with open(dora_file, 'w', encoding='utf-8') as f:
                json.dump(dora_report, f, indent=2, ensure_ascii=False)
            logger.info(f"DORA レポート生成: {dora_file}")
        
        if args.report in ['security', 'all']:
            security_report = report_generator.generate_security_report(args.org, args.days)
            security_file = output_dir / f'security-report-{timestamp}.json'
            with open(security_file, 'w', encoding='utf-8') as f:
                json.dump(security_report, f, indent=2, ensure_ascii=False)
            logger.info(f"セキュリティレポート生成: {security_file}")
        
        logger.info("GitHub Analytics データ収集完了")
        
    except KeyboardInterrupt:
        logger.info("処理が中断されました")
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()