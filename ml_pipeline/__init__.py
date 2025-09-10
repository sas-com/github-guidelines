"""
GitHub Guidelines Violation Detection ML Pipeline
SAS Company - Automated Compliance and Risk Prediction System
"""

__version__ = "1.0.0"
__author__ = "SAS GitHub Management Team"

from .config import Config
from .data_collector import GitHubDataCollector
from .feature_engineering import FeatureEngineer
from .models import ViolationDetector, RiskPredictor
from .api import ScoringAPI

__all__ = [
    "Config",
    "GitHubDataCollector",
    "FeatureEngineer",
    "ViolationDetector",
    "RiskPredictor",
    "ScoringAPI"
]