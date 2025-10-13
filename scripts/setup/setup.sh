#!/bin/bash

# ============================================
# Crypto Trading Signal System - Setup Script
# ============================================

set -e  # Exit on error

echo "🚀 Setting up Crypto Trading Signal System..."

# Check prerequisites
echo "📋 Checking prerequisites..."

command -v docker >/dev/null 2>&1 || { echo "❌ Docker is not installed. Please install Docker first."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is not installed. Please install Docker Compose first."; exit 1; }

echo "✅ Prerequisites check passed"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys and configuration"
    echo "   Run: nano .env"
    exit 0
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p backend/bots/{market-data-bot,news-collector-bot,technical-analysis-bot,sentiment-analysis-bot,itc-analysis-bot,signal-aggregator-bot,ml-learning-engine,notification-bot,feedback-processor-bot}/logs
mkdir -p backend/bots/ml-learning-engine/{models,notebooks}
mkdir -p infrastructure/nginx/ssl

# Build Docker images
echo "🔨 Building Docker images..."
docker-compose build

# Start databases first
echo "🗄️  Starting databases..."
docker-compose up -d mysql timescaledb redis mongodb rabbitmq

# Wait for databases to be ready
echo "⏳ Waiting for databases to be ready..."
sleep 30

# Run database migrations
echo "🔄 Running database migrations..."
docker-compose run --rm api-gateway npm run migration:run

# Start all services
echo "🚀 Starting all services..."
docker-compose up -d

# Show status
echo ""
echo "✅ Setup complete!"
echo ""
echo "📊 Service URLs:"
echo "   Dashboard:    http://localhost:3001"
echo "   API:          http://localhost:3000"
echo "   API Docs:     http://localhost:3000/api/docs"
echo "   RabbitMQ UI:  http://localhost:15672 (user: rabbitmq_user)"
echo "   Grafana:      http://localhost:3002 (user: admin)"
echo ""
echo "📝 View logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Stop services:"
echo "   docker-compose down"
echo ""