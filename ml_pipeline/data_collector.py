"""
Data Collection Module for GitHub API
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import requests
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from ratelimit import limits, sleep_and_retry
import hashlib

from .config import Config

logger = logging.getLogger(__name__)


class GitHubDataCollector:
    """Collect and process data from GitHub API"""
    
    def __init__(self, config: Config):
        self.config = config
        self.headers = {
            "Authorization": f"token {config.GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    @sleep_and_retry
    @limits(calls=5000, period=3600)  # GitHub API rate limit
    def _api_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make rate-limited API request"""
        url = f"{self.config.GITHUB_API_BASE}{endpoint}"
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return {}
    
    def collect_repository_data(self, repo_name: str, days_back: int = 30) -> Dict[str, Any]:
        """Collect comprehensive repository data"""
        
        since_date = datetime.utcnow() - timedelta(days=days_back)
        repo_data = {
            "repository": repo_name,
            "collected_at": datetime.utcnow().isoformat(),
            "metadata": {},
            "commits": [],
            "pull_requests": [],
            "issues": [],
            "security_events": [],
            "workflows": [],
            "contributors": [],
            "branches": [],
            "tags": []
        }
        
        # Repository metadata
        repo_info = self._api_request(f"/repos/{self.config.GITHUB_ORG}/{repo_name}")
        repo_data["metadata"] = {
            "name": repo_info.get("name"),
            "description": repo_info.get("description"),
            "private": repo_info.get("private"),
            "created_at": repo_info.get("created_at"),
            "updated_at": repo_info.get("updated_at"),
            "size": repo_info.get("size"),
            "stars": repo_info.get("stargazers_count"),
            "forks": repo_info.get("forks_count"),
            "open_issues": repo_info.get("open_issues_count"),
            "language": repo_info.get("language"),
            "default_branch": repo_info.get("default_branch"),
            "has_wiki": repo_info.get("has_wiki"),
            "has_pages": repo_info.get("has_pages"),
            "archived": repo_info.get("archived")
        }
        
        # Collect commits
        commits = self._collect_commits(repo_name, since_date)
        repo_data["commits"] = commits
        
        # Collect pull requests
        prs = self._collect_pull_requests(repo_name, since_date)
        repo_data["pull_requests"] = prs
        
        # Collect issues
        issues = self._collect_issues(repo_name, since_date)
        repo_data["issues"] = issues
        
        # Collect security events
        security = self._collect_security_events(repo_name)
        repo_data["security_events"] = security
        
        # Collect workflow runs
        workflows = self._collect_workflow_runs(repo_name, since_date)
        repo_data["workflows"] = workflows
        
        # Collect contributor statistics
        contributors = self._collect_contributors(repo_name)
        repo_data["contributors"] = contributors
        
        # Collect branch protection rules
        branches = self._collect_branch_info(repo_name)
        repo_data["branches"] = branches
        
        return repo_data
    
    def _collect_commits(self, repo_name: str, since: datetime) -> List[Dict]:
        """Collect commit data"""
        commits = []
        page = 1
        
        while True:
            response = self._api_request(
                f"/repos/{self.config.GITHUB_ORG}/{repo_name}/commits",
                params={"since": since.isoformat(), "page": page, "per_page": 100}
            )
            
            if not response:
                break
                
            for commit in response:
                commit_data = {
                    "sha": commit.get("sha"),
                    "message": commit.get("commit", {}).get("message"),
                    "author": commit.get("commit", {}).get("author", {}).get("name"),
                    "author_email": commit.get("commit", {}).get("author", {}).get("email"),
                    "date": commit.get("commit", {}).get("author", {}).get("date"),
                    "committer": commit.get("commit", {}).get("committer", {}).get("name"),
                    "verified": commit.get("commit", {}).get("verification", {}).get("verified"),
                    "parents_count": len(commit.get("parents", [])),
                    "additions": 0,
                    "deletions": 0,
                    "files_changed": 0
                }
                
                # Get detailed commit info
                detail = self._api_request(
                    f"/repos/{self.config.GITHUB_ORG}/{repo_name}/commits/{commit['sha']}"
                )
                if detail:
                    commit_data["additions"] = detail.get("stats", {}).get("additions", 0)
                    commit_data["deletions"] = detail.get("stats", {}).get("deletions", 0)
                    commit_data["files_changed"] = len(detail.get("files", []))
                
                commits.append(commit_data)
            
            if len(response) < 100:
                break
            page += 1
        
        return commits
    
    def _collect_pull_requests(self, repo_name: str, since: datetime) -> List[Dict]:
        """Collect pull request data"""
        prs = []
        
        for state in ["open", "closed"]:
            page = 1
            while True:
                response = self._api_request(
                    f"/repos/{self.config.GITHUB_ORG}/{repo_name}/pulls",
                    params={"state": state, "page": page, "per_page": 100}
                )
                
                if not response:
                    break
                
                for pr in response:
                    created_at = datetime.fromisoformat(pr.get("created_at").replace("Z", "+00:00"))
                    if created_at < since:
                        continue
                    
                    pr_data = {
                        "number": pr.get("number"),
                        "title": pr.get("title"),
                        "state": pr.get("state"),
                        "created_at": pr.get("created_at"),
                        "updated_at": pr.get("updated_at"),
                        "closed_at": pr.get("closed_at"),
                        "merged_at": pr.get("merged_at"),
                        "author": pr.get("user", {}).get("login"),
                        "base_branch": pr.get("base", {}).get("ref"),
                        "head_branch": pr.get("head", {}).get("ref"),
                        "additions": pr.get("additions", 0),
                        "deletions": pr.get("deletions", 0),
                        "changed_files": pr.get("changed_files", 0),
                        "commits": pr.get("commits", 0),
                        "review_comments": pr.get("review_comments", 0),
                        "comments": pr.get("comments", 0),
                        "mergeable": pr.get("mergeable"),
                        "draft": pr.get("draft", False)
                    }
                    
                    # Get reviews
                    reviews = self._api_request(
                        f"/repos/{self.config.GITHUB_ORG}/{repo_name}/pulls/{pr['number']}/reviews"
                    )
                    pr_data["reviews"] = len(reviews) if reviews else 0
                    pr_data["approved"] = any(r.get("state") == "APPROVED" for r in (reviews or []))
                    
                    prs.append(pr_data)
                
                if len(response) < 100:
                    break
                page += 1
        
        return prs
    
    def _collect_issues(self, repo_name: str, since: datetime) -> List[Dict]:
        """Collect issue data"""
        issues = []
        
        for state in ["open", "closed"]:
            page = 1
            while True:
                response = self._api_request(
                    f"/repos/{self.config.GITHUB_ORG}/{repo_name}/issues",
                    params={"state": state, "since": since.isoformat(), "page": page, "per_page": 100}
                )
                
                if not response:
                    break
                
                for issue in response:
                    # Skip pull requests (they appear in issues endpoint too)
                    if "pull_request" in issue:
                        continue
                    
                    issue_data = {
                        "number": issue.get("number"),
                        "title": issue.get("title"),
                        "state": issue.get("state"),
                        "created_at": issue.get("created_at"),
                        "updated_at": issue.get("updated_at"),
                        "closed_at": issue.get("closed_at"),
                        "author": issue.get("user", {}).get("login"),
                        "assignees": [a.get("login") for a in issue.get("assignees", [])],
                        "labels": [l.get("name") for l in issue.get("labels", [])],
                        "comments": issue.get("comments", 0),
                        "body_length": len(issue.get("body", "")),
                        "is_security": any("security" in l.get("name", "").lower() 
                                         for l in issue.get("labels", []))
                    }
                    issues.append(issue_data)
                
                if len(response) < 100:
                    break
                page += 1
        
        return issues
    
    def _collect_security_events(self, repo_name: str) -> List[Dict]:
        """Collect security-related events"""
        security_data = []
        
        # Vulnerability alerts
        vulns = self._api_request(
            f"/repos/{self.config.GITHUB_ORG}/{repo_name}/vulnerability-alerts"
        )
        
        # Dependabot alerts
        dependabot = self._api_request(
            f"/repos/{self.config.GITHUB_ORG}/{repo_name}/dependabot/alerts"
        )
        
        if isinstance(dependabot, list):
            for alert in dependabot:
                security_data.append({
                    "type": "dependabot",
                    "severity": alert.get("security_advisory", {}).get("severity"),
                    "state": alert.get("state"),
                    "created_at": alert.get("created_at"),
                    "fixed_at": alert.get("fixed_at"),
                    "package": alert.get("dependency", {}).get("package", {}).get("name"),
                    "vulnerable_version": alert.get("dependency", {}).get("manifest_path")
                })
        
        # Code scanning alerts
        code_scanning = self._api_request(
            f"/repos/{self.config.GITHUB_ORG}/{repo_name}/code-scanning/alerts"
        )
        
        if isinstance(code_scanning, list):
            for alert in code_scanning:
                security_data.append({
                    "type": "code_scanning",
                    "severity": alert.get("rule", {}).get("severity"),
                    "state": alert.get("state"),
                    "created_at": alert.get("created_at"),
                    "fixed_at": alert.get("fixed_at"),
                    "tool": alert.get("tool", {}).get("name"),
                    "rule": alert.get("rule", {}).get("description")
                })
        
        # Secret scanning alerts
        secret_scanning = self._api_request(
            f"/repos/{self.config.GITHUB_ORG}/{repo_name}/secret-scanning/alerts"
        )
        
        if isinstance(secret_scanning, list):
            for alert in secret_scanning:
                security_data.append({
                    "type": "secret_scanning",
                    "severity": "critical",  # Secrets are always critical
                    "state": alert.get("state"),
                    "created_at": alert.get("created_at"),
                    "resolved_at": alert.get("resolved_at"),
                    "secret_type": alert.get("secret_type"),
                    "resolution": alert.get("resolution")
                })
        
        return security_data
    
    def _collect_workflow_runs(self, repo_name: str, since: datetime) -> List[Dict]:
        """Collect GitHub Actions workflow runs"""
        workflows = []
        
        response = self._api_request(
            f"/repos/{self.config.GITHUB_ORG}/{repo_name}/actions/runs",
            params={"created": f">={since.isoformat()}"}
        )
        
        if response and "workflow_runs" in response:
            for run in response["workflow_runs"]:
                workflow_data = {
                    "id": run.get("id"),
                    "name": run.get("name"),
                    "status": run.get("status"),
                    "conclusion": run.get("conclusion"),
                    "created_at": run.get("created_at"),
                    "updated_at": run.get("updated_at"),
                    "run_number": run.get("run_number"),
                    "event": run.get("event"),
                    "branch": run.get("head_branch"),
                    "duration_seconds": 0
                }
                
                # Calculate duration
                if run.get("created_at") and run.get("updated_at"):
                    created = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
                    updated = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
                    workflow_data["duration_seconds"] = (updated - created).total_seconds()
                
                workflows.append(workflow_data)
        
        return workflows
    
    def _collect_contributors(self, repo_name: str) -> List[Dict]:
        """Collect contributor statistics"""
        contributors = []
        
        response = self._api_request(
            f"/repos/{self.config.GITHUB_ORG}/{repo_name}/contributors"
        )
        
        if response:
            for contributor in response[:50]:  # Top 50 contributors
                contrib_data = {
                    "login": contributor.get("login"),
                    "contributions": contributor.get("contributions"),
                    "type": contributor.get("type")
                }
                
                # Get user details
                user_detail = self._api_request(f"/users/{contributor['login']}")
                if user_detail:
                    contrib_data["name"] = user_detail.get("name")
                    contrib_data["company"] = user_detail.get("company")
                    contrib_data["created_at"] = user_detail.get("created_at")
                
                contributors.append(contrib_data)
        
        return contributors
    
    def _collect_branch_info(self, repo_name: str) -> List[Dict]:
        """Collect branch information and protection rules"""
        branches = []
        
        response = self._api_request(
            f"/repos/{self.config.GITHUB_ORG}/{repo_name}/branches"
        )
        
        if response:
            for branch in response:
                branch_data = {
                    "name": branch.get("name"),
                    "protected": branch.get("protected"),
                    "protection_rules": {}
                }
                
                # Get protection rules if protected
                if branch.get("protected"):
                    protection = self._api_request(
                        f"/repos/{self.config.GITHUB_ORG}/{repo_name}/branches/{branch['name']}/protection"
                    )
                    if protection:
                        branch_data["protection_rules"] = {
                            "required_reviews": protection.get("required_pull_request_reviews", {}).get("required_approving_review_count", 0),
                            "dismiss_stale_reviews": protection.get("required_pull_request_reviews", {}).get("dismiss_stale_reviews", False),
                            "require_code_owner_reviews": protection.get("required_pull_request_reviews", {}).get("require_code_owner_reviews", False),
                            "required_status_checks": bool(protection.get("required_status_checks")),
                            "enforce_admins": protection.get("enforce_admins", {}).get("enabled", False),
                            "require_signed_commits": protection.get("required_signatures", {}).get("enabled", False)
                        }
                
                branches.append(branch_data)
        
        return branches
    
    def collect_organization_data(self, days_back: int = 30) -> pd.DataFrame:
        """Collect data for all repositories in the organization"""
        all_data = []
        
        # Get all repositories
        repos = self._api_request(f"/orgs/{self.config.GITHUB_ORG}/repos")
        
        if not repos:
            logger.error("Failed to fetch organization repositories")
            return pd.DataFrame()
        
        # Collect data in parallel
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self.collect_repository_data, repo["name"], days_back): repo["name"]
                for repo in repos
            }
            
            for future in as_completed(futures):
                repo_name = futures[future]
                try:
                    data = future.result()
                    all_data.append(data)
                    logger.info(f"Collected data for {repo_name}")
                except Exception as e:
                    logger.error(f"Failed to collect data for {repo_name}: {e}")
        
        # Convert to DataFrame
        df = pd.json_normalize(all_data)
        return df
    
    def save_raw_data(self, data: Dict, filename: str):
        """Save raw collected data to file"""
        filepath = f"{self.config.FEATURE_STORE_PATH}/raw/{filename}"
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"Saved raw data to {filepath}")
    
    def load_raw_data(self, filename: str) -> Dict:
        """Load raw data from file"""
        filepath = f"{self.config.FEATURE_STORE_PATH}/raw/{filename}"
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data