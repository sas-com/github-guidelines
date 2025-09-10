"""
Feature Engineering Module for ML Pipeline
"""

import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.decomposition import PCA
import hashlib
from scipy import stats

from .config import Config

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Advanced feature engineering for GitHub data"""
    
    def __init__(self, config: Config):
        self.config = config
        self.text_vectorizer = TfidfVectorizer(
            max_features=config.TEXT_MAX_FEATURES,
            min_df=config.MIN_WORD_FREQUENCY,
            ngram_range=(1, 3)
        )
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_importance = {}
        
    def engineer_features(self, raw_data: Dict[str, Any]) -> pd.DataFrame:
        """Main feature engineering pipeline"""
        
        features = pd.DataFrame()
        
        # Repository-level features
        repo_features = self._extract_repository_features(raw_data)
        features = pd.concat([features, repo_features], axis=1)
        
        # Commit-based features
        commit_features = self._extract_commit_features(raw_data.get("commits", []))
        features = pd.concat([features, commit_features], axis=1)
        
        # Pull request features
        pr_features = self._extract_pr_features(raw_data.get("pull_requests", []))
        features = pd.concat([features, pr_features], axis=1)
        
        # Issue tracking features
        issue_features = self._extract_issue_features(raw_data.get("issues", []))
        features = pd.concat([features, issue_features], axis=1)
        
        # Security features
        security_features = self._extract_security_features(raw_data.get("security_events", []))
        features = pd.concat([features, security_features], axis=1)
        
        # CI/CD features
        cicd_features = self._extract_cicd_features(raw_data.get("workflows", []))
        features = pd.concat([features, cicd_features], axis=1)
        
        # Developer behavior features
        dev_features = self._extract_developer_features(raw_data)
        features = pd.concat([features, dev_features], axis=1)
        
        # DORA metrics
        dora_features = self._calculate_dora_metrics(raw_data)
        features = pd.concat([features, dora_features], axis=1)
        
        # Time series features
        time_features = self._extract_time_series_features(raw_data)
        features = pd.concat([features, time_features], axis=1)
        
        # Text analysis features
        text_features = self._extract_text_features(raw_data)
        features = pd.concat([features, text_features], axis=1)
        
        # Compliance features
        compliance_features = self._extract_compliance_features(raw_data)
        features = pd.concat([features, compliance_features], axis=1)
        
        return features
    
    def _extract_repository_features(self, data: Dict) -> pd.DataFrame:
        """Extract repository-level features"""
        
        metadata = data.get("metadata", {})
        
        features = {
            # Basic metrics
            "repo_age_days": self._calculate_age_days(metadata.get("created_at")),
            "repo_size_mb": metadata.get("size", 0) / 1024,
            "repo_stars": metadata.get("stars", 0),
            "repo_forks": metadata.get("forks", 0),
            "repo_open_issues": metadata.get("open_issues", 0),
            "repo_is_private": int(metadata.get("private", False)),
            "repo_is_archived": int(metadata.get("archived", False)),
            
            # Activity indicators
            "days_since_last_update": self._calculate_age_days(metadata.get("updated_at")),
            "has_wiki": int(metadata.get("has_wiki", False)),
            "has_pages": int(metadata.get("has_pages", False)),
            
            # Language features
            "primary_language": metadata.get("language", "unknown"),
            "is_javascript": int(metadata.get("language") == "JavaScript"),
            "is_python": int(metadata.get("language") == "Python"),
            "is_java": int(metadata.get("language") == "Java"),
            
            # Branch protection
            "default_branch_protected": 0,  # Will be updated from branch data
            "num_protected_branches": 0,
            "avg_review_requirement": 0
        }
        
        # Update branch protection features
        branches = data.get("branches", [])
        protected_branches = [b for b in branches if b.get("protected")]
        features["num_protected_branches"] = len(protected_branches)
        
        if branches:
            default_branch = metadata.get("default_branch", "main")
            for branch in branches:
                if branch.get("name") == default_branch:
                    features["default_branch_protected"] = int(branch.get("protected", False))
                    
            # Average review requirements
            review_requirements = [
                b.get("protection_rules", {}).get("required_reviews", 0)
                for b in protected_branches
                if b.get("protection_rules")
            ]
            if review_requirements:
                features["avg_review_requirement"] = np.mean(review_requirements)
        
        return pd.DataFrame([features])
    
    def _extract_commit_features(self, commits: List[Dict]) -> pd.DataFrame:
        """Extract commit-based features"""
        
        if not commits:
            return pd.DataFrame([{
                "num_commits": 0,
                "avg_commits_per_day": 0,
                "commit_message_avg_length": 0,
                "commit_message_compliance_rate": 0,
                "percent_verified_commits": 0,
                "avg_files_per_commit": 0,
                "avg_additions_per_commit": 0,
                "avg_deletions_per_commit": 0,
                "commit_size_variance": 0,
                "merge_commit_ratio": 0,
                "commit_hour_entropy": 0,
                "weekend_commit_ratio": 0,
                "force_push_indicators": 0
            }])
        
        df = pd.DataFrame(commits)
        
        # Convert dates
        df['date'] = pd.to_datetime(df['date'])
        
        # Basic statistics
        features = {
            "num_commits": len(commits),
            "unique_authors": df['author'].nunique(),
            "unique_committers": df['committer'].nunique(),
            
            # Commit frequency
            "avg_commits_per_day": len(commits) / max(1, (df['date'].max() - df['date'].min()).days),
            "max_commits_single_day": df.groupby(df['date'].dt.date).size().max(),
            
            # Commit message analysis
            "commit_message_avg_length": df['message'].str.len().mean(),
            "commit_message_min_length": df['message'].str.len().min(),
            "commit_message_max_length": df['message'].str.len().max(),
            
            # Compliance checking
            "commit_message_compliance_rate": self._check_commit_message_compliance(df['message'].tolist()),
            "percent_conventional_commits": self._check_conventional_commits(df['message'].tolist()),
            
            # Security
            "percent_verified_commits": df['verified'].mean() * 100,
            "unverified_commit_count": (~df['verified']).sum(),
            
            # Change metrics
            "avg_files_per_commit": df['files_changed'].mean(),
            "avg_additions_per_commit": df['additions'].mean(),
            "avg_deletions_per_commit": df['deletions'].mean(),
            "total_lines_changed": df['additions'].sum() + df['deletions'].sum(),
            "code_churn": df['deletions'].sum() / max(1, df['additions'].sum()),
            
            # Commit patterns
            "commit_size_variance": df['additions'].var(),
            "merge_commit_ratio": (df['parents_count'] > 1).mean(),
            "single_parent_ratio": (df['parents_count'] == 1).mean(),
            
            # Time-based patterns
            "commit_hour_entropy": self._calculate_entropy(df['date'].dt.hour.value_counts()),
            "weekend_commit_ratio": df['date'].dt.dayofweek.isin([5, 6]).mean(),
            "night_commit_ratio": df['date'].dt.hour.between(22, 6).mean(),
            
            # Potential issues
            "force_push_indicators": self._detect_force_push_patterns(commits),
            "large_commit_count": (df['files_changed'] > 50).sum(),
            "empty_message_count": (df['message'].str.strip() == "").sum()
        }
        
        return pd.DataFrame([features])
    
    def _extract_pr_features(self, pull_requests: List[Dict]) -> pd.DataFrame:
        """Extract pull request features"""
        
        if not pull_requests:
            return pd.DataFrame([{
                "num_prs": 0,
                "pr_merge_rate": 0,
                "avg_pr_lifetime_hours": 0,
                "avg_pr_size": 0,
                "avg_review_count": 0,
                "pr_approval_rate": 0,
                "draft_pr_ratio": 0,
                "pr_rejection_rate": 0
            }])
        
        df = pd.DataFrame(pull_requests)
        
        # Convert dates
        date_cols = ['created_at', 'updated_at', 'closed_at', 'merged_at']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
        
        # Calculate PR lifetime
        df['lifetime_hours'] = (df['closed_at'] - df['created_at']).dt.total_seconds() / 3600
        df['lifetime_hours'] = df['lifetime_hours'].fillna(
            (datetime.utcnow() - df['created_at']).dt.total_seconds() / 3600
        )
        
        features = {
            "num_prs": len(pull_requests),
            "num_open_prs": (df['state'] == 'open').sum(),
            "num_closed_prs": (df['state'] == 'closed').sum(),
            
            # Merge metrics
            "pr_merge_rate": df['merged_at'].notna().mean(),
            "pr_rejection_rate": ((df['state'] == 'closed') & df['merged_at'].isna()).mean(),
            
            # Time metrics
            "avg_pr_lifetime_hours": df['lifetime_hours'].mean(),
            "median_pr_lifetime_hours": df['lifetime_hours'].median(),
            "max_pr_lifetime_hours": df['lifetime_hours'].max(),
            "pr_lifetime_variance": df['lifetime_hours'].var(),
            
            # Size metrics
            "avg_pr_size": df['additions'].add(df['deletions']).mean(),
            "avg_pr_files": df['changed_files'].mean(),
            "avg_pr_commits": df['commits'].mean(),
            "large_pr_count": ((df['additions'] + df['deletions']) > 500).sum(),
            
            # Review metrics
            "avg_review_count": df['reviews'].mean(),
            "avg_review_comments": df['review_comments'].mean(),
            "avg_comments": df['comments'].mean(),
            "pr_approval_rate": df['approved'].mean(),
            "no_review_pr_count": (df['reviews'] == 0).sum(),
            
            # PR patterns
            "draft_pr_ratio": df['draft'].mean(),
            "unmergeable_pr_count": (df['mergeable'] == False).sum(),
            "pr_to_main_ratio": (df['base_branch'] == 'main').mean(),
            
            # Author diversity
            "unique_pr_authors": df['author'].nunique(),
            "pr_author_concentration": 1 - (df['author'].nunique() / len(df))
        }
        
        return pd.DataFrame([features])
    
    def _extract_issue_features(self, issues: List[Dict]) -> pd.DataFrame:
        """Extract issue tracking features"""
        
        if not issues:
            return pd.DataFrame([{
                "num_issues": 0,
                "open_issue_ratio": 0,
                "avg_issue_resolution_hours": 0,
                "security_issue_count": 0,
                "avg_issue_comments": 0
            }])
        
        df = pd.DataFrame(issues)
        
        # Convert dates
        date_cols = ['created_at', 'updated_at', 'closed_at']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
        
        # Calculate resolution time
        df['resolution_hours'] = (df['closed_at'] - df['created_at']).dt.total_seconds() / 3600
        
        features = {
            "num_issues": len(issues),
            "num_open_issues": (df['state'] == 'open').sum(),
            "open_issue_ratio": (df['state'] == 'open').mean(),
            
            # Resolution metrics
            "avg_issue_resolution_hours": df['resolution_hours'].mean(),
            "median_issue_resolution_hours": df['resolution_hours'].median(),
            "unresolved_old_issues": ((df['state'] == 'open') & 
                                     ((datetime.utcnow() - df['created_at']).dt.days > 30)).sum(),
            
            # Issue characteristics
            "security_issue_count": df['is_security'].sum(),
            "security_issue_ratio": df['is_security'].mean(),
            "avg_issue_comments": df['comments'].mean(),
            "avg_issue_body_length": df['body_length'].mean(),
            
            # Assignment patterns
            "unassigned_issue_ratio": df['assignees'].apply(lambda x: len(x) == 0).mean(),
            "multi_assignee_ratio": df['assignees'].apply(lambda x: len(x) > 1).mean(),
            
            # Label analysis
            "avg_labels_per_issue": df['labels'].apply(len).mean(),
            "unlabeled_issue_ratio": df['labels'].apply(lambda x: len(x) == 0).mean()
        }
        
        return pd.DataFrame([features])
    
    def _extract_security_features(self, security_events: List[Dict]) -> pd.DataFrame:
        """Extract security-related features"""
        
        if not security_events:
            return pd.DataFrame([{
                "total_security_alerts": 0,
                "critical_security_alerts": 0,
                "open_security_alerts": 0,
                "avg_security_resolution_hours": 0,
                "has_dependabot_alerts": 0,
                "has_code_scanning_alerts": 0,
                "has_secret_scanning_alerts": 0
            }])
        
        df = pd.DataFrame(security_events)
        
        # Convert dates
        date_cols = ['created_at', 'fixed_at', 'resolved_at']
        for col in date_cols:
            if col in df.columns and col in df:
                df[col] = pd.to_datetime(df[col])
        
        # Calculate resolution time
        if 'fixed_at' in df.columns:
            df['resolution_hours'] = (df['fixed_at'] - df['created_at']).dt.total_seconds() / 3600
        elif 'resolved_at' in df.columns:
            df['resolution_hours'] = (df['resolved_at'] - df['created_at']).dt.total_seconds() / 3600
        else:
            df['resolution_hours'] = np.nan
        
        features = {
            "total_security_alerts": len(security_events),
            
            # Severity breakdown
            "critical_security_alerts": (df['severity'] == 'critical').sum() if 'severity' in df else 0,
            "high_security_alerts": (df['severity'] == 'high').sum() if 'severity' in df else 0,
            "medium_security_alerts": (df['severity'] == 'medium').sum() if 'severity' in df else 0,
            "low_security_alerts": (df['severity'] == 'low').sum() if 'severity' in df else 0,
            
            # Alert status
            "open_security_alerts": (df['state'].isin(['open', 'active'])).sum() if 'state' in df else 0,
            "dismissed_security_alerts": (df['state'] == 'dismissed').sum() if 'state' in df else 0,
            
            # Resolution metrics
            "avg_security_resolution_hours": df['resolution_hours'].mean() if 'resolution_hours' in df else 0,
            "max_security_resolution_hours": df['resolution_hours'].max() if 'resolution_hours' in df else 0,
            
            # Alert types
            "has_dependabot_alerts": int((df['type'] == 'dependabot').any()) if 'type' in df else 0,
            "has_code_scanning_alerts": int((df['type'] == 'code_scanning').any()) if 'type' in df else 0,
            "has_secret_scanning_alerts": int((df['type'] == 'secret_scanning').any()) if 'type' in df else 0,
            
            # Specific counts
            "dependabot_alert_count": (df['type'] == 'dependabot').sum() if 'type' in df else 0,
            "code_scanning_alert_count": (df['type'] == 'code_scanning').sum() if 'type' in df else 0,
            "secret_scanning_alert_count": (df['type'] == 'secret_scanning').sum() if 'type' in df else 0
        }
        
        return pd.DataFrame([features])
    
    def _extract_cicd_features(self, workflows: List[Dict]) -> pd.DataFrame:
        """Extract CI/CD pipeline features"""
        
        if not workflows:
            return pd.DataFrame([{
                "total_workflow_runs": 0,
                "workflow_success_rate": 0,
                "avg_workflow_duration": 0,
                "failed_workflow_count": 0
            }])
        
        df = pd.DataFrame(workflows)
        
        features = {
            "total_workflow_runs": len(workflows),
            
            # Success metrics
            "workflow_success_rate": (df['conclusion'] == 'success').mean() if 'conclusion' in df else 0,
            "workflow_failure_rate": (df['conclusion'] == 'failure').mean() if 'conclusion' in df else 0,
            "workflow_cancelled_rate": (df['conclusion'] == 'cancelled').mean() if 'conclusion' in df else 0,
            
            # Counts by status
            "successful_workflow_count": (df['conclusion'] == 'success').sum() if 'conclusion' in df else 0,
            "failed_workflow_count": (df['conclusion'] == 'failure').sum() if 'conclusion' in df else 0,
            "cancelled_workflow_count": (df['conclusion'] == 'cancelled').sum() if 'conclusion' in df else 0,
            
            # Duration metrics
            "avg_workflow_duration": df['duration_seconds'].mean() if 'duration_seconds' in df else 0,
            "median_workflow_duration": df['duration_seconds'].median() if 'duration_seconds' in df else 0,
            "max_workflow_duration": df['duration_seconds'].max() if 'duration_seconds' in df else 0,
            
            # Event triggers
            "push_triggered_runs": (df['event'] == 'push').sum() if 'event' in df else 0,
            "pr_triggered_runs": (df['event'] == 'pull_request').sum() if 'event' in df else 0,
            "schedule_triggered_runs": (df['event'] == 'schedule').sum() if 'event' in df else 0,
            
            # Branch analysis
            "main_branch_runs": (df['branch'] == 'main').sum() if 'branch' in df else 0,
            "feature_branch_runs": (~df['branch'].isin(['main', 'master', 'develop'])).sum() if 'branch' in df else 0
        }
        
        return pd.DataFrame([features])
    
    def _extract_developer_features(self, data: Dict) -> pd.DataFrame:
        """Extract developer behavior features"""
        
        commits = data.get("commits", [])
        prs = data.get("pull_requests", [])
        contributors = data.get("contributors", [])
        
        features = {
            "total_contributors": len(contributors),
            "top_contributor_concentration": 0,
            "new_contributor_ratio": 0,
            "avg_contributions_per_dev": 0,
            "bus_factor": 0  # Number of key developers
        }
        
        if contributors:
            df_contrib = pd.DataFrame(contributors)
            total_contributions = df_contrib['contributions'].sum()
            
            # Concentration metrics
            top_5_contributions = df_contrib.nlargest(5, 'contributions')['contributions'].sum()
            features["top_contributor_concentration"] = top_5_contributions / total_contributions
            
            # Average contributions
            features["avg_contributions_per_dev"] = df_contrib['contributions'].mean()
            
            # Bus factor (developers with >10% contributions)
            features["bus_factor"] = (df_contrib['contributions'] / total_contributions > 0.1).sum()
            
            # New contributors (joined in last 90 days)
            if 'created_at' in df_contrib.columns:
                df_contrib['created_at'] = pd.to_datetime(df_contrib['created_at'])
                new_cutoff = datetime.utcnow() - timedelta(days=90)
                features["new_contributor_ratio"] = (df_contrib['created_at'] > new_cutoff).mean()
        
        # Developer patterns from commits
        if commits:
            df_commits = pd.DataFrame(commits)
            
            # Work patterns
            features["unique_commit_authors"] = df_commits['author'].nunique()
            features["commits_per_author"] = len(commits) / max(1, df_commits['author'].nunique())
            
            # Email domain analysis
            if 'author_email' in df_commits.columns:
                domains = df_commits['author_email'].str.extract(r'@(.+)$')[0]
                features["unique_email_domains"] = domains.nunique()
                features["external_contributor_ratio"] = (~domains.str.contains('sas-com', na=False)).mean()
        
        # PR author patterns
        if prs:
            df_prs = pd.DataFrame(prs)
            features["unique_pr_authors"] = df_prs['author'].nunique()
            features["prs_per_author"] = len(prs) / max(1, df_prs['author'].nunique())
        
        return pd.DataFrame([features])
    
    def _calculate_dora_metrics(self, data: Dict) -> pd.DataFrame:
        """Calculate DORA (DevOps Research and Assessment) metrics"""
        
        features = {
            "deployment_frequency": 0,
            "lead_time_hours": 0,
            "mttr_hours": 0,  # Mean Time To Recovery
            "change_failure_rate": 0
        }
        
        workflows = data.get("workflows", [])
        commits = data.get("commits", [])
        issues = data.get("issues", [])
        
        if workflows:
            df_workflows = pd.DataFrame(workflows)
            
            # Deployment frequency (successful deployments per day)
            if 'created_at' in df_workflows.columns:
                df_workflows['created_at'] = pd.to_datetime(df_workflows['created_at'])
                days_range = (df_workflows['created_at'].max() - df_workflows['created_at'].min()).days
                if days_range > 0:
                    successful_deployments = (df_workflows['conclusion'] == 'success').sum()
                    features["deployment_frequency"] = successful_deployments / days_range
            
            # Change failure rate
            total_deployments = len(df_workflows)
            failed_deployments = (df_workflows['conclusion'] == 'failure').sum()
            if total_deployments > 0:
                features["change_failure_rate"] = failed_deployments / total_deployments
        
        # Lead time (from commit to deployment)
        if commits and workflows:
            # Simplified: average time from commit to next successful workflow
            features["lead_time_hours"] = 24  # Placeholder - would need more sophisticated matching
        
        # MTTR (from incident detection to resolution)
        if issues:
            df_issues = pd.DataFrame(issues)
            incident_issues = df_issues[df_issues['labels'].apply(
                lambda x: any('incident' in label.lower() for label in x) if x else False
            )]
            
            if not incident_issues.empty:
                incident_issues['created_at'] = pd.to_datetime(incident_issues['created_at'])
                incident_issues['closed_at'] = pd.to_datetime(incident_issues['closed_at'])
                resolution_times = (incident_issues['closed_at'] - incident_issues['created_at']).dt.total_seconds() / 3600
                features["mttr_hours"] = resolution_times.mean()
        
        # Evaluate against targets
        for metric, value in features.items():
            if metric in self.config.DORA_TARGETS:
                targets = self.config.DORA_TARGETS[metric]
                if value <= targets["excellent"]:
                    features[f"{metric}_score"] = 3
                elif value <= targets["good"]:
                    features[f"{metric}_score"] = 2
                elif value <= targets["needs_improvement"]:
                    features[f"{metric}_score"] = 1
                else:
                    features[f"{metric}_score"] = 0
        
        return pd.DataFrame([features])
    
    def _extract_time_series_features(self, data: Dict) -> pd.DataFrame:
        """Extract time series features for trend analysis"""
        
        features = {}
        
        # Commit trends
        commits = data.get("commits", [])
        if commits:
            df_commits = pd.DataFrame(commits)
            df_commits['date'] = pd.to_datetime(df_commits['date'])
            df_commits['day'] = df_commits['date'].dt.date
            
            daily_commits = df_commits.groupby('day').size()
            
            features["commit_trend_slope"] = self._calculate_trend(daily_commits)
            features["commit_volatility"] = daily_commits.std()
            features["commit_autocorrelation"] = self._calculate_autocorrelation(daily_commits)
            
            # Weekly patterns
            df_commits['week'] = df_commits['date'].dt.isocalendar().week
            weekly_commits = df_commits.groupby('week').size()
            features["weekly_commit_trend"] = self._calculate_trend(weekly_commits)
        
        # PR trends
        prs = data.get("pull_requests", [])
        if prs:
            df_prs = pd.DataFrame(prs)
            df_prs['created_at'] = pd.to_datetime(df_prs['created_at'])
            df_prs['day'] = df_prs['created_at'].dt.date
            
            daily_prs = df_prs.groupby('day').size()
            features["pr_trend_slope"] = self._calculate_trend(daily_prs)
            features["pr_creation_volatility"] = daily_prs.std()
        
        # Issue trends
        issues = data.get("issues", [])
        if issues:
            df_issues = pd.DataFrame(issues)
            df_issues['created_at'] = pd.to_datetime(df_issues['created_at'])
            df_issues['day'] = df_issues['created_at'].dt.date
            
            daily_issues = df_issues.groupby('day').size()
            features["issue_trend_slope"] = self._calculate_trend(daily_issues)
            features["issue_creation_volatility"] = daily_issues.std()
            
            # Open issues over time
            open_issues = df_issues[df_issues['state'] == 'open']
            if not open_issues.empty:
                features["open_issue_growth_rate"] = len(open_issues) / max(1, len(df_issues))
        
        return pd.DataFrame([features])
    
    def _extract_text_features(self, data: Dict) -> pd.DataFrame:
        """Extract features from text data using NLP"""
        
        features = {}
        
        # Combine all text data
        text_data = []
        
        # Commit messages
        commits = data.get("commits", [])
        if commits:
            text_data.extend([c.get("message", "") for c in commits])
        
        # PR titles and descriptions
        prs = data.get("pull_requests", [])
        if prs:
            text_data.extend([pr.get("title", "") for pr in prs])
        
        # Issue titles
        issues = data.get("issues", [])
        if issues:
            text_data.extend([issue.get("title", "") for issue in issues])
        
        if text_data:
            # Basic text statistics
            text_lengths = [len(text) for text in text_data]
            features["avg_text_length"] = np.mean(text_lengths)
            features["text_length_variance"] = np.var(text_lengths)
            
            # Sentiment indicators (simplified)
            positive_words = ["fix", "improve", "enhance", "add", "feature", "implement"]
            negative_words = ["bug", "error", "fail", "break", "issue", "problem"]
            
            positive_count = sum(1 for text in text_data for word in positive_words if word in text.lower())
            negative_count = sum(1 for text in text_data for word in negative_words if word in text.lower())
            
            features["positive_sentiment_ratio"] = positive_count / max(1, len(text_data))
            features["negative_sentiment_ratio"] = negative_count / max(1, len(text_data))
            
            # Security-related text
            security_keywords = ["security", "vulnerability", "cve", "exploit", "injection", "xss", "csrf"]
            security_mentions = sum(1 for text in text_data for keyword in security_keywords if keyword in text.lower())
            features["security_mention_ratio"] = security_mentions / max(1, len(text_data))
            
            # Urgency indicators
            urgency_keywords = ["urgent", "critical", "asap", "emergency", "immediately", "hotfix"]
            urgency_mentions = sum(1 for text in text_data for keyword in urgency_keywords if keyword in text.lower())
            features["urgency_indicator_ratio"] = urgency_mentions / max(1, len(text_data))
        
        return pd.DataFrame([features])
    
    def _extract_compliance_features(self, data: Dict) -> pd.DataFrame:
        """Extract compliance and guideline adherence features"""
        
        features = {
            "branch_protection_compliance": 0,
            "commit_signing_compliance": 0,
            "pr_review_compliance": 0,
            "security_scanning_enabled": 0,
            "documentation_compliance": 0,
            "test_coverage_indicator": 0
        }
        
        # Branch protection compliance
        branches = data.get("branches", [])
        if branches:
            protected_branches = [b for b in branches if b.get("protected")]
            total_branches = len(branches)
            
            if total_branches > 0:
                features["branch_protection_compliance"] = len(protected_branches) / total_branches
            
            # Check main/master branch specifically
            main_branches = [b for b in branches if b.get("name") in ["main", "master"]]
            if main_branches:
                main_protected = any(b.get("protected") for b in main_branches)
                features["main_branch_protected"] = int(main_protected)
        
        # Commit signing compliance
        commits = data.get("commits", [])
        if commits:
            verified_commits = sum(1 for c in commits if c.get("verified"))
            features["commit_signing_compliance"] = verified_commits / max(1, len(commits))
        
        # PR review compliance
        prs = data.get("pull_requests", [])
        if prs:
            reviewed_prs = sum(1 for pr in prs if pr.get("reviews", 0) > 0)
            features["pr_review_compliance"] = reviewed_prs / max(1, len(prs))
            
            # Multi-reviewer compliance
            multi_reviewed = sum(1 for pr in prs if pr.get("reviews", 0) >= 2)
            features["multi_review_compliance"] = multi_reviewed / max(1, len(prs))
        
        # Security scanning indicators
        security_events = data.get("security_events", [])
        features["security_scanning_enabled"] = int(len(security_events) > 0)
        features["has_dependabot"] = int(any(e.get("type") == "dependabot" for e in security_events))
        features["has_code_scanning"] = int(any(e.get("type") == "code_scanning" for e in security_events))
        
        # CI/CD compliance
        workflows = data.get("workflows", [])
        if workflows:
            features["cicd_enabled"] = 1
            features["cicd_success_threshold"] = int(
                sum(1 for w in workflows if w.get("conclusion") == "success") / len(workflows) > 0.8
            )
        else:
            features["cicd_enabled"] = 0
            features["cicd_success_threshold"] = 0
        
        # Calculate overall compliance score
        compliance_metrics = [
            features["branch_protection_compliance"],
            features["commit_signing_compliance"],
            features["pr_review_compliance"],
            features.get("main_branch_protected", 0),
            features["security_scanning_enabled"],
            features["cicd_enabled"]
        ]
        features["overall_compliance_score"] = np.mean(compliance_metrics)
        
        return pd.DataFrame([features])
    
    def _check_commit_message_compliance(self, messages: List[str]) -> float:
        """Check commit message compliance with guidelines"""
        
        if not messages:
            return 0
        
        compliant = 0
        for message in messages:
            # Check basic requirements
            if len(message) < 10:
                continue
            
            # Check for conventional commit format
            pattern = r'^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\(.+\))?: .+'
            if re.match(pattern, message, re.IGNORECASE):
                compliant += 1
            # Check for basic format (capital letter, no period)
            elif message[0].isupper() and not message.endswith('.'):
                compliant += 0.5
        
        return compliant / len(messages)
    
    def _check_conventional_commits(self, messages: List[str]) -> float:
        """Check for conventional commit format"""
        
        if not messages:
            return 0
        
        pattern = r'^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\(.+\))?: .+'
        conventional = sum(1 for msg in messages if re.match(pattern, msg, re.IGNORECASE))
        
        return conventional / len(messages)
    
    def _detect_force_push_patterns(self, commits: List[Dict]) -> int:
        """Detect potential force push patterns"""
        
        if not commits:
            return 0
        
        df = pd.DataFrame(commits)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Look for suspicious patterns
        force_push_indicators = 0
        
        # Check for commits with unusual parent counts
        if 'parents_count' in df.columns:
            force_push_indicators += (df['parents_count'] == 0).sum()
        
        # Check for time anomalies (commits appearing out of order)
        if len(df) > 1:
            time_diffs = df['date'].diff()
            negative_diffs = (time_diffs < pd.Timedelta(0)).sum()
            force_push_indicators += negative_diffs
        
        return force_push_indicators
    
    def _calculate_age_days(self, date_str: str) -> float:
        """Calculate age in days from date string"""
        
        if not date_str:
            return 0
        
        try:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            age = (datetime.utcnow().replace(tzinfo=date.tzinfo) - date).days
            return max(0, age)
        except:
            return 0
    
    def _calculate_entropy(self, series: pd.Series) -> float:
        """Calculate Shannon entropy"""
        
        if len(series) == 0:
            return 0
        
        probabilities = series / series.sum()
        entropy = -sum(p * np.log2(p) for p in probabilities if p > 0)
        
        return entropy
    
    def _calculate_trend(self, series: pd.Series) -> float:
        """Calculate trend slope using linear regression"""
        
        if len(series) < 2:
            return 0
        
        x = np.arange(len(series))
        y = series.values
        
        # Simple linear regression
        coefficients = np.polyfit(x, y, 1)
        
        return coefficients[0]  # Return slope
    
    def _calculate_autocorrelation(self, series: pd.Series, lag: int = 1) -> float:
        """Calculate autocorrelation at specified lag"""
        
        if len(series) <= lag:
            return 0
        
        return series.autocorr(lag=lag)
    
    def create_feature_store(self, features: pd.DataFrame, repo_name: str):
        """Save engineered features to feature store"""
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.config.FEATURE_STORE_PATH}/features/{repo_name}_{timestamp}.parquet"
        
        features.to_parquet(filename, index=False)
        logger.info(f"Saved features to {filename}")
        
        return filename