"""
Scheduler for automated ML pipeline tasks
"""

import logging
import signal
import sys
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .config import Config
from .continuous_learning import ContinuousLearningPipeline
from .data_collector import GitHubDataCollector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MLPipelineScheduler:
    """Scheduler for ML pipeline tasks"""
    
    def __init__(self, config: Config):
        self.config = config
        self.scheduler = BlockingScheduler()
        self.pipeline = ContinuousLearningPipeline(config)
        self.data_collector = GitHubDataCollector(config)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.scheduler.shutdown(wait=False)
        sys.exit(0)
    
    def setup_jobs(self):
        """Setup scheduled jobs"""
        
        # Data collection job - runs every hour
        self.scheduler.add_job(
            func=self.collect_data,
            trigger=IntervalTrigger(hours=1),
            id='collect_data',
            name='Collect GitHub data',
            replace_existing=True,
            max_instances=1
        )
        
        # Model retraining job - runs weekly on Sunday at 2 AM
        self.scheduler.add_job(
            func=self.retrain_models,
            trigger=CronTrigger(day_of_week='sun', hour=2, minute=0),
            id='retrain_models',
            name='Retrain ML models',
            replace_existing=True,
            max_instances=1
        )
        
        # Drift detection job - runs daily at midnight
        self.scheduler.add_job(
            func=self.check_drift,
            trigger=CronTrigger(hour=0, minute=0),
            id='check_drift',
            name='Check model drift',
            replace_existing=True,
            max_instances=1
        )
        
        # Performance monitoring job - runs every 6 hours
        self.scheduler.add_job(
            func=self.monitor_performance,
            trigger=IntervalTrigger(hours=6),
            id='monitor_performance',
            name='Monitor model performance',
            replace_existing=True,
            max_instances=1
        )
        
        # Cleanup job - runs daily at 3 AM
        self.scheduler.add_job(
            func=self.cleanup_old_data,
            trigger=CronTrigger(hour=3, minute=0),
            id='cleanup',
            name='Cleanup old data',
            replace_existing=True,
            max_instances=1
        )
        
        logger.info("Scheduled jobs configured:")
        for job in self.scheduler.get_jobs():
            logger.info(f"  - {job.name}: {job.trigger}")
    
    def collect_data(self):
        """Collect data from GitHub"""
        try:
            logger.info("Starting data collection...")
            
            # Collect organization data
            df = self.data_collector.collect_organization_data(
                days_back=self.config.FEATURE_WINDOW_DAYS
            )
            
            if not df.empty:
                # Save to feature store
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                filename = f"org_data_{timestamp}.parquet"
                filepath = f"{self.config.FEATURE_STORE_PATH}/raw/{filename}"
                df.to_parquet(filepath)
                logger.info(f"Collected data for {len(df)} repositories")
            else:
                logger.warning("No data collected")
                
        except Exception as e:
            logger.error(f"Error in data collection: {e}")
    
    def retrain_models(self):
        """Retrain ML models"""
        try:
            logger.info("Starting model retraining...")
            result = self.pipeline.retrain_models()
            logger.info(f"Retraining completed with status: {result['status']}")
            
            # Log performance metrics
            if 'validation_performance' in result:
                perf = result['validation_performance']
                logger.info(f"Model performance: {perf}")
                
        except Exception as e:
            logger.error(f"Error in model retraining: {e}")
    
    def check_drift(self):
        """Check for model drift"""
        try:
            logger.info("Checking for model drift...")
            drift_results = self.pipeline.check_model_drift()
            
            if drift_results['drift_detected']:
                logger.warning(f"Drift detected with score: {drift_results['drift_score']}")
                
                # Send alert
                self._send_alert(
                    "Model Drift Detected",
                    f"Drift score: {drift_results['drift_score']}"
                )
            else:
                logger.info("No significant drift detected")
                
        except Exception as e:
            logger.error(f"Error in drift detection: {e}")
    
    def monitor_performance(self):
        """Monitor model performance"""
        try:
            logger.info("Monitoring model performance...")
            performance = self.pipeline.monitor_performance()
            
            logger.info(f"Performance metrics: {performance}")
            
            # Check for performance degradation
            if performance.get('violation_detection_rate', 1) < 0.1:
                self._send_alert(
                    "Low Detection Rate",
                    "Violation detection rate is below threshold"
                )
            
            if performance.get('false_positive_rate', 0) > 0.2:
                self._send_alert(
                    "High False Positive Rate",
                    "False positive rate exceeds threshold"
                )
                
        except Exception as e:
            logger.error(f"Error in performance monitoring: {e}")
    
    def cleanup_old_data(self):
        """Clean up old data files"""
        try:
            logger.info("Cleaning up old data...")
            
            import os
            from datetime import timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            # Clean raw data
            raw_path = f"{self.config.FEATURE_STORE_PATH}/raw"
            if os.path.exists(raw_path):
                for filename in os.listdir(raw_path):
                    filepath = os.path.join(raw_path, filename)
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    
                    if file_time < cutoff_date:
                        os.remove(filepath)
                        logger.info(f"Removed old file: {filename}")
            
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.error(f"Error in cleanup: {e}")
    
    def _send_alert(self, subject: str, message: str):
        """Send alert notification"""
        try:
            # In production, this would send actual alerts (email, Slack, etc.)
            logger.warning(f"ALERT - {subject}: {message}")
            
            # Log to file for monitoring
            with open("alerts.log", "a") as f:
                f.write(f"{datetime.utcnow().isoformat()} - {subject}: {message}\n")
                
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
    
    def run(self):
        """Start the scheduler"""
        logger.info("Starting ML Pipeline Scheduler...")
        
        # Setup jobs
        self.setup_jobs()
        
        # Start scheduler
        try:
            logger.info("Scheduler is running. Press Ctrl+C to exit.")
            self.scheduler.start()
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            sys.exit(1)


def main():
    """Main entry point"""
    config = Config.from_env()
    scheduler = MLPipelineScheduler(config)
    scheduler.run()


if __name__ == "__main__":
    main()