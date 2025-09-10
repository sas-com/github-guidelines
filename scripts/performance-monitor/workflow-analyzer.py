#!/usr/bin/env python3
"""
GitHub Actions Workflow Performance Analyzer
エス・エー・エス株式会社
"""

import json
import sys
import os
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
from dataclasses import dataclass, asdict
import statistics

@dataclass
class WorkflowMetrics:
    """ワークフローメトリクスデータクラス"""
    workflow_id: int
    workflow_name: str
    run_number: int
    status: str
    conclusion: Optional[str]
    created_at: str
    updated_at: str
    run_duration_seconds: float
    billable_minutes: Dict[str, float]
    total_cost_usd: float
    jobs_count: int
    steps_count: int
    cache_hit_rate: float
    parallel_efficiency: float
    failure_rate: float

class GitHubActionsAnalyzer:
    """GitHub Actions パフォーマンス分析ツール"""
    
    # GitHub Actions 料金（USD/分）
    PRICING = {
        'UBUNTU': 0.008,
        'WINDOWS': 0.016,
        'MACOS': 0.08
    }
    
    def __init__(self, token: str, owner: str, repo: str):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = f'https://api.github.com/repos/{owner}/{repo}'
    
    def fetch_workflow_runs(self, 
                           workflow_id: Optional[str] = None,
                           branch: Optional[str] = None,
                           status: Optional[str] = None,
                           per_page: int = 100) -> List[dict]:
        """ワークフロー実行履歴を取得"""
        params = {
            'per_page': per_page
        }
        
        if branch:
            params['branch'] = branch
        if status:
            params['status'] = status
        
        url = f"{self.base_url}/actions/workflows/{workflow_id}/runs" if workflow_id else f"{self.base_url}/actions/runs"
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        return response.json().get('workflow_runs', [])
    
    def fetch_workflow_jobs(self, run_id: int) -> List[dict]:
        """ワークフロー実行のジョブ詳細を取得"""
        url = f"{self.base_url}/actions/runs/{run_id}/jobs"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json().get('jobs', [])
    
    def fetch_workflow_timing(self, run_id: int) -> dict:
        """ワークフロー実行のタイミング情報を取得"""
        url = f"{self.base_url}/actions/runs/{run_id}/timing"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        return {}
    
    def calculate_duration(self, start: str, end: str) -> float:
        """実行時間を秒単位で計算"""
        if not start or not end:
            return 0.0
        
        start_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(end.replace('Z', '+00:00'))
        return (end_time - start_time).total_seconds()
    
    def calculate_billable_minutes(self, jobs: List[dict]) -> Dict[str, float]:
        """課金対象分数を計算"""
        billable = {
            'UBUNTU': 0.0,
            'WINDOWS': 0.0,
            'MACOS': 0.0
        }
        
        for job in jobs:
            if job.get('status') != 'completed':
                continue
            
            runner_os = job.get('runner_os', 'Linux').upper()
            if 'LINUX' in runner_os or 'UBUNTU' in runner_os:
                os_key = 'UBUNTU'
            elif 'WINDOWS' in runner_os:
                os_key = 'WINDOWS'
            elif 'MAC' in runner_os:
                os_key = 'MACOS'
            else:
                os_key = 'UBUNTU'
            
            duration = self.calculate_duration(
                job.get('started_at'),
                job.get('completed_at')
            )
            
            # 分単位に変換（1分未満は切り上げ）
            minutes = max(1, int(duration / 60) + (1 if duration % 60 > 0 else 0))
            billable[os_key] += minutes
        
        return billable
    
    def calculate_total_cost(self, billable_minutes: Dict[str, float]) -> float:
        """総コストを計算"""
        total = 0.0
        for os_type, minutes in billable_minutes.items():
            total += minutes * self.PRICING.get(os_type, 0.008)
        return round(total, 4)
    
    def calculate_cache_hit_rate(self, jobs: List[dict]) -> float:
        """キャッシュヒット率を計算"""
        cache_steps = 0
        cache_hits = 0
        
        for job in jobs:
            for step in job.get('steps', []):
                if 'cache' in step.get('name', '').lower():
                    cache_steps += 1
                    if step.get('conclusion') == 'success':
                        # 簡易的な判定（実際はログ解析が必要）
                        cache_hits += 1
        
        return (cache_hits / cache_steps * 100) if cache_steps > 0 else 0
    
    def calculate_parallel_efficiency(self, jobs: List[dict]) -> float:
        """並列実行効率を計算"""
        if not jobs:
            return 0
        
        # ジョブの開始・終了時刻から並列度を計算
        timeline = []
        for job in jobs:
            if job.get('started_at') and job.get('completed_at'):
                timeline.append((
                    datetime.fromisoformat(job['started_at'].replace('Z', '+00:00')),
                    datetime.fromisoformat(job['completed_at'].replace('Z', '+00:00'))
                ))
        
        if not timeline:
            return 0
        
        # 最大同時実行数を計算
        events = []
        for start, end in timeline:
            events.append((start, 1))  # ジョブ開始
            events.append((end, -1))    # ジョブ終了
        
        events.sort()
        current_parallel = 0
        max_parallel = 0
        
        for _, delta in events:
            current_parallel += delta
            max_parallel = max(max_parallel, current_parallel)
        
        # 効率 = 実際の並列数 / 理論最大並列数
        theoretical_max = len(jobs)
        efficiency = (max_parallel / theoretical_max * 100) if theoretical_max > 0 else 0
        
        return min(100, efficiency)
    
    def analyze_workflow_run(self, run: dict) -> WorkflowMetrics:
        """単一のワークフロー実行を分析"""
        run_id = run['id']
        
        # ジョブ情報を取得
        jobs = self.fetch_workflow_jobs(run_id)
        
        # メトリクス計算
        duration = self.calculate_duration(run.get('created_at'), run.get('updated_at'))
        billable = self.calculate_billable_minutes(jobs)
        total_cost = self.calculate_total_cost(billable)
        cache_hit_rate = self.calculate_cache_hit_rate(jobs)
        parallel_efficiency = self.calculate_parallel_efficiency(jobs)
        
        # ステップ数カウント
        total_steps = sum(len(job.get('steps', [])) for job in jobs)
        
        return WorkflowMetrics(
            workflow_id=run.get('workflow_id', 0),
            workflow_name=run.get('name', 'Unknown'),
            run_number=run.get('run_number', 0),
            status=run.get('status', 'unknown'),
            conclusion=run.get('conclusion'),
            created_at=run.get('created_at', ''),
            updated_at=run.get('updated_at', ''),
            run_duration_seconds=duration,
            billable_minutes=billable,
            total_cost_usd=total_cost,
            jobs_count=len(jobs),
            steps_count=total_steps,
            cache_hit_rate=cache_hit_rate,
            parallel_efficiency=parallel_efficiency,
            failure_rate=0  # 後で計算
        )
    
    def analyze_multiple_runs(self, runs: List[dict]) -> Dict:
        """複数のワークフロー実行を分析"""
        metrics_list = []
        
        for run in runs:
            try:
                metrics = self.analyze_workflow_run(run)
                metrics_list.append(metrics)
            except Exception as e:
                print(f"Error analyzing run {run.get('id')}: {e}", file=sys.stderr)
                continue
        
        if not metrics_list:
            return {}
        
        # 失敗率を計算
        failed_runs = sum(1 for m in metrics_list if m.conclusion == 'failure')
        failure_rate = (failed_runs / len(metrics_list) * 100) if metrics_list else 0
        
        for metric in metrics_list:
            metric.failure_rate = failure_rate
        
        # 統計情報を計算
        durations = [m.run_duration_seconds for m in metrics_list]
        costs = [m.total_cost_usd for m in metrics_list]
        cache_rates = [m.cache_hit_rate for m in metrics_list]
        parallel_rates = [m.parallel_efficiency for m in metrics_list]
        
        return {
            'summary': {
                'total_runs': len(metrics_list),
                'failed_runs': failed_runs,
                'failure_rate': round(failure_rate, 2),
                'avg_duration_seconds': round(statistics.mean(durations), 2),
                'median_duration_seconds': round(statistics.median(durations), 2),
                'total_cost_usd': round(sum(costs), 2),
                'avg_cost_usd': round(statistics.mean(costs), 4),
                'avg_cache_hit_rate': round(statistics.mean(cache_rates), 2),
                'avg_parallel_efficiency': round(statistics.mean(parallel_rates), 2),
            },
            'runs': [asdict(m) for m in metrics_list],
            'recommendations': self.generate_recommendations(metrics_list)
        }
    
    def generate_recommendations(self, metrics_list: List[WorkflowMetrics]) -> List[str]:
        """パフォーマンス改善の推奨事項を生成"""
        recommendations = []
        
        if not metrics_list:
            return recommendations
        
        # 平均値を計算
        avg_duration = statistics.mean(m.run_duration_seconds for m in metrics_list)
        avg_cache_hit = statistics.mean(m.cache_hit_rate for m in metrics_list)
        avg_parallel = statistics.mean(m.parallel_efficiency for m in metrics_list)
        avg_cost = statistics.mean(m.total_cost_usd for m in metrics_list)
        failure_rate = metrics_list[0].failure_rate if metrics_list else 0
        
        # 推奨事項の生成
        if avg_duration > 900:  # 15分以上
            recommendations.append(f"⚠️ 平均実行時間が{avg_duration/60:.1f}分と長いです。ジョブの並列化やキャッシュ活用を検討してください。")
        
        if avg_cache_hit < 70:
            recommendations.append(f"⚠️ キャッシュヒット率が{avg_cache_hit:.1f}%と低いです。キャッシュキーの最適化を検討してください。")
        
        if avg_parallel < 50:
            recommendations.append(f"⚠️ 並列実行効率が{avg_parallel:.1f}%と低いです。ジョブの依存関係を見直してください。")
        
        if avg_cost > 0.1:
            recommendations.append(f"💰 平均コストが${avg_cost:.3f}とやや高めです。Self-hosted Runnerの利用を検討してください。")
        
        if failure_rate > 10:
            recommendations.append(f"❌ 失敗率が{failure_rate:.1f}%と高いです。テストの安定性を改善してください。")
        
        # ポジティブなフィードバック
        if avg_cache_hit > 85:
            recommendations.append(f"✅ キャッシュヒット率{avg_cache_hit:.1f}%は優秀です！")
        
        if avg_parallel > 75:
            recommendations.append(f"✅ 並列実行効率{avg_parallel:.1f}%は良好です！")
        
        if avg_duration < 300:  # 5分未満
            recommendations.append(f"✅ 平均実行時間{avg_duration/60:.1f}分は高速です！")
        
        return recommendations

