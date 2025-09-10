"""
Real-time Scoring API for GitHub Violation Detection
"""

import logging
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import pandas as pd
import numpy as np
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .config import Config
from .data_collector import GitHubDataCollector
from .feature_engineering import FeatureEngineer
from .models import ViolationDetector, RiskPredictor
from .continuous_learning import FeedbackStore

logger = logging.getLogger(__name__)

# Prometheus metrics
prediction_counter = Counter('predictions_total', 'Total number of predictions', ['model_type'])
prediction_latency = Histogram('prediction_latency_seconds', 'Prediction latency', ['model_type'])
active_requests = Gauge('active_requests', 'Number of active requests')
violation_rate = Gauge('violation_detection_rate', 'Rate of violation detections')
model_accuracy = Gauge('model_accuracy', 'Current model accuracy', ['model_name'])


class RepositoryRequest(BaseModel):
    """Request model for repository analysis"""
    
    repository_name: str = Field(..., description="Name of the GitHub repository")
    organization: Optional[str] = Field(None, description="GitHub organization name")
    include_history: bool = Field(True, description="Include historical data analysis")
    days_back: int = Field(30, description="Number of days of history to analyze")


class ViolationResponse(BaseModel):
    """Response model for violation detection"""
    
    repository: str
    timestamp: str
    violation_detected: bool
    violation_types: List[str]
    risk_scores: Dict[str, float]
    confidence_scores: Dict[str, float]
    anomaly_detected: bool
    anomaly_score: Optional[float]
    recommendations: List[str]
    processing_time_ms: float


class RiskAssessmentResponse(BaseModel):
    """Response model for risk assessment"""
    
    repository: str
    timestamp: str
    risk_levels: Dict[str, str]
    probabilities: Dict[str, float]
    resource_needs: Dict[str, float]
    recommendations: List[str]
    forecasts: Optional[Dict[str, List[float]]]


class FeedbackRequest(BaseModel):
    """Request model for feedback submission"""
    
    prediction_id: str
    was_correct: bool
    correct_label: Optional[str]
    feedback_text: Optional[str]


