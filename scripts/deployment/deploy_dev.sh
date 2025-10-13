#!/bin/bash

# ============================================
# scripts/setup/deploy_dev.sh
# Deploy to Development Environment
# Crypto Trading Signal System
# ============================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Deploying to Development                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}✗${NC} .env file not found"
    echo "Run: ./scripts/setup/generate_env_files.sh"
    exit 1
fi

# Load environment
export $(cat .env | grep -v '^#' | xargs)

echo "Environment: ${NODE_ENV:-development}"
echo "Deployment time: $(date)"
echo ""

# ==================== PRE-DEPLOYMENT CHECKS ====================

echo "🔍 Running pre-deployment checks..."
echo ""

# Check Docker
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}✗${NC} Docker is not running"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker is running"

# Check disk space
AVAILABLE_SPACE=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$AVAILABLE_SPACE" -lt 5 ]; then
    echo -e "${RED}✗${NC} Insufficient disk space: ${AVAILABLE_SPACE}GB"
    exit 1
fi
echo -e "${GREEN}✓${NC} Sufficient disk space: ${AVAILABLE_SPACE}GB"

# Check if ports are available
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}!${NC} Port $1 is already in use"
        return 1
    else
        echo -e "${GREEN}✓${NC} Port $1 is available"
        return 0
    fi
}

check_port 3000 || true
check_port 3001 || true
check_port 3306 || true
check_port 5432 || true

echo ""

# ==================== BACKUP CURRENT STATE ====================

echo "💾 Creating backup before deployment..."
if [ -d "./backups" ]; then
    ./scripts/backup/backup_database.sh || echo -e "${YELLOW}!${NC} Backup skipped"
fi
echo ""

# ==================== PULL LATEST CODE ====================

echo "📥 Pulling latest code..."
if [ -d .git ]; then
    git fetch origin
    git pull origin main || git pull origin master || echo -e "${YELLOW}!${NC} Git pull skipped"
    echo -e "${GREEN}✓${NC} Code updated"
else
    echo -e "${YELLOW}!${NC} Not a git repository, skipping pull"
fi
echo ""

# ==================== STOP CURRENT SERVICES ====================

echo "🛑 Stopping current services..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down || true
echo -e "${GREEN}✓${NC} Services stopped"
echo ""

# ==================== BUILD IMAGES ====================

echo "🔨 Building Docker images..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --no-cache
echo -e "${GREEN}✓${NC} Images built"
echo ""

# ==================== START DATABASES ====================

echo "🗄️  Starting databases..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d \
    mysql timescaledb redis mongodb rabbitmq

echo "⏳ Waiting for databases..."
sleep 20

# Health check for databases
echo -n "Checking database health: "
for i in {1..30}; do
    if docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec -T mysql \
        mysqladmin ping -h localhost -u root -p${MYSQL_ROOT_PASSWORD} >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        break
    fi
    echo -n "."
    sleep 2
done
echo ""

# ==================== RUN MIGRATIONS ====================

echo "🔄 Running database migrations..."
if [ -d "./database/migrations" ]; then
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml run --rm \
        api-gateway npm run migration:run || echo -e "${YELLOW}!${NC} Migrations skipped"
    echo -e "${GREEN}✓${NC} Migrations completed"
fi
echo ""

# ==================== START ALL SERVICES ====================

echo "🚀 Starting all services..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

echo "⏳ Waiting for services to start..."
sleep 15
echo ""

# ==================== HEALTH CHECKS ====================

echo "🏥 Running health checks..."
echo ""

# Check API Gateway
API_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/health || echo "000")
if [ "$API_HEALTH" = "200" ]; then
    echo -e "${GREEN}✓${NC} API Gateway: Healthy"
else
    echo -e "${YELLOW}!${NC} API Gateway: Unhealthy (HTTP $API_HEALTH)"
fi

# Check Frontend
FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001 || echo "000")
if [ "$FRONTEND_HEALTH" = "200" ]; then
    echo -e "${GREEN}✓${NC} Frontend: Healthy"
else
    echo -e "${YELLOW}!${NC} Frontend: Unhealthy (HTTP $FRONTEND_HEALTH)"
fi

# Check RabbitMQ
RABBITMQ_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" \
    -u ${RABBITMQ_USER}:${RABBITMQ_PASSWORD} \
    http://localhost:15672/api/healthchecks/node || echo "000")
if [ "$RABBITMQ_HEALTH" = "200" ]; then
    echo -e "${GREEN}✓${NC} RabbitMQ: Healthy"
else
    echo -e "${YELLOW}!${NC} RabbitMQ: Unhealthy"
fi

echo ""

# ==================== CHECK RUNNING SERVICES ====================

echo "📊 Service Status:"
docker-compose -f docker-compose.yml -f docker-compose.dev.yml ps
echo ""

# ==================== INSTALL/UPDATE DEPENDENCIES ====================

echo "📦 Updating dependencies..."

# Frontend
if [ -d "./frontend" ]; then
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec -T frontend \
        npm install || echo -e "${YELLOW}!${NC} Frontend dependencies skipped"
fi

# Backend
if [ -d "./backend/api-gateway" ]; then
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec -T api-gateway \
        npm install || echo -e "${YELLOW}!${NC} Backend dependencies skipped"
fi

echo -e "${GREEN}✓${NC} Dependencies updated"
echo ""

# ==================== SEED DATA (OPTIONAL) ====================

read -p "Load seed data for development? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "./database/seeds/seed_data.sql" ]; then
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec -T mysql \
            mysql -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} \
            < ./database/seeds/seed_data.sql
        echo -e "${GREEN}✓${NC} Seed data loaded"
    fi
fi
echo ""

# ==================== DEPLOYMENT SUMMARY ====================

echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Development Deployment Complete!        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo "🌐 Application URLs:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Dashboard:        http://localhost:3001"
echo "  API:              http://localhost:3000"
echo "  API Docs:         http://localhost:3000/api/docs"
echo "  RabbitMQ:         http://localhost:15672"
echo "  Grafana:          http://localhost:3002"
echo "  Adminer:          http://localhost:8080"
echo "  Redis Commander:  http://localhost:8081"
echo "  Mailhog:          http://localhost:8025"
echo ""
echo "📝 Useful Commands:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  View logs:        docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f"
echo "  Stop services:    docker-compose -f docker-compose.yml -f docker-compose.dev.yml down"
echo "  Restart service:  docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart <service>"
echo "  Run tests:        docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec api-gateway npm test"
echo ""
echo "🐛 Debugging:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  API Gateway debugger: ws://localhost:9229"
echo "  Python bots debugger: localhost:5678-5686"
echo "  Jupyter notebooks:    http://localhost:8888"
echo ""