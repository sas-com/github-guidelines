"""
Machine Learning Models for Violation Detection and Risk Prediction
"""

import logging
import pickle
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.ensemble import (
    RandomForestClassifier, 
    IsolationForest, 
    GradientBoostingClassifier,
    VotingClassifier
)
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.model_selection import (
    train_test_split, 
    cross_val_score, 
    GridSearchCV,
    StratifiedKFold
)
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    precision_recall_curve,
    f1_score,
    accuracy_score,
    recall_score,
    precision_score
)
from sklearn.calibration import CalibratedClassifierCV
import xgboost as xgb
import lightgbm as lgb
import shap
import joblib
from scipy import stats

from .config import Config

logger = logging.getLogger(__name__)


class ViolationDetector:
    """Multi-class violation detection system"""
    
    def __init__(self, config: Config):
        self.config = config
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.thresholds = {}
        self.feature_importance = {}
        self.model_performance = {}
        
        # Initialize models for each violation type
        self._initialize_models()
        
    def _initialize_models(self):
        """Initialize ML models for violation detection"""
        
        # Multi-class classifier for violation types
        self.models['violation_classifier'] = self._create_ensemble_classifier()
        
        # Binary classifiers for specific violations
        self.models['security_violation'] = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            objective='binary:logistic',
            random_state=self.config.RANDOM_STATE
        )
        
        self.models['commit_compliance'] = lgb.LGBMClassifier(
            n_estimators=150,
            num_leaves=31,
            learning_rate=0.1,
            feature_fraction=0.9,
            bagging_fraction=0.8,
            random_state=self.config.RANDOM_STATE
        )
        
        self.models['pr_process_violation'] = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=self.config.RANDOM_STATE
        )
        
        # Anomaly detection for unusual patterns
        self.models['anomaly_detector'] = IsolationForest(
            contamination=self.config.ANOMALY_CONTAMINATION,
            random_state=self.config.RANDOM_STATE,
            n_estimators=100
        )
        
        # Text classifier for commit messages
        self.models['text_classifier'] = LogisticRegression(
            max_iter=1000,
            random_state=self.config.RANDOM_STATE
        )
        
    def _create_ensemble_classifier(self) -> VotingClassifier:
        """Create ensemble classifier for violation detection"""
        
        estimators = [
            ('rf', RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=self.config.RANDOM_STATE
            )),
            ('xgb', xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=self.config.RANDOM_STATE
            )),
            ('lgb', lgb.LGBMClassifier(
                n_estimators=100,
                num_leaves=31,
                random_state=self.config.RANDOM_STATE
            ))
        ]
        
        return VotingClassifier(
            estimators=estimators,
            voting='soft'
        )
    
    def train(self, features: pd.DataFrame, labels: pd.DataFrame) -> Dict[str, Any]:
        """Train all violation detection models"""
        
        results = {}
        
        # Prepare data
        X_train, X_test, y_train, y_test = train_test_split(
            features, labels,
            test_size=1 - self.config.TRAIN_TEST_SPLIT,
            random_state=self.config.RANDOM_STATE,
            stratify=labels['violation_type'] if 'violation_type' in labels else None
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        self.scalers['main'] = scaler
        
        # Train multi-class violation classifier
        if 'violation_type' in labels:
            logger.info("Training multi-class violation classifier...")
            
            le = LabelEncoder()
            y_train_encoded = le.fit_transform(y_train['violation_type'])
            y_test_encoded = le.transform(y_test['violation_type'])
            self.encoders['violation_type'] = le
            
            # Train with cross-validation
            cv_scores = cross_val_score(
                self.models['violation_classifier'],
                X_train_scaled, y_train_encoded,
                cv=5, scoring='f1_weighted'
            )
            
            self.models['violation_classifier'].fit(X_train_scaled, y_train_encoded)
            
            # Evaluate
            y_pred = self.models['violation_classifier'].predict(X_test_scaled)
            
            results['violation_classifier'] = {
                'accuracy': accuracy_score(y_test_encoded, y_pred),
                'f1_weighted': f1_score(y_test_encoded, y_pred, average='weighted'),
                'cv_scores': cv_scores.tolist(),
                'classification_report': classification_report(
                    y_test_encoded, y_pred,
                    target_names=le.classes_
                )
            }
            
            # Feature importance
            self._calculate_feature_importance('violation_classifier', features.columns)
        
        # Train binary classifiers for specific violations
        for violation_type in ['security_violation', 'commit_compliance', 'pr_process_violation']:
            if violation_type in labels:
                logger.info(f"Training {violation_type} detector...")
                
                y_binary_train = labels[violation_type].iloc[X_train.index]
                y_binary_test = labels[violation_type].iloc[X_test.index]
                
                # Handle imbalanced data
                if y_binary_train.sum() < 10:
                    logger.warning(f"Insufficient positive samples for {violation_type}")
                    continue
                
                # Train model
                self.models[violation_type].fit(X_train_scaled, y_binary_train)
                
                # Predictions
                y_pred = self.models[violation_type].predict(X_test_scaled)
                y_pred_proba = self.models[violation_type].predict_proba(X_test_scaled)[:, 1]
                
                # Find optimal threshold
                optimal_threshold = self._find_optimal_threshold(y_binary_test, y_pred_proba)
                self.thresholds[violation_type] = optimal_threshold
                
                # Evaluate with optimal threshold
                y_pred_optimal = (y_pred_proba >= optimal_threshold).astype(int)
                
                results[violation_type] = {
                    'accuracy': accuracy_score(y_binary_test, y_pred_optimal),
                    'precision': precision_score(y_binary_test, y_pred_optimal),
                    'recall': recall_score(y_binary_test, y_pred_optimal),
                    'f1': f1_score(y_binary_test, y_pred_optimal),
                    'roc_auc': roc_auc_score(y_binary_test, y_pred_proba) if y_binary_test.nunique() > 1 else 0,
                    'optimal_threshold': optimal_threshold
                }
        
        # Train anomaly detector
        logger.info("Training anomaly detector...")
        self.models['anomaly_detector'].fit(X_train_scaled)
        
        # Detect anomalies in test set
        anomaly_predictions = self.models['anomaly_detector'].predict(X_test_scaled)
        anomaly_scores = self.models['anomaly_detector'].score_samples(X_test_scaled)
        
        results['anomaly_detector'] = {
            'anomaly_rate': (anomaly_predictions == -1).mean(),
            'score_threshold': np.percentile(anomaly_scores, 10)
        }
        
        self.model_performance = results
        return results
    
    def predict(self, features: pd.DataFrame) -> Dict[str, Any]:
        """Predict violations for new data"""
        
        predictions = {
            'violation_detected': False,
            'violation_types': [],
            'risk_scores': {},
            'anomaly_detected': False,
            'confidence_scores': {},
            'recommendations': []
        }
        
        # Scale features
        if 'main' in self.scalers:
            features_scaled = self.scalers['main'].transform(features)
        else:
            features_scaled = features.values
        
        # Multi-class violation prediction
        if 'violation_classifier' in self.models and 'violation_type' in self.encoders:
            try:
                violation_proba = self.models['violation_classifier'].predict_proba(features_scaled)[0]
                violation_pred = self.models['violation_classifier'].predict(features_scaled)[0]
                
                violation_type = self.encoders['violation_type'].inverse_transform([violation_pred])[0]
                predictions['violation_types'].append(violation_type)
                predictions['violation_detected'] = True
                
                # Confidence scores for each violation type
                for i, vtype in enumerate(self.encoders['violation_type'].classes_):
                    predictions['confidence_scores'][vtype] = float(violation_proba[i])
            except Exception as e:
                logger.error(f"Error in violation classification: {e}")
        
        # Binary violation predictions
        for violation_type in ['security_violation', 'commit_compliance', 'pr_process_violation']:
            if violation_type in self.models:
                try:
                    proba = self.models[violation_type].predict_proba(features_scaled)[0, 1]
                    threshold = self.thresholds.get(violation_type, 0.5)
                    
                    predictions['risk_scores'][violation_type] = float(proba)
                    
                    if proba >= threshold:
                        predictions['violation_detected'] = True
                        predictions['violation_types'].append(violation_type)
                except Exception as e:
                    logger.error(f"Error predicting {violation_type}: {e}")
        
        # Anomaly detection
        if 'anomaly_detector' in self.models:
            try:
                anomaly_pred = self.models['anomaly_detector'].predict(features_scaled)[0]
                anomaly_score = self.models['anomaly_detector'].score_samples(features_scaled)[0]
                
                predictions['anomaly_detected'] = bool(anomaly_pred == -1)
                predictions['anomaly_score'] = float(anomaly_score)
            except Exception as e:
                logger.error(f"Error in anomaly detection: {e}")
        
        # Generate recommendations
        predictions['recommendations'] = self._generate_recommendations(predictions)
        
        return predictions
    
    def _find_optimal_threshold(self, y_true: pd.Series, y_scores: np.ndarray) -> float:
        """Find optimal classification threshold using F1 score"""
        
        precision, recall, thresholds = precision_recall_curve(y_true, y_scores)
        
        # Calculate F1 scores
        f1_scores = 2 * (precision * recall) / (precision + recall + 1e-10)
        
        # Find threshold with best F1 score
        best_idx = np.argmax(f1_scores[:-1])
        optimal_threshold = thresholds[best_idx]
        
        return float(optimal_threshold)
    
    def _calculate_feature_importance(self, model_name: str, feature_names: List[str]):
        """Calculate and store feature importance"""
        
        model = self.models[model_name]
        
        if hasattr(model, 'feature_importances_'):
            importance = model.feature_importances_
        elif hasattr(model, 'coef_'):
            importance = np.abs(model.coef_[0])
        elif model_name == 'violation_classifier' and hasattr(model, 'estimators_'):
            # For voting classifier, average importance across estimators
            importances = []
            for est_name, est in model.estimators_:
                if hasattr(est, 'feature_importances_'):
                    importances.append(est.feature_importances_)
            importance = np.mean(importances, axis=0) if importances else None
        else:
            importance = None
        
        if importance is not None:
            # Sort features by importance
            indices = np.argsort(importance)[::-1]
            
            self.feature_importance[model_name] = {
                'features': [feature_names[i] for i in indices[:20]],
                'scores': [float(importance[i]) for i in indices[:20]]
            }
    
    def _generate_recommendations(self, predictions: Dict) -> List[str]:
        """Generate actionable recommendations based on predictions"""
        
        recommendations = []
        
        # Security violations
        if 'security_violation' in predictions['violation_types']:
            recommendations.append("Enable security scanning and dependency updates")
            recommendations.append("Review and fix security alerts immediately")
            recommendations.append("Implement signed commits requirement")
        
        # Commit compliance violations
        if 'commit_compliance' in predictions['violation_types']:
            recommendations.append("Enforce conventional commit message format")
            recommendations.append("Provide commit message templates and guidelines")
            recommendations.append("Enable commit message linting in CI/CD")
        
        # PR process violations
        if 'pr_process_violation' in predictions['violation_types']:
            recommendations.append("Require code reviews before merging")
            recommendations.append("Set up branch protection rules")
            recommendations.append("Implement PR templates and checklists")
        
        # Anomaly detected
        if predictions.get('anomaly_detected'):
            recommendations.append("Manual review recommended - unusual activity detected")
            recommendations.append("Check for unauthorized access or policy violations")
        
        # Risk-based recommendations
        for violation, score in predictions.get('risk_scores', {}).items():
            if score > 0.8:
                recommendations.append(f"High risk of {violation} - immediate action required")
            elif score > 0.5:
                recommendations.append(f"Moderate risk of {violation} - review recommended")
        
        return recommendations
    
    def explain_prediction(self, features: pd.DataFrame) -> Dict[str, Any]:
        """Generate SHAP explanations for predictions"""
        
        explanations = {}
        
        # Scale features
        if 'main' in self.scalers:
            features_scaled = self.scalers['main'].transform(features)
        else:
            features_scaled = features.values
        
        # Generate SHAP values for tree-based models
        for model_name in ['security_violation', 'pr_process_violation']:
            if model_name in self.models:
                try:
                    explainer = shap.TreeExplainer(self.models[model_name])
                    shap_values = explainer.shap_values(features_scaled)
                    
                    # Get top contributing features
                    if len(shap_values.shape) > 1:
                        shap_values = shap_values[0]
                    
                    feature_impacts = list(zip(features.columns, shap_values))
                    feature_impacts.sort(key=lambda x: abs(x[1]), reverse=True)
                    
                    explanations[model_name] = {
                        'top_features': feature_impacts[:10],
                        'base_value': float(explainer.expected_value)
                    }
                except Exception as e:
                    logger.error(f"Error generating SHAP explanation for {model_name}: {e}")
        
        return explanations
    
    def save_models(self, path: str):
        """Save trained models to disk"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_dir = f"{path}/violation_detector_{timestamp}"
        
        # Save models
        for name, model in self.models.items():
            model_path = f"{model_dir}/{name}.pkl"
            joblib.dump(model, model_path)
            logger.info(f"Saved model {name} to {model_path}")
        
        # Save scalers and encoders
        joblib.dump(self.scalers, f"{model_dir}/scalers.pkl")
        joblib.dump(self.encoders, f"{model_dir}/encoders.pkl")
        joblib.dump(self.thresholds, f"{model_dir}/thresholds.pkl")
        
        # Save metadata
        metadata = {
            'version': self.config.MODEL_VERSION,
            'timestamp': timestamp,
            'performance': self.model_performance,
            'feature_importance': self.feature_importance
        }
        
        with open(f"{model_dir}/metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return model_dir
    
    def load_models(self, model_dir: str):
        """Load models from disk"""
        
        # Load models
        for name in self.models.keys():
            model_path = f"{model_dir}/{name}.pkl"
            try:
                self.models[name] = joblib.load(model_path)
                logger.info(f"Loaded model {name}")
            except FileNotFoundError:
                logger.warning(f"Model {name} not found")
        
        # Load scalers and encoders
        self.scalers = joblib.load(f"{model_dir}/scalers.pkl")
        self.encoders = joblib.load(f"{model_dir}/encoders.pkl")
        self.thresholds = joblib.load(f"{model_dir}/thresholds.pkl")
        
        # Load metadata
        with open(f"{model_dir}/metadata.json", 'r') as f:
            metadata = json.load(f)
            self.model_performance = metadata.get('performance', {})
            self.feature_importance = metadata.get('feature_importance', {})


class RiskPredictor:
    """Predictive analytics for risk assessment"""
    
    def __init__(self, config: Config):
        self.config = config
        self.models = {}
        self.scalers = {}
        self.thresholds = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize risk prediction models"""
        
        # Security vulnerability risk
        self.models['security_risk'] = GradientBoostingClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.1,
            random_state=self.config.RANDOM_STATE
        )
        
        # CI/CD failure risk
        self.models['cicd_failure_risk'] = xgb.XGBClassifier(
            n_estimators=150,
            max_depth=6,
            learning_rate=0.1,
            objective='binary:logistic',
            random_state=self.config.RANDOM_STATE
        )
        
        # Developer training needs
        self.models['training_needs'] = RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            random_state=self.config.RANDOM_STATE
        )
        
        # Resource allocation predictor
        self.models['resource_predictor'] = lgb.LGBMRegressor(
            n_estimators=150,
            num_leaves=31,
            learning_rate=0.1,
            random_state=self.config.RANDOM_STATE
        )
    
    def train(self, features: pd.DataFrame, targets: Dict[str, pd.Series]) -> Dict[str, Any]:
        """Train risk prediction models"""
        
        results = {}
        
        # Prepare data
        X_train, X_test = train_test_split(
            features,
            test_size=1 - self.config.TRAIN_TEST_SPLIT,
            random_state=self.config.RANDOM_STATE
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        self.scalers['main'] = scaler
        
        # Train each risk model
        for risk_type, model in self.models.items():
            if risk_type in targets:
                logger.info(f"Training {risk_type} predictor...")
                
                y_train = targets[risk_type].iloc[X_train.index]
                y_test = targets[risk_type].iloc[X_test.index]
                
                # Train model
                model.fit(X_train_scaled, y_train)
                
                # Evaluate
                if risk_type == 'resource_predictor':
                    # Regression metrics
                    from sklearn.metrics import mean_squared_error, r2_score
                    y_pred = model.predict(X_test_scaled)
                    
                    results[risk_type] = {
                        'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
                        'r2': r2_score(y_test, y_pred)
                    }
                else:
                    # Classification metrics
                    y_pred = model.predict(X_test_scaled)
                    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
                    
                    results[risk_type] = {
                        'accuracy': accuracy_score(y_test, y_pred),
                        'precision': precision_score(y_test, y_pred),
                        'recall': recall_score(y_test, y_pred),
                        'f1': f1_score(y_test, y_pred),
                        'roc_auc': roc_auc_score(y_test, y_pred_proba) if y_test.nunique() > 1 else 0
                    }
        
        return results
    
    def predict_risks(self, features: pd.DataFrame) -> Dict[str, Any]:
        """Predict various risks for a repository"""
        
        predictions = {
            'risk_levels': {},
            'probabilities': {},
            'recommendations': [],
            'resource_needs': {}
        }
        
        # Scale features
        if 'main' in self.scalers:
            features_scaled = self.scalers['main'].transform(features)
        else:
            features_scaled = features.values
        
        # Security risk prediction
        if 'security_risk' in self.models:
            try:
                security_proba = self.models['security_risk'].predict_proba(features_scaled)[0, 1]
                predictions['probabilities']['security_vulnerability'] = float(security_proba)
                predictions['risk_levels']['security'] = self._categorize_risk(security_proba)
            except Exception as e:
                logger.error(f"Error predicting security risk: {e}")
        
        # CI/CD failure risk
        if 'cicd_failure_risk' in self.models:
            try:
                cicd_proba = self.models['cicd_failure_risk'].predict_proba(features_scaled)[0, 1]
                predictions['probabilities']['cicd_failure'] = float(cicd_proba)
                predictions['risk_levels']['cicd'] = self._categorize_risk(cicd_proba)
            except Exception as e:
                logger.error(f"Error predicting CI/CD risk: {e}")
        
        # Training needs assessment
        if 'training_needs' in self.models:
            try:
                training_proba = self.models['training_needs'].predict_proba(features_scaled)[0, 1]
                predictions['probabilities']['training_required'] = float(training_proba)
                
                if training_proba > 0.7:
                    predictions['recommendations'].append("Schedule developer training on GitHub best practices")
            except Exception as e:
                logger.error(f"Error predicting training needs: {e}")
        
        # Resource allocation prediction
        if 'resource_predictor' in self.models:
            try:
                resource_pred = self.models['resource_predictor'].predict(features_scaled)[0]
                predictions['resource_needs']['review_hours'] = float(resource_pred)
                predictions['resource_needs']['recommended_reviewers'] = max(1, int(resource_pred / 2))
            except Exception as e:
                logger.error(f"Error predicting resources: {e}")
        
        # Generate risk-based recommendations
        predictions['recommendations'].extend(self._generate_risk_recommendations(predictions))
        
        return predictions
    
    def _categorize_risk(self, probability: float) -> str:
        """Categorize risk level based on probability"""
        
        if probability >= self.config.RISK_THRESHOLDS['critical']:
            return 'critical'
        elif probability >= self.config.RISK_THRESHOLDS['high']:
            return 'high'
        elif probability >= self.config.RISK_THRESHOLDS['medium']:
            return 'medium'
        elif probability >= self.config.RISK_THRESHOLDS['low']:
            return 'low'
        else:
            return 'minimal'
    
    def _generate_risk_recommendations(self, predictions: Dict) -> List[str]:
        """Generate recommendations based on risk predictions"""
        
        recommendations = []
        
        # Security risk recommendations
        security_level = predictions['risk_levels'].get('security')
        if security_level in ['critical', 'high']:
            recommendations.append("Immediate security audit required")
            recommendations.append("Enable all security scanning tools")
            recommendations.append("Review and update dependencies")
        elif security_level == 'medium':
            recommendations.append("Schedule security review within a week")
        
        # CI/CD risk recommendations
        cicd_level = predictions['risk_levels'].get('cicd')
        if cicd_level in ['critical', 'high']:
            recommendations.append("Review and optimize CI/CD pipeline")
            recommendations.append("Add more comprehensive tests")
            recommendations.append("Consider pipeline parallelization")
        
        # Resource recommendations
        if predictions['resource_needs'].get('review_hours', 0) > 10:
            recommendations.append("Allocate additional review resources")
            recommendations.append("Consider breaking down large changes")
        
        return recommendations
    
    def forecast_metrics(self, historical_data: pd.DataFrame, horizon: int = 7) -> Dict[str, np.ndarray]:
        """Forecast future metrics using time series analysis"""
        
        forecasts = {}
        
        # Prepare time series data
        if 'date' not in historical_data.columns:
            logger.warning("No date column found for forecasting")
            return forecasts
        
        historical_data['date'] = pd.to_datetime(historical_data['date'])
        historical_data = historical_data.set_index('date').sort_index()
        
        # Forecast key metrics
        metrics_to_forecast = [
            'daily_commits',
            'open_issues',
            'pr_merge_rate',
            'cicd_success_rate'
        ]
        
        for metric in metrics_to_forecast:
            if metric in historical_data.columns:
                try:
                    # Simple exponential smoothing for now
                    from statsmodels.tsa.holtwinters import ExponentialSmoothing
                    
                    model = ExponentialSmoothing(
                        historical_data[metric],
                        seasonal='add',
                        seasonal_periods=7
                    )
                    fit = model.fit()
                    forecast = fit.forecast(horizon)
                    
                    forecasts[metric] = forecast.values
                except Exception as e:
                    logger.error(f"Error forecasting {metric}: {e}")
                    # Fallback to simple moving average
                    last_values = historical_data[metric].tail(7).mean()
                    forecasts[metric] = np.full(horizon, last_values)
        
        return forecasts
    
    def save_models(self, path: str) -> str:
        """Save risk prediction models"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_dir = f"{path}/risk_predictor_{timestamp}"
        
        # Save models and scalers
        for name, model in self.models.items():
            joblib.dump(model, f"{model_dir}/{name}.pkl")
        
        joblib.dump(self.scalers, f"{model_dir}/scalers.pkl")
        
        return model_dir
    
    def load_models(self, model_dir: str):
        """Load risk prediction models"""
        
        for name in self.models.keys():
            try:
                self.models[name] = joblib.load(f"{model_dir}/{name}.pkl")
            except FileNotFoundError:
                logger.warning(f"Model {name} not found")
        
        self.scalers = joblib.load(f"{model_dir}/scalers.pkl")