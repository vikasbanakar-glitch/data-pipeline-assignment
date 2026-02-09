#!/bin/bash

# Startup script for Product Pricing Pipeline
# This script helps set up and start the entire pipeline

set -e

echo "================================================"
echo "  Product Pricing Intelligence Pipeline Setup"
echo "================================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✓ Docker and Docker Compose are installed"
echo ""

# Create necessary directories
echo "Creating required directories..."
mkdir -p logs
mkdir -p config
echo "✓ Directories created"
echo ""

# Set Airflow UID
export AIRFLOW_UID=$(id -u)
echo "✓ Set AIRFLOW_UID=$AIRFLOW_UID"
echo ""

# Start services
echo "Starting services (this may take a few minutes)..."
echo ""
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service status
echo ""
echo "Service Status:"
docker-compose ps

echo ""
echo "================================================"
echo "  🎉 Pipeline is starting up!"
echo "================================================"
echo ""
echo "Access Airflow UI:"
echo "  URL:      http://localhost:8080"
echo "  Username: admin"
echo "  Password: admin"
echo ""
echo "Access PostgreSQL:"
echo "  Host:     localhost"
echo "  Port:     5432"
echo "  Database: pipeline_db"
echo "  Username: pipeline_user"
echo "  Password: pipeline_pass"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop services:"
echo "  docker-compose down"
echo ""
echo "To run tests:"
echo "  docker-compose exec airflow-scheduler python /opt/airflow/test_pipeline.py"
echo ""
echo "================================================"
echo "  Next Steps:"
echo "================================================"
echo "1. Wait 2-3 minutes for Airflow to fully initialize"
echo "2. Open http://localhost:8080 in your browser"
echo "3. Find the 'product_pricing_pipeline' DAG"
echo "4. Toggle it ON and click 'Trigger DAG'"
echo ""