def generate_html_report(analysis_result: Dict, output_file: str):
    """HTML形式のレポートを生成"""
    html_template = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitHub Actions Performance Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #24292e; border-bottom: 2px solid #e1e4e8; padding-bottom: 10px; }}
        h2 {{ color: #586069; margin-top: 30px; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: #f6f8fa; padding: 15px; border-radius: 6px; border-left: 4px solid #0366d6; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #0366d6; }}
        .metric-label {{ color: #586069; font-size: 14px; margin-top: 5px; }}
        .recommendations {{ background: #fff8dc; padding: 15px; border-radius: 6px; margin: 20px 0; }}
        .recommendation-item {{ margin: 10px 0; padding-left: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #f6f8fa; padding: 10px; text-align: left; border-bottom: 2px solid #e1e4e8; }}
        td {{ padding: 10px; border-bottom: 1px solid #e1e4e8; }}
        tr:hover {{ background: #f6f8fa; }}
        .status-success {{ color: #28a745; }}
        .status-failure {{ color: #dc3545; }}
        .chart {{ margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 GitHub Actions Performance Report</h1>
        <p>Generated: {timestamp}</p>
        
        <h2>📊 Summary Metrics</h2>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{total_runs}</div>
                <div class="metric-label">Total Runs</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{avg_duration:.1f}min</div>
                <div class="metric-label">Avg Duration</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${total_cost:.2f}</div>
                <div class="metric-label">Total Cost</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{failure_rate:.1f}%</div>
                <div class="metric-label">Failure Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{cache_hit_rate:.1f}%</div>
                <div class="metric-label">Cache Hit Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{parallel_efficiency:.1f}%</div>
                <div class="metric-label">Parallel Efficiency</div>
            </div>
        </div>
        
        <h2>💡 Recommendations</h2>
        <div class="recommendations">
            {recommendations_html}
        </div>
        
        <h2>📈 Recent Workflow Runs</h2>
        <table>
            <thead>
                <tr>
                    <th>Workflow</th>
                    <th>Run #</th>
                    <th>Status</th>
                    <th>Duration</th>
                    <th>Cost</th>
                    <th>Jobs</th>
                    <th>Cache Hit</th>
                    <th>Parallel</th>
                </tr>
            </thead>
            <tbody>
                {runs_table_html}
            </tbody>
        </table>
    </div>
</body>
</html>
    """
    
    summary = analysis_result.get('summary', {})
    recommendations = analysis_result.get('recommendations', [])
    runs = analysis_result.get('runs', [])
    
    # 推奨事項のHTML生成
    recommendations_html = '\n'.join(
        f'<div class="recommendation-item">{rec}</div>'
        for rec in recommendations
    )
    
    # 実行履歴テーブルのHTML生成
    runs_table_html = ''
    for run in runs[:20]:  # 最新20件のみ表示
        status_class = 'status-success' if run['conclusion'] == 'success' else 'status-failure'
        runs_table_html += f"""
        <tr>
            <td>{run['workflow_name']}</td>
            <td>{run['run_number']}</td>
            <td class="{status_class}">{run['conclusion'] or run['status']}</td>
            <td>{run['run_duration_seconds']/60:.1f}min</td>
            <td>${run['total_cost_usd']:.3f}</td>
            <td>{run['jobs_count']}</td>
            <td>{run['cache_hit_rate']:.1f}%</td>
            <td>{run['parallel_efficiency']:.1f}%</td>
        </tr>
        """
    
    # HTMLファイル生成
    html_content = html_template.format(
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        total_runs=summary.get('total_runs', 0),
        avg_duration=summary.get('avg_duration_seconds', 0) / 60,
        total_cost=summary.get('total_cost_usd', 0),
        failure_rate=summary.get('failure_rate', 0),
        cache_hit_rate=summary.get('avg_cache_hit_rate', 0),
        parallel_efficiency=summary.get('avg_parallel_efficiency', 0),
        recommendations_html=recommendations_html,
        runs_table_html=runs_table_html
    )
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Report generated: {output_file}")

def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='GitHub Actions Performance Analyzer')
    parser.add_argument('--token', required=True, help='GitHub Personal Access Token')
    parser.add_argument('--owner', required=True, help='Repository owner')
    parser.add_argument('--repo', required=True, help='Repository name')
    parser.add_argument('--workflow-id', help='Specific workflow ID to analyze')
    parser.add_argument('--branch', help='Branch to analyze')
    parser.add_argument('--output', default='performance-report.html', help='Output file path')
    parser.add_argument('--json', action='store_true', help='Output JSON format')
    parser.add_argument('--limit', type=int, default=30, help='Number of runs to analyze')
    
    args = parser.parse_args()
    
    # 分析実行
    analyzer = GitHubActionsAnalyzer(args.token, args.owner, args.repo)
    
    print(f"🔍 Fetching workflow runs for {args.owner}/{args.repo}...")
    runs = analyzer.fetch_workflow_runs(
        workflow_id=args.workflow_id,
        branch=args.branch,
        per_page=args.limit
    )
    
    if not runs:
        print("No workflow runs found.")
        return
    
    print(f"📊 Analyzing {len(runs)} workflow runs...")
    analysis_result = analyzer.analyze_multiple_runs(runs)
    
    if args.json:
        # JSON出力
        output_file = args.output.replace('.html', '.json')
        with open(output_file, 'w') as f:
            json.dump(analysis_result, f, indent=2, default=str)
        print(f"✅ JSON report saved: {output_file}")
    else:
        # HTML出力
        generate_html_report(analysis_result, args.output)
    
    # サマリー表示
    summary = analysis_result.get('summary', {})
    print("\n📈 Performance Summary:")
    print(f"  Total Runs: {summary.get('total_runs', 0)}")
    print(f"  Average Duration: {summary.get('avg_duration_seconds', 0)/60:.1f} minutes")
    print(f"  Total Cost: ${summary.get('total_cost_usd', 0):.2f}")
    print(f"  Average Cost: ${summary.get('avg_cost_usd', 0):.4f}")
    print(f"  Failure Rate: {summary.get('failure_rate', 0):.1f}%")
    print(f"  Cache Hit Rate: {summary.get('avg_cache_hit_rate', 0):.1f}%")
    print(f"  Parallel Efficiency: {summary.get('avg_parallel_efficiency', 0):.1f}%")
    
    # 推奨事項表示
    recommendations = analysis_result.get('recommendations', [])
    if recommendations:
        print("\n💡 Recommendations:")
        for rec in recommendations:
            print(f"  {rec}")

if __name__ == '__main__':
    main()