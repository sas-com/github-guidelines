#!/bin/bash

# Deployment script for ML Pipeline
set -e

echo "🚀 Starting GitHub Violation Detection ML Pipeline Deployment"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker is not installed${NC}"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}Docker Compose is not installed${NC}"
        exit 1
    fi
    
    # Check GitHub token
    if [ -z "$GITHUB_TOKEN" ]; then
        echo -e "${RED}GITHUB_TOKEN environment variable is not set${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ All prerequisites met${NC}"
}

# Create necessary directories
setup_directories() {
    echo -e "${YELLOW}Setting up directories...${NC}"
    
    mkdir -p models
    mkdir -p feature_store/raw
    mkdir -p feature_store/features
    mkdir -p logs
    mkdir -p grafana/dashboards
    mkdir -p grafana/datasources
    
    echo -e "${GREEN}✓ Directories created${NC}"
}

# Generate configuration files
generate_configs() {
    echo -e "${YELLOW}Generating configuration files...${NC}"
    
    # Create .env file if not exists
    if [ ! -f .env ]; then
        cat > .env << EOF
GITHUB_TOKEN=${GITHUB_TOKEN}
GITHUB_ORG=sas-com
ML_PIPELINE_API_PORT=8000
ML_PIPELINE_LOG_LEVEL=INFO
EOF
        echo -e "${GREEN}✓ .env file created${NC}"
    fi
    
    # Create Prometheus configuration
    cat > prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'ml-api'
    static_configs:
      - targets: ['ml-api:8000']
    metrics_path: '/metrics'
EOF
    
    # Create Grafana datasource configuration
    cat > grafana/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF
    
    # Create database initialization script
    cat > init.sql << EOF
-- Initialize GitHub ML Database

CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    prediction_id VARCHAR(255) UNIQUE NOT NULL,
    repository VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    violation_detected BOOLEAN,
    violation_types TEXT[],
    risk_scores JSONB,
    anomaly_score FLOAT,
    recommendations TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_predictions_repository ON predictions(repository);
CREATE INDEX idx_predictions_timestamp ON predictions(timestamp);

CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    prediction_id VARCHAR(255) REFERENCES predictions(prediction_id),
    was_correct BOOLEAN,
    correct_label VARCHAR(255),
    feedback_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS model_performance (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    accuracy FLOAT,
    f1_score FLOAT,
    precision FLOAT,
    recall FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS training_runs (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(255) UNIQUE NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    status VARCHAR(50),
    metrics JSONB,
    parameters JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
EOF
    
    echo -e "${GREEN}✓ Configuration files generated${NC}"
}

# Build Docker images
build_images() {
    echo -e "${YELLOW}Building Docker images...${NC}"
    
    docker-compose build --no-cache
    
    echo -e "${GREEN}✓ Docker images built${NC}"
}

# Start services
start_services() {
    echo -e "${YELLOW}Starting services...${NC}"
    
    docker-compose up -d
    
    echo -e "${GREEN}✓ Services started${NC}"
}

# Wait for services to be ready
wait_for_services() {
    echo -e "${YELLOW}Waiting for services to be ready...${NC}"
    
    # Wait for API
    echo -n "Waiting for API..."
    until curl -f http://localhost:8000/health &>/dev/null; do
        echo -n "."
        sleep 2
    done
    echo -e " ${GREEN}Ready${NC}"
    
    # Wait for Postgres
    echo -n "Waiting for PostgreSQL..."
    until docker-compose exec -T postgres pg_isready &>/dev/null; do
        echo -n "."
        sleep 2
    done
    echo -e " ${GREEN}Ready${NC}"
    
    echo -e "${GREEN}✓ All services are ready${NC}"
}

# Train initial models
train_models() {
    echo -e "${YELLOW}Training initial models...${NC}"
    
    # Run training script
    docker-compose exec -T ml-api python -c "
from ml_pipeline.continuous_learning import ContinuousLearningPipeline
from ml_pipeline.config import Config

config = Config.from_env()
pipeline = ContinuousLearningPipeline(config)
result = pipeline.retrain_models(force=True)
print('Training result:', result['status'])
"
    
    echo -e "${GREEN}✓ Initial models trained${NC}"
}

# Show status
show_status() {
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment Successful!${NC}"
    echo -e "${GREEN}========================================${NC}\n"
    
    echo "Services are running at:"
    echo "  • API:        http://localhost:8000"
    echo "  • Dashboard:  http://localhost:8000/dashboard"
    echo "  • Grafana:    http://localhost:3000 (admin/admin)"
    echo "  • Prometheus: http://localhost:9090"
    echo ""
    echo "API Documentation: http://localhost:8000/docs"
    echo ""
    echo "To view logs:"
    echo "  docker-compose logs -f ml-api"
    echo ""
    echo "To stop services:"
    echo "  docker-compose down"
    echo ""
}

# Main deployment flow
main() {
    echo ""
    check_prerequisites
    setup_directories
    generate_configs
    build_images
    start_services
    wait_for_services
    
    # Optional: train models
    read -p "Do you want to train initial models? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        train_models
    fi
    
    show_status
}

# Handle errors
trap 'echo -e "\n${RED}Deployment failed!${NC}"; exit 1' ERR

# Run main function
main