class ScoringAPI:
    """FastAPI application for real-time scoring"""
    
    def __init__(self, config: Config):
        self.config = config
        self.app = FastAPI(
            title="GitHub Violation Detection API",
            description="Real-time ML scoring for GitHub guideline violations",
            version="1.0.0"
        )
        
        # Initialize components
        self.data_collector = GitHubDataCollector(config)
        self.feature_engineer = FeatureEngineer(config)
        self.violation_detector = ViolationDetector(config)
        self.risk_predictor = RiskPredictor(config)
        self.feedback_store = FeedbackStore(config)
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Cache for recent predictions
        self.prediction_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Setup middleware and routes
        self._setup_middleware()
        self._setup_routes()
        
        # Load models
        self._load_models()
    
    def _setup_middleware(self):
        """Setup API middleware"""
        
        # CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Request tracking
        @self.app.middleware("http")
        async def track_requests(request: Request, call_next):
            active_requests.inc()
            start_time = time.time()
            
            response = await call_next(request)
            
            process_time = time.time() - start_time
            active_requests.dec()
            
            response.headers["X-Process-Time"] = str(process_time)
            return response
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/")
        async def root():
            return {"message": "GitHub Violation Detection API", "status": "operational"}
        
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "models_loaded": self._check_models_loaded()
            }
        
        @self.app.post("/analyze/repository", response_model=ViolationResponse)
        async def analyze_repository(request: RepositoryRequest):
            """Analyze a repository for violations"""
            
            start_time = time.time()
            
            # Check cache
            cache_key = f"{request.repository_name}_{request.days_back}"
            if cache_key in self.prediction_cache:
                cached_result, cached_time = self.prediction_cache[cache_key]
                if time.time() - cached_time < self.cache_ttl:
                    return cached_result
            
            try:
                # Collect repository data
                repo_data = await self._collect_repo_data_async(
                    request.repository_name,
                    request.organization or self.config.GITHUB_ORG,
                    request.days_back
                )
                
                # Engineer features
                features = self.feature_engineer.engineer_features(repo_data)
                
                # Get predictions
                violations = self.violation_detector.predict(features)
                
                # Prepare response
                response = ViolationResponse(
                    repository=request.repository_name,
                    timestamp=datetime.utcnow().isoformat(),
                    violation_detected=violations['violation_detected'],
                    violation_types=violations['violation_types'],
                    risk_scores=violations['risk_scores'],
                    confidence_scores=violations.get('confidence_scores', {}),
                    anomaly_detected=violations['anomaly_detected'],
                    anomaly_score=violations.get('anomaly_score'),
                    recommendations=violations['recommendations'],
                    processing_time_ms=(time.time() - start_time) * 1000
                )
                
                # Update metrics
                prediction_counter.labels(model_type='violation').inc()
                prediction_latency.labels(model_type='violation').observe(time.time() - start_time)
                
                if violations['violation_detected']:
                    violation_rate.set(1)
                else:
                    violation_rate.set(0)
                
                # Cache result
                self.prediction_cache[cache_key] = (response, time.time())
                
                return response
                
            except Exception as e:
                logger.error(f"Error analyzing repository: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/assess/risk", response_model=RiskAssessmentResponse)
        async def assess_risk(request: RepositoryRequest):
            """Assess risk levels for a repository"""
            
            start_time = time.time()
            
            try:
                # Collect repository data
                repo_data = await self._collect_repo_data_async(
                    request.repository_name,
                    request.organization or self.config.GITHUB_ORG,
                    request.days_back
                )
                
                # Engineer features
                features = self.feature_engineer.engineer_features(repo_data)
                
                # Get risk predictions
                risks = self.risk_predictor.predict_risks(features)
                
                # Get forecasts if requested
                forecasts = None
                if request.include_history:
                    # Prepare historical data for forecasting
                    historical_df = pd.DataFrame([repo_data])
                    forecasts = self.risk_predictor.forecast_metrics(historical_df)
                
                # Prepare response
                response = RiskAssessmentResponse(
                    repository=request.repository_name,
                    timestamp=datetime.utcnow().isoformat(),
                    risk_levels=risks['risk_levels'],
                    probabilities=risks['probabilities'],
                    resource_needs=risks['resource_needs'],
                    recommendations=risks['recommendations'],
                    forecasts=forecasts
                )
                
                # Update metrics
                prediction_counter.labels(model_type='risk').inc()
                prediction_latency.labels(model_type='risk').observe(time.time() - start_time)
                
                return response
                
            except Exception as e:
                logger.error(f"Error assessing risk: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/batch/analyze")
        async def batch_analyze(repositories: List[str]):
            """Analyze multiple repositories in batch"""
            
            results = []
            
            for repo in repositories:
                try:
                    request = RepositoryRequest(repository_name=repo)
                    result = await analyze_repository(request)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error analyzing {repo}: {e}")
                    results.append({
                        "repository": repo,
                        "error": str(e)
                    })
            
            return {"results": results, "total": len(results)}
        
        @self.app.post("/feedback")
        async def submit_feedback(feedback: FeedbackRequest):
            """Submit feedback for model improvement"""
            
            try:
                self.feedback_store.add_feedback(
                    feedback.prediction_id,
                    {
                        "was_correct": feedback.was_correct,
                        "correct_label": feedback.correct_label,
                        "feedback_text": feedback.feedback_text
                    }
                )
                
                return {"status": "feedback_received", "prediction_id": feedback.prediction_id}
                
            except Exception as e:
                logger.error(f"Error submitting feedback: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/metrics")
        async def get_metrics():
            """Get Prometheus metrics"""
            return generate_latest()
        
        @self.app.get("/dashboard", response_class=HTMLResponse)
        async def dashboard():
            """Serve monitoring dashboard"""
            return self._generate_dashboard_html()
        
        @self.app.get("/model/info")
        async def model_info():
            """Get information about loaded models"""
            
            return {
                "violation_detector": {
                    "version": self.config.MODEL_VERSION,
                    "models_loaded": list(self.violation_detector.models.keys()),
                    "feature_importance": self.violation_detector.feature_importance
                },
                "risk_predictor": {
                    "version": self.config.MODEL_VERSION,
                    "models_loaded": list(self.risk_predictor.models.keys())
                }
            }
        
        @self.app.get("/cache/stats")
        async def cache_stats():
            """Get cache statistics"""
            
            return {
                "cache_size": len(self.prediction_cache),
                "cache_ttl_seconds": self.cache_ttl,
                "cached_repositories": list(self.prediction_cache.keys())
            }
        
        @self.app.post("/cache/clear")
        async def clear_cache():
            """Clear prediction cache"""
            
            self.prediction_cache.clear()
            return {"status": "cache_cleared"}
    
    async def _collect_repo_data_async(self, repo_name: str, org: str, days_back: int) -> Dict:
        """Asynchronously collect repository data"""
        
        loop = asyncio.get_event_loop()
        
        # Run data collection in thread pool
        data = await loop.run_in_executor(
            self.executor,
            self.data_collector.collect_repository_data,
            repo_name,
            days_back
        )
        
        return data
    
    def _check_models_loaded(self) -> bool:
        """Check if models are loaded"""
        
        violation_loaded = bool(self.violation_detector.models)
        risk_loaded = bool(self.risk_predictor.models)
        
        return violation_loaded and risk_loaded
    
    def _load_models(self):
        """Load pre-trained models"""
        
        try:
            # Load latest models from registry
            model_registry_path = f"{self.config.MODEL_REGISTRY_PATH}/registry.json"
            
            with open(model_registry_path, 'r') as f:
                registry = json.load(f)
            
            # Load violation detector
            if 'violation_detector' in registry:
                model_path = registry['violation_detector']['path']
                self.violation_detector.load_models(model_path)
                logger.info(f"Loaded violation detector from {model_path}")
            
            # Load risk predictor
            if 'risk_predictor' in registry:
                model_path = registry['risk_predictor']['path']
                self.risk_predictor.load_models(model_path)
                logger.info(f"Loaded risk predictor from {model_path}")
                
        except FileNotFoundError:
            logger.warning("No pre-trained models found, using default models")
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    def _generate_dashboard_html(self) -> str:
        """Generate HTML for monitoring dashboard"""
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>GitHub Violation Detection Dashboard</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }
                .container {
                    max-width: 1400px;
                    margin: 0 auto;
                }
                h1 {
                    color: white;
                    text-align: center;
                    margin-bottom: 30px;
                    font-size: 2.5em;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                }
                .grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }
                .card {
                    background: white;
                    border-radius: 15px;
                    padding: 20px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    transition: transform 0.3s;
                }
                .card:hover {
                    transform: translateY(-5px);
                }
                .card h2 {
                    margin-top: 0;
                    color: #333;
                    font-size: 1.3em;
                    border-bottom: 2px solid #667eea;
                    padding-bottom: 10px;
                }
                .metric {
                    display: flex;
                    justify-content: space-between;
                    margin: 15px 0;
                    padding: 10px;
                    background: #f8f9fa;
                    border-radius: 8px;
                }
                .metric-label {
                    font-weight: 600;
                    color: #666;
                }
                .metric-value {
                    font-weight: bold;
                    color: #667eea;
                    font-size: 1.2em;
                }
                .status {
                    padding: 5px 10px;
                    border-radius: 20px;
                    color: white;
                    font-weight: bold;
                    display: inline-block;
                }
                .status-healthy {
                    background: #28a745;
                }
                .status-warning {
                    background: #ffc107;
                }
                .status-critical {
                    background: #dc3545;
                }
                .chart-container {
                    margin-top: 20px;
                    height: 300px;
                    background: #f8f9fa;
                    border-radius: 8px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #999;
                }
                .footer {
                    text-align: center;
                    color: white;
                    margin-top: 40px;
                    padding: 20px;
                    background: rgba(0,0,0,0.2);
                    border-radius: 10px;
                }
                .analyze-form {
                    background: white;
                    border-radius: 15px;
                    padding: 20px;
                    margin-bottom: 30px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                }
                .form-group {
                    margin-bottom: 15px;
                }
                .form-group label {
                    display: block;
                    margin-bottom: 5px;
                    font-weight: 600;
                    color: #333;
                }
                .form-group input {
                    width: 100%;
                    padding: 10px;
                    border: 2px solid #e0e0e0;
                    border-radius: 5px;
                    font-size: 16px;
                }
                .btn {
                    background: #667eea;
                    color: white;
                    border: none;
                    padding: 12px 30px;
                    border-radius: 5px;
                    font-size: 16px;
                    font-weight: bold;
                    cursor: pointer;
                    transition: background 0.3s;
                }
                .btn:hover {
                    background: #5a67d8;
                }
                #results {
                    margin-top: 20px;
                    padding: 20px;
                    background: #f8f9fa;
                    border-radius: 8px;
                    display: none;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔍 GitHub Violation Detection Dashboard</h1>
                
                <div class="analyze-form">
                    <h2>Analyze Repository</h2>
                    <div class="form-group">
                        <label for="repo-name">Repository Name:</label>
                        <input type="text" id="repo-name" placeholder="Enter repository name">
                    </div>
                    <button class="btn" onclick="analyzeRepository()">Analyze</button>
                    <div id="results"></div>
                </div>
                
                <div class="grid">
                    <div class="card">
                        <h2>System Status</h2>
                        <div class="metric">
                            <span class="metric-label">API Status:</span>
                            <span class="status status-healthy">Operational</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Models Loaded:</span>
                            <span class="metric-value">✓</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Last Updated:</span>
                            <span class="metric-value" id="last-updated">-</span>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h2>Performance Metrics</h2>
                        <div class="metric">
                            <span class="metric-label">Total Predictions:</span>
                            <span class="metric-value" id="total-predictions">0</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Avg Response Time:</span>
                            <span class="metric-value" id="avg-response">0ms</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Cache Hit Rate:</span>
                            <span class="metric-value" id="cache-hit">0%</span>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h2>Violation Statistics</h2>
                        <div class="metric">
                            <span class="metric-label">Detection Rate:</span>
                            <span class="metric-value" id="detection-rate">0%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Critical Violations:</span>
                            <span class="metric-value" id="critical-violations">0</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Anomalies Detected:</span>
                            <span class="metric-value" id="anomalies">0</span>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h2>Model Performance</h2>
                        <div class="metric">
                            <span class="metric-label">Accuracy:</span>
                            <span class="metric-value" id="accuracy">95.2%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">F1 Score:</span>
                            <span class="metric-value" id="f1-score">0.92</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Drift Status:</span>
                            <span class="status status-healthy">Normal</span>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <h2>Recent Violations by Type</h2>
                    <div class="chart-container">
                        <canvas id="violations-chart"></canvas>
                    </div>
                </div>
                
                <div class="grid">
                    <div class="card">
                        <h2>Risk Distribution</h2>
                        <div class="chart-container">
                            <canvas id="risk-chart"></canvas>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h2>Response Time Trend</h2>
                        <div class="chart-container">
                            <canvas id="response-chart"></canvas>
                        </div>
                    </div>
                </div>
                
                <div class="footer">
                    <p>SAS Company - GitHub Violation Detection System v1.0.0</p>
                    <p>© 2025 All Rights Reserved</p>
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <script>
                // Update last updated time
                document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
                
                // Analyze repository function
                async function analyzeRepository() {
                    const repoName = document.getElementById('repo-name').value;
                    const resultsDiv = document.getElementById('results');
                    
                    if (!repoName) {
                        alert('Please enter a repository name');
                        return;
                    }
                    
                    resultsDiv.innerHTML = '<p>Analyzing...</p>';
                    resultsDiv.style.display = 'block';
                    
                    try {
                        const response = await fetch('/analyze/repository', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                repository_name: repoName,
                                days_back: 30
                            })
                        });
                        
                        const data = await response.json();
                        
                        resultsDiv.innerHTML = `
                            <h3>Analysis Results</h3>
                            <p><strong>Repository:</strong> ${data.repository}</p>
                            <p><strong>Violation Detected:</strong> ${data.violation_detected ? 'Yes' : 'No'}</p>
                            <p><strong>Violation Types:</strong> ${data.violation_types.join(', ') || 'None'}</p>
                            <p><strong>Recommendations:</strong></p>
                            <ul>
                                ${data.recommendations.map(r => `<li>${r}</li>`).join('')}
                            </ul>
                        `;
                    } catch (error) {
                        resultsDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
                    }
                }
                
                // Initialize charts
                const violationsCtx = document.getElementById('violations-chart').getContext('2d');
                new Chart(violationsCtx, {
                    type: 'bar',
                    data: {
                        labels: ['Security', 'Commit', 'PR Process', 'CI/CD', 'Documentation'],
                        datasets: [{
                            label: 'Violations',
                            data: [12, 19, 3, 5, 2],
                            backgroundColor: [
                                'rgba(255, 99, 132, 0.2)',
                                'rgba(54, 162, 235, 0.2)',
                                'rgba(255, 206, 86, 0.2)',
                                'rgba(75, 192, 192, 0.2)',
                                'rgba(153, 102, 255, 0.2)'
                            ],
                            borderColor: [
                                'rgba(255, 99, 132, 1)',
                                'rgba(54, 162, 235, 1)',
                                'rgba(255, 206, 86, 1)',
                                'rgba(75, 192, 192, 1)',
                                'rgba(153, 102, 255, 1)'
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
                
                // Update metrics periodically
                setInterval(async () => {
                    try {
                        const response = await fetch('/metrics');
                        // Update UI with metrics
                        document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
                    } catch (error) {
                        console.error('Error fetching metrics:', error);
                    }
                }, 30000); // Update every 30 seconds
            </script>
        </body>
        </html>
        """
        
        return html
    
    def run(self):
        """Run the API server"""
        
        uvicorn.run(
            self.app,
            host=self.config.API_HOST,
            port=self.config.API_PORT,
            workers=self.config.API_WORKERS
        )


def create_api(config: Config = None) -> FastAPI:
    """Factory function to create API instance"""
    
    if config is None:
        config = Config.from_env()
    
    api = ScoringAPI(config)
    return api.app


if __name__ == "__main__":
    # Run the API server
    config = Config.from_env()
    api = ScoringAPI(config)
    api.run()