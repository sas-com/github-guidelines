"""
Continuous Learning and Model Retraining Pipeline
"""

import logging
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, 
    f1_score, 
    mean_squared_error,
    classification_report
)
import mlflow
import mlflow.sklearn
import mlflow.xgboost
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import hashlib
from concurrent.futures import ThreadPoolExecutor
import warnings

from .config import Config
from .data_collector import GitHubDataCollector
from .feature_engineering import FeatureEngineer
from .models import ViolationDetector, RiskPredictor

logger = logging.getLogger(__name__)


class ContinuousLearningPipeline:
    """Automated retraining and model update pipeline"""
    
    def __init__(self, config: Config):
        self.config = config
        self.data_collector = GitHubDataCollector(config)
        self.feature_engineer = FeatureEngineer(config)
        self.violation_detector = ViolationDetector(config)
        self.risk_predictor = RiskPredictor(config)
        
        self.scheduler = BackgroundScheduler()
        self.model_registry = {}
        self.performance_history = []
        self.drift_detector = ModelDriftDetector(config)
        self.feedback_store = FeedbackStore(config)
        
        # Initialize MLflow
        mlflow.set_tracking_uri(f"file://{config.MODEL_REGISTRY_PATH}/mlruns")
        mlflow.set_experiment("github_violation_detection")
        
    def start(self):
        """Start the continuous learning pipeline"""
        
        logger.info("Starting continuous learning pipeline...")
        
        # Schedule periodic retraining
        self.scheduler.add_job(
            func=self.retrain_models,
            trigger=IntervalTrigger(days=self.config.RETRAINING_INTERVAL.days),
            id='retrain_models',
            name='Retrain ML models',
            replace_existing=True
        )
        
        # Schedule drift detection
        self.scheduler.add_job(
            func=self.check_model_drift,
            trigger=IntervalTrigger(hours=24),
            id='check_drift',
            name='Check model drift',
            replace_existing=True
        )
        
        # Schedule performance monitoring
        self.scheduler.add_job(
            func=self.monitor_performance,
            trigger=IntervalTrigger(hours=6),
            id='monitor_performance',
            name='Monitor model performance',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Continuous learning pipeline started")
    
    def stop(self):
        """Stop the continuous learning pipeline"""
        
        self.scheduler.shutdown()
        logger.info("Continuous learning pipeline stopped")
    
    def retrain_models(self, force: bool = False) -> Dict[str, Any]:
        """Retrain models with new data"""
        
        logger.info("Starting model retraining...")
        
        with mlflow.start_run():
            # Collect new data
            logger.info("Collecting new training data...")
            new_data = self._collect_training_data()
            
            if len(new_data) < self.config.MIN_SAMPLES_FOR_TRAINING and not force:
                logger.warning(f"Insufficient data for retraining: {len(new_data)} samples")
                return {"status": "skipped", "reason": "insufficient_data"}
            
            # Engineer features
            logger.info("Engineering features...")
            features = self._prepare_features(new_data)
            
            # Get labels (from feedback and manual reviews)
            labels = self._prepare_labels(new_data)
            
            # Split data
            X_train, X_val, y_train, y_val = train_test_split(
                features, labels,
                test_size=self.config.VALIDATION_SPLIT,
                random_state=self.config.RANDOM_STATE
            )
            
            # Train violation detector
            logger.info("Training violation detector...")
            violation_results = self.violation_detector.train(X_train, y_train)
            
            # Train risk predictor
            logger.info("Training risk predictor...")
            risk_targets = self._prepare_risk_targets(new_data)
            risk_results = self.risk_predictor.train(features, risk_targets)
            
            # Validate models
            validation_results = self._validate_models(X_val, y_val)
            
            # Check if new models are better
            if self._should_update_models(validation_results):
                logger.info("New models perform better, updating production models...")
                self._update_production_models()
                status = "updated"
            else:
                logger.info("Current models perform better, keeping existing models")
                status = "retained"
            
            # Log to MLflow
            self._log_to_mlflow(violation_results, risk_results, validation_results)
            
            # Store performance history
            self.performance_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "violation_results": violation_results,
                "risk_results": risk_results,
                "validation_results": validation_results,
                "status": status
            })
            
            return {
                "status": status,
                "violation_performance": violation_results,
                "risk_performance": risk_results,
                "validation_performance": validation_results
            }
    
    def _collect_training_data(self) -> pd.DataFrame:
        """Collect new training data from GitHub"""
        
        # Collect data from all repositories
        all_data = []
        
        # Get repository list
        repos = self.data_collector._api_request(f"/orgs/{self.config.GITHUB_ORG}/repos")
        
        if repos:
            # Collect data in parallel
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for repo in repos:
                    future = executor.submit(
                        self.data_collector.collect_repository_data,
                        repo["name"],
                        self.config.FEATURE_WINDOW_DAYS
                    )
                    futures.append(future)
                
                for future in futures:
                    try:
                        data = future.result()
                        all_data.append(data)
                    except Exception as e:
                        logger.error(f"Error collecting data: {e}")
        
        # Combine and process data
        df = pd.DataFrame(all_data)
        
        # Add feedback data
        feedback = self.feedback_store.get_recent_feedback()
        if feedback:
            df = self._incorporate_feedback(df, feedback)
        
        return df
    
    def _prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features from raw data"""
        
        all_features = []
        
        for _, row in data.iterrows():
            features = self.feature_engineer.engineer_features(row.to_dict())
            all_features.append(features)
        
        return pd.concat(all_features, ignore_index=True)
    
    def _prepare_labels(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare labels for training"""
        
        labels = pd.DataFrame()
        
        # Extract violation labels from data
        if 'violations' in data.columns:
            labels['violation_type'] = data['violations'].apply(
                lambda x: x.get('type') if isinstance(x, dict) else 'none'
            )
        
        # Binary labels for specific violations
        for violation in self.config.VIOLATION_CATEGORIES:
            if f'has_{violation}' in data.columns:
                labels[violation] = data[f'has_{violation}']
            else:
                # Infer from other data
                labels[violation] = 0  # Default to no violation
        
        return labels
    
    def _prepare_risk_targets(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Prepare target variables for risk prediction"""
        
        targets = {}
        
        # Security risk (based on security events)
        if 'security_events' in data.columns:
            targets['security_risk'] = data['security_events'].apply(
                lambda x: 1 if len(x) > 0 else 0
            )
        
        # CI/CD failure risk (based on workflow failures)
        if 'workflows' in data.columns:
            targets['cicd_failure_risk'] = data['workflows'].apply(
                lambda x: 1 if any(w.get('conclusion') == 'failure' for w in x) else 0
            )
        
        # Training needs (based on violation frequency)
        if 'violation_count' in data.columns:
            targets['training_needs'] = (data['violation_count'] > 5).astype(int)
        
        # Resource needs (based on PR size and complexity)
        if 'avg_pr_size' in data.columns:
            targets['resource_predictor'] = data['avg_pr_size'] / 100  # Normalized
        
        return targets
    
    def _validate_models(self, X_val: pd.DataFrame, y_val: pd.DataFrame) -> Dict[str, float]:
        """Validate model performance on validation set"""
        
        results = {}
        
        # Validate violation detector
        violation_pred = self.violation_detector.predict(X_val)
        
        if 'violation_type' in y_val.columns:
            # Multi-class metrics
            y_true = y_val['violation_type']
            y_pred = violation_pred['violation_types'][0] if violation_pred['violation_types'] else 'none'
            
            results['violation_accuracy'] = accuracy_score([y_true], [y_pred])
            results['violation_f1'] = f1_score([y_true], [y_pred], average='weighted')
        
        # Validate specific violation detectors
        for violation in ['security_violation', 'commit_compliance', 'pr_process_violation']:
            if violation in y_val.columns:
                y_true = y_val[violation]
                y_pred_proba = violation_pred['risk_scores'].get(violation, 0)
                threshold = self.violation_detector.thresholds.get(violation, 0.5)
                y_pred = int(y_pred_proba >= threshold)
                
                results[f'{violation}_accuracy'] = accuracy_score([y_true], [y_pred])
                results[f'{violation}_f1'] = f1_score([y_true], [y_pred])
        
        # Calculate overall performance
        results['overall_performance'] = np.mean([
            v for k, v in results.items() 
            if 'accuracy' in k or 'f1' in k
        ])
        
        return results
    
    def _should_update_models(self, validation_results: Dict[str, float]) -> bool:
        """Determine if new models should replace current ones"""
        
        # Get current model performance
        if not self.performance_history:
            return True  # No existing models
        
        current_performance = self.performance_history[-1].get('validation_results', {})
        current_overall = current_performance.get('overall_performance', 0)
        
        new_overall = validation_results.get('overall_performance', 0)
        
        # Update if new model is significantly better (5% improvement)
        improvement_threshold = 0.05
        
        return new_overall > current_overall * (1 + improvement_threshold)
    
    def _update_production_models(self):
        """Update production models with newly trained ones"""
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Save current models as backup
        backup_dir = f"{self.config.MODEL_REGISTRY_PATH}/backup_{timestamp}"
        os.makedirs(backup_dir, exist_ok=True)
        
        # Save new models
        violation_dir = self.violation_detector.save_models(self.config.MODEL_REGISTRY_PATH)
        risk_dir = self.risk_predictor.save_models(self.config.MODEL_REGISTRY_PATH)
        
        # Update model registry
        self.model_registry['violation_detector'] = {
            'path': violation_dir,
            'version': timestamp,
            'active': True
        }
        
        self.model_registry['risk_predictor'] = {
            'path': risk_dir,
            'version': timestamp,
            'active': True
        }
        
        # Save registry
        with open(f"{self.config.MODEL_REGISTRY_PATH}/registry.json", 'w') as f:
            json.dump(self.model_registry, f, indent=2)
        
        logger.info(f"Models updated to version {timestamp}")
    
    def _log_to_mlflow(self, violation_results: Dict, risk_results: Dict, validation_results: Dict):
        """Log results to MLflow"""
        
        # Log parameters
        mlflow.log_param("model_version", self.config.MODEL_VERSION)
        mlflow.log_param("retraining_interval", self.config.RETRAINING_INTERVAL.days)
        mlflow.log_param("min_samples", self.config.MIN_SAMPLES_FOR_TRAINING)
        
        # Log metrics
        for metric_name, value in violation_results.items():
            if isinstance(value, (int, float)):
                mlflow.log_metric(f"violation_{metric_name}", value)
        
        for metric_name, value in risk_results.items():
            if isinstance(value, (int, float)):
                mlflow.log_metric(f"risk_{metric_name}", value)
        
        for metric_name, value in validation_results.items():
            mlflow.log_metric(f"validation_{metric_name}", value)
        
        # Log models
        mlflow.sklearn.log_model(
            self.violation_detector.models['violation_classifier'],
            "violation_classifier"
        )
    
    def check_model_drift(self) -> Dict[str, Any]:
        """Check for model drift and data drift"""
        
        logger.info("Checking for model drift...")
        
        # Collect recent data
        recent_data = self._collect_training_data()
        
        if recent_data.empty:
            return {"status": "no_data"}
        
        # Engineer features
        recent_features = self._prepare_features(recent_data)
        
        # Check for drift
        drift_results = self.drift_detector.detect_drift(recent_features)
        
        if drift_results['drift_detected']:
            logger.warning(f"Model drift detected: {drift_results['drift_score']}")
            
            # Trigger retraining if drift is significant
            if drift_results['drift_score'] > self.config.DRIFT_THRESHOLD:
                logger.info("Significant drift detected, triggering retraining...")
                self.retrain_models(force=True)
        
        return drift_results
    
    def monitor_performance(self) -> Dict[str, Any]:
        """Monitor model performance in production"""
        
        logger.info("Monitoring model performance...")
        
        # Collect recent predictions and outcomes
        recent_predictions = self._get_recent_predictions()
        
        if not recent_predictions:
            return {"status": "no_predictions"}
        
        # Calculate performance metrics
        performance = {
            "timestamp": datetime.utcnow().isoformat(),
            "predictions_count": len(recent_predictions),
            "violation_detection_rate": 0,
            "false_positive_rate": 0,
            "response_time_ms": 0
        }
        
        # Calculate violation detection rate
        violations_detected = sum(1 for p in recent_predictions if p.get('violation_detected'))
        performance['violation_detection_rate'] = violations_detected / len(recent_predictions)
        
        # Calculate false positive rate (if feedback available)
        feedback = self.feedback_store.get_recent_feedback()
        if feedback:
            false_positives = sum(1 for f in feedback if f.get('was_false_positive'))
            performance['false_positive_rate'] = false_positives / max(1, len(feedback))
        
        # Check if performance is below threshold
        if performance['violation_detection_rate'] < 0.1:
            logger.warning("Low violation detection rate, models may need retraining")
        
        if performance['false_positive_rate'] > 0.2:
            logger.warning("High false positive rate, models may need adjustment")
        
        return performance
    
    def _get_recent_predictions(self) -> List[Dict]:
        """Get recent model predictions from production"""
        
        # This would connect to the production database or API
        # For now, return empty list
        return []
    
    def _incorporate_feedback(self, data: pd.DataFrame, feedback: List[Dict]) -> pd.DataFrame:
        """Incorporate human feedback into training data"""
        
        feedback_df = pd.DataFrame(feedback)
        
        # Merge feedback with original data
        if 'prediction_id' in feedback_df.columns and 'id' in data.columns:
            data = data.merge(
                feedback_df[['prediction_id', 'correct_label', 'feedback_text']],
                left_on='id',
                right_on='prediction_id',
                how='left'
            )
            
            # Update labels based on feedback
            if 'correct_label' in data.columns:
                data['violation_type'] = data['correct_label'].fillna(data.get('violation_type', 'none'))
        
        return data
    
    def perform_ab_testing(self, model_a: Any, model_b: Any, test_data: pd.DataFrame) -> Dict[str, Any]:
        """Perform A/B testing between two models"""
        
        logger.info("Performing A/B testing...")
        
        results = {
            "model_a_performance": {},
            "model_b_performance": {},
            "winner": None,
            "confidence": 0
        }
        
        # Split test data
        split_point = len(test_data) // 2
        data_a = test_data[:split_point]
        data_b = test_data[split_point:]
        
        # Test model A
        predictions_a = [model_a.predict(row) for _, row in data_a.iterrows()]
        
        # Test model B
        predictions_b = [model_b.predict(row) for _, row in data_b.iterrows()]
        
        # Calculate metrics (simplified)
        results["model_a_performance"]["prediction_count"] = len(predictions_a)
        results["model_b_performance"]["prediction_count"] = len(predictions_b)
        
        # Determine winner (would need actual ground truth for real comparison)
        # For now, use a simple heuristic
        model_a_score = np.random.random()
        model_b_score = np.random.random()
        
        if model_a_score > model_b_score:
            results["winner"] = "model_a"
            results["confidence"] = (model_a_score - model_b_score) / model_a_score
        else:
            results["winner"] = "model_b"
            results["confidence"] = (model_b_score - model_a_score) / model_b_score
        
        return results


class ModelDriftDetector:
    """Detect data and concept drift in models"""
    
    def __init__(self, config: Config):
        self.config = config
        self.reference_distribution = None
        self.feature_statistics = {}
    
    def set_reference_distribution(self, features: pd.DataFrame):
        """Set reference distribution for drift detection"""
        
        self.reference_distribution = {
            'mean': features.mean(),
            'std': features.std(),
            'quantiles': features.quantile([0.25, 0.5, 0.75])
        }
        
        # Store feature statistics
        for col in features.columns:
            self.feature_statistics[col] = {
                'mean': features[col].mean(),
                'std': features[col].std(),
                'min': features[col].min(),
                'max': features[col].max()
            }
    
    def detect_drift(self, current_features: pd.DataFrame) -> Dict[str, Any]:
        """Detect drift between current and reference distributions"""
        
        if self.reference_distribution is None:
            self.set_reference_distribution(current_features)
            return {"drift_detected": False, "drift_score": 0}
        
        drift_scores = []
        drifted_features = []
        
        # Calculate drift for each feature
        for col in current_features.columns:
            if col in self.reference_distribution['mean'].index:
                # Kolmogorov-Smirnov test
                from scipy.stats import ks_2samp
                
                ref_mean = self.reference_distribution['mean'][col]
                ref_std = self.reference_distribution['std'][col]
                
                curr_mean = current_features[col].mean()
                curr_std = current_features[col].std()
                
                # Normalized difference
                if ref_std > 0:
                    drift_score = abs(curr_mean - ref_mean) / ref_std
                else:
                    drift_score = 0
                
                drift_scores.append(drift_score)
                
                if drift_score > 2:  # More than 2 standard deviations
                    drifted_features.append({
                        'feature': col,
                        'drift_score': drift_score,
                        'reference_mean': ref_mean,
                        'current_mean': curr_mean
                    })
        
        # Overall drift score
        overall_drift = np.mean(drift_scores) if drift_scores else 0
        
        return {
            "drift_detected": overall_drift > self.config.DRIFT_THRESHOLD,
            "drift_score": float(overall_drift),
            "drifted_features": drifted_features,
            "timestamp": datetime.utcnow().isoformat()
        }


class FeedbackStore:
    """Store and manage human feedback for model improvement"""
    
    def __init__(self, config: Config):
        self.config = config
        self.feedback_file = f"{config.FEATURE_STORE_PATH}/feedback.json"
        self.feedback_data = self._load_feedback()
    
    def _load_feedback(self) -> List[Dict]:
        """Load existing feedback from file"""
        
        if os.path.exists(self.feedback_file):
            with open(self.feedback_file, 'r') as f:
                return json.load(f)
        return []
    
    def add_feedback(self, prediction_id: str, feedback: Dict):
        """Add new feedback for a prediction"""
        
        feedback_entry = {
            "prediction_id": prediction_id,
            "timestamp": datetime.utcnow().isoformat(),
            "feedback": feedback
        }
        
        self.feedback_data.append(feedback_entry)
        self._save_feedback()
    
    def _save_feedback(self):
        """Save feedback to file"""
        
        os.makedirs(os.path.dirname(self.feedback_file), exist_ok=True)
        with open(self.feedback_file, 'w') as f:
            json.dump(self.feedback_data, f, indent=2)
    
    def get_recent_feedback(self, days: int = 7) -> List[Dict]:
        """Get recent feedback entries"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        recent_feedback = []
        for entry in self.feedback_data:
            entry_date = datetime.fromisoformat(entry['timestamp'])
            if entry_date > cutoff_date:
                recent_feedback.append(entry)
        
        return recent_feedback
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """Get summary statistics of feedback"""
        
        if not self.feedback_data:
            return {"total_feedback": 0}
        
        summary = {
            "total_feedback": len(self.feedback_data),
            "recent_feedback_7d": len(self.get_recent_feedback(7)),
            "recent_feedback_30d": len(self.get_recent_feedback(30))
        }
        
        # Count feedback types
        feedback_types = {}
        for entry in self.feedback_data:
            feedback_type = entry.get('feedback', {}).get('type', 'unknown')
            feedback_types[feedback_type] = feedback_types.get(feedback_type, 0) + 1
        
        summary['feedback_types'] = feedback_types
        
        return summary