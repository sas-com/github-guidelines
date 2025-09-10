"""
Configuration module for ML Pipeline
"""

import os
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import timedelta

@dataclass
class Config:
    """Central configuration for ML pipeline"""
    
    # GitHub API Configuration
    GITHUB_ORG: str = "sas-com"
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_API_BASE: str = "https://api.github.com"
    
    # Model Configuration
    MODEL_VERSION: str = "1.0.0"
    MODEL_REGISTRY_PATH: str = "./models"
    FEATURE_STORE_PATH: str = "./feature_store"
    
    # Training Configuration
    TRAIN_TEST_SPLIT: float = 0.8
    VALIDATION_SPLIT: float = 0.1
    RANDOM_STATE: int = 42
    RETRAINING_INTERVAL: timedelta = timedelta(days=7)
    MIN_SAMPLES_FOR_TRAINING: int = 1000
    
    # Violation Types
    VIOLATION_CATEGORIES: List[str] = [
        "security_violation",
        "commit_message_violation",
        "branch_protection_violation",
        "pr_process_violation",
        "cicd_failure",
        "code_quality_violation",
        "documentation_missing",
        "dependency_vulnerability"
    ]
    
    # Risk Scoring Thresholds
    RISK_THRESHOLDS: Dict[str, float] = {
        "critical": 0.9,
        "high": 0.7,
        "medium": 0.5,
        "low": 0.3
    }
    
    # Feature Engineering Parameters
    FEATURE_WINDOW_DAYS: int = 30
    TEXT_MAX_FEATURES: int = 500
    MIN_WORD_FREQUENCY: int = 2
    
    # Model Parameters
    ANOMALY_CONTAMINATION: float = 0.1
    CLASSIFICATION_THRESHOLD: float = 0.5
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    API_TIMEOUT: int = 30
    
    # Monitoring Configuration
    DRIFT_THRESHOLD: float = 0.15
    PERFORMANCE_THRESHOLD: float = 0.85
    ALERT_EMAIL: str = "github@sas-com.com"
    
    # Database Configuration
    DB_CONNECTION_STRING: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost/github_ml"
    )
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "./logs/ml_pipeline.log"
    
    # DORA Metrics Thresholds
    DORA_TARGETS: Dict[str, Dict[str, float]] = {
        "deployment_frequency": {
            "excellent": 7,  # deployments per week
            "good": 1,
            "needs_improvement": 0.25
        },
        "lead_time": {
            "excellent": 1,  # days
            "good": 7,
            "needs_improvement": 30
        },
        "mttr": {
            "excellent": 1,  # hours
            "good": 24,
            "needs_improvement": 168
        },
        "change_failure_rate": {
            "excellent": 0.05,  # percentage
            "good": 0.15,
            "needs_improvement": 0.30
        }
    }
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables"""
        config = cls()
        for key in dir(config):
            if key.startswith("_"):
                continue
            env_key = f"ML_PIPELINE_{key}"
            if env_key in os.environ:
                setattr(config, key, os.environ[env_key])
        return config