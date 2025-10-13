#!/bin/bash

# ============================================
# Start the system
# ============================================

set -e

echo "🚀 Starting Crypto Trading Signal System..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please run ./scripts/setup.sh first"
    exit 1
fi

# Start services
docker-compose up -d

echo "✅ System started successfully!"
echo ""
echo "View logs: docker-compose logs -f"