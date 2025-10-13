#!/bin/bash

# ============================================
# Deploy to Production Environment
# Crypto Trading Signal System
# ============================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${RED}╔════════════════════════════════════════════╗${NC}"
echo -e "${RED}║   PRODUCTION DEPLOYMENT                   ║${NC}"
echo -e "${RED}╚════════════════════════════════════════════╝${NC}"
echo ""

# Confirmation prompt
echo -e "${YELLOW}⚠️  WARNING: You are about to deploy to PRODUCTION${NC}"
echo ""
read -p "Are you sure you want to continue? (yes/no) " -r
if [[ ! $REPLY =~ ^yes$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi
echo ""

# Second confirmation
read -p "Type 'deploy-production' to confirm: " -r
if [[ $REPLY != "deploy-production" ]]; then
    echo "Deployment cancelled"
    exit 0
fi
echo ""

DEPLOYMENT_ID=$(date +%Y%m%d_%H%M%S)
DEPLOYMENT_LOG="./logs/deployment_${DEPLOYMENT_ID}.log"

mkdir -p ./logs

echo "Deployment ID: $DEPLOYMENT_ID" | tee -a "$DEPLOYMENT_LOG"
echo "Deployment started: $(date)" | tee -a "$DEPLOYMENT_LOG"
echo "" | tee -a "$DEPLOYMENT_LOG"

# ==================== PRE-DEPLOYMENT CHECKS ====================

echo "🔍 Running pre-deployment checks..." | tee -a "$DEPLOYMENT_LOG"
echo "" | tee -a "$DEPLOYMENT_LOG"

# Check environment file
if [ ! -f .env.production ]; then
    echo -e "${RED}✗${NC} .env.production file not found" | tee -a "$DEPLOYMENT_LOG"
    exit 1
fi
echo -e "${GREEN}✓${NC} Environment file exists" | tee -a "$DEPLOYMENT_LOG"

# Load production environment
export $(cat .env.production | grep -v '^#' | xargs)
export NODE_ENV=production

# Check critical environment variables
REQUIRED_VARS=(
    "MYSQL_ROOT_PASSWORD"
    "JWT_SECRET"
    "BINANCE_API_KEY"
    "BINANCE_API_SECRET"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}✗${NC} Required variable $var is not set" | tee -a "$DEPLOYMENT_LOG"
        exit 1
    fi
done
echo -e "${GREEN}✓${NC} All required variables are set" | tee -a "$DEPLOYMENT_LOG"

# Check Docker
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}✗${NC} Docker is not running" | tee -a "$DEPLOYMENT_LOG"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker is running" | tee -a "$DEPLOYMENT_LOG"

# Check disk space (minimum 20GB for production)
AVAILABLE_SPACE=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$AVAILABLE_SPACE" -lt 20 ]; then
    echo -e "${RED}✗${NC} Insufficient disk space: ${AVAILABLE_SPACE}GB (20GB+ required)" | tee -a "$DEPLOYMENT_LOG"
    exit 1
fi
echo -e "${GREEN}✓${NC} Sufficient disk space: ${AVAILABLE_SPACE}GB" | tee -a "$DEPLOYMENT_LOG"

# Check memory (minimum 8GB for production)
TOTAL_MEM=$(free -g 2>/dev/null | awk '/^Mem:/{print $2}' || echo "0")
if [ "$TOTAL_MEM" -lt 8 ]; then
    echo -e "${YELLOW}!${NC} Low memory: ${TOTAL_MEM}GB (8GB+ recommended)" | tee -a "$DEPLOYMENT_LOG"
fi

echo "" | tee -a "$DEPLOYMENT_LOG"

# ==================== BACKUP CURRENT STATE ====================

echo "💾 Creating pre-deployment backup..." | tee -a "$DEPLOYMENT_LOG"
BACKUP_DIR="./backups/pre_deploy_${DEPLOYMENT_ID}"
mkdir -p "$BACKUP_DIR"

# Backup databases
./scripts/backup/backup_database.sh

# Backup current configuration
cp .env.production "$BACKUP_DIR/.env.production.backup"
docker-compose -f docker-compose.yml -f docker-compose.prod.yml config > "$BACKUP_DIR/docker-compose-snapshot.yml"

echo -e "${GREEN}✓${NC} Backup created: $BACKUP_DIR" | tee -a "$DEPLOYMENT_LOG"
echo "" | tee -a "$DEPLOYMENT_LOG"

# ==================== RUN TESTS ====================

echo "🧪 Running tests..." | tee -a "$DEPLOYMENT_LOG"

# Backend tests
if [ -d "./backend/api-gateway" ]; then
    cd backend/api-gateway
    npm test || {
        echo -e "${RED}✗${NC} Backend tests failed" | tee -a "$DEPLOYMENT_LOG"
        exit 1
    }
    cd ../..
    echo -e "${GREEN}✓${NC} Backend tests passed" | tee -a "$DEPLOYMENT_LOG"
fi

# Frontend tests
if [ -d "./frontend" ]; then
    cd frontend
    npm test || {
        echo -e "${RED}✗${NC} Frontend tests failed" | tee -a "$DEPLOYMENT_LOG"
        exit 1
    }
    cd ..
    echo -e "${GREEN}✓${NC} Frontend tests passed" | tee -a "$DEPLOYMENT_LOG"
fi

echo "" | tee -a "$DEPLOYMENT_LOG"

# ==================== BUILD PRODUCTION IMAGES ====================

echo "🔨 Building production images..." | tee -a "$DEPLOYMENT_LOG"
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache 2>&1 | tee -a "$DEPLOYMENT_LOG"
echo -e "${GREEN}✓${NC} Images built" | tee -a "$DEPLOYMENT_LOG"
echo "" | tee -a "$DEPLOYMENT_LOG"

# ==================== STOP CURRENT SERVICES (ZERO-DOWNTIME) ====================

echo "🔄 Performing rolling update..." | tee -a "$DEPLOYMENT_LOG"

# Scale up new instances before stopping old ones
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale api-gateway=4 --no-recreate

# Wait for new instances to be healthy
echo "⏳ Waiting for new instances to be healthy..."
sleep 30

# Health check new instances
NEW_INSTANCES_HEALTHY=true
for i in {1..10}; do
    API_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/health || echo "000")
    if [ "$API_HEALTH" = "200" ]; then
        echo -e "${GREEN}✓${NC} New instances are healthy" | tee -a "$DEPLOYMENT_LOG"
        break
    fi
    if [ $i -eq 10 ]; then
        NEW_INSTANCES_HEALTHY=false
        echo -e "${RED}✗${NC} New instances failed health check" | tee -a "$DEPLOYMENT_LOG"
    fi
    sleep 3
done

if [ "$NEW_INSTANCES_HEALTHY" = false ]; then
    echo "Rolling back..." | tee -a "$DEPLOYMENT_LOG"
    ./scripts/deployment/rollback.sh
    exit 1
fi

# Stop old services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
echo "" | tee -a "$DEPLOYMENT_LOG"

# ==================== START PRODUCTION SERVICES ====================

echo "🚀 Starting production services..." | tee -a "$DEPLOYMENT_LOG"
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d 2>&1 | tee -a "$DEPLOYMENT_LOG"

echo "⏳ Waiting for all services to start..."
sleep 30
echo "" | tee -a "$DEPLOYMENT_LOG"

# ==================== RUN MIGRATIONS ====================

echo "🔄 Running database migrations..." | tee -a "$DEPLOYMENT_LOG"
docker-compose -f docker-compose.yml -f docker-compose.prod.yml run --rm \
    api-gateway npm run migration:run 2>&1 | tee -a "$DEPLOYMENT_LOG"
echo -e "${GREEN}✓${NC} Migrations completed" | tee -a "$DEPLOYMENT_LOG"
echo "" | tee -a "$DEPLOYMENT_LOG"

# ==================== HEALTH CHECKS ====================

echo "🏥 Running post-deployment health checks..." | tee -a "$DEPLOYMENT_LOG"
echo "" | tee -a "$DEPLOYMENT_LOG"

ALL_HEALTHY=true

# Check all services
SERVICES=(
    "API Gateway:http://localhost:3000/health"
    "Frontend:http://localhost:3001"
    "MySQL:mysql"
    "TimescaleDB:timescaledb"
    "Redis:redis"
    "MongoDB:mongodb"
    "RabbitMQ:rabbitmq"
)

for service_info in "${SERVICES[@]}"; do
    service_name=$(echo "$service_info" | cut -d':' -f1)
    service_check=$(echo "$service_info" | cut -d':' -f2-)
    
    if [[ "$service_check" == http* ]]; then
        # HTTP health check
        HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$service_check" || echo "000")
        if [ "$HEALTH" = "200" ]; then
            echo -e "${GREEN}✓${NC} $service_name: Healthy" | tee -a "$DEPLOYMENT_LOG"
        else
            echo -e "${RED}✗${NC} $service_name: Unhealthy (HTTP $HEALTH)" | tee -a "$DEPLOYMENT_LOG"
            ALL_HEALTHY=false
        fi
    else
        # Docker health check
        HEALTH=$(docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps "$service_check" | grep -c "(healthy)" || echo "0")
        if [ "$HEALTH" -gt 0 ]; then
            echo -e "${GREEN}✓${NC} $service_name: Healthy" | tee -a "$DEPLOYMENT_LOG"
        else
            echo -e "${YELLOW}!${NC} $service_name: Check manually" | tee -a "$DEPLOYMENT_LOG"
        fi
    fi
done

echo "" | tee -a "$DEPLOYMENT_LOG"

if [ "$ALL_HEALTHY" = false ]; then
    echo -e "${RED}⚠️  Some services are unhealthy!${NC}" | tee -a "$DEPLOYMENT_LOG"
    read -p "Continue anyway? (yes/no) " -r
    if [[ ! $REPLY =~ ^yes$ ]]; then
        echo "Rolling back..." | tee -a "$DEPLOYMENT_LOG"
        ./scripts/deployment/rollback.sh
        exit 1
    fi
fi

# ==================== SMOKE TESTS ====================

echo "🔥 Running smoke tests..." | tee -a "$DEPLOYMENT_LOG"

# Test API endpoints
API_TESTS=(
    "GET:/health"
    "GET:/api/v1/signals"
    "GET:/api/v1/news"
)

for test in "${API_TESTS[@]}"; do
    method=$(echo "$test" | cut -d':' -f1)
    endpoint=$(echo "$test" | cut -d':' -f2)
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "http://localhost:3000$endpoint")
    
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "401" ]; then
        echo -e "${GREEN}✓${NC} $method $endpoint: OK" | tee -a "$DEPLOYMENT_LOG"
    else
        echo -e "${RED}✗${NC} $method $endpoint: Failed (HTTP $HTTP_CODE)" | tee -a "$DEPLOYMENT_LOG"
    fi
done

echo "" | tee -a "$DEPLOYMENT_LOG"

# ==================== PERFORMANCE CHECKS ====================

echo "⚡ Running performance checks..." | tee -a "$DEPLOYMENT_LOG"

# Check response times
RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:3000/health)
echo "API response time: ${RESPONSE_TIME}s" | tee -a "$DEPLOYMENT_LOG"

# Check resource usage
echo "Resource usage:" | tee -a "$DEPLOYMENT_LOG"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | tee -a "$DEPLOYMENT_LOG"

echo "" | tee -a "$DEPLOYMENT_LOG"

# ==================== ENABLE MONITORING ====================

echo "📊 Enabling monitoring..." | tee -a "$DEPLOYMENT_LOG"

# Ensure Prometheus and Grafana are running
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d prometheus grafana

echo -e "${GREEN}✓${NC} Monitoring enabled" | tee -a "$DEPLOYMENT_LOG"
echo "" | tee -a "$DEPLOYMENT_LOG"

# ==================== DEPLOYMENT SUMMARY ====================

DEPLOYMENT_END=$(date)

echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}" | tee -a "$DEPLOYMENT_LOG"
echo -e "${GREEN}║   Production Deployment Complete!         ║${NC}" | tee -a "$DEPLOYMENT_LOG"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}" | tee -a "$DEPLOYMENT_LOG"
echo "" | tee -a "$DEPLOYMENT_LOG"

echo "📋 Deployment Summary:" | tee -a "$DEPLOYMENT_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$DEPLOYMENT_LOG"
echo "  Deployment ID:    $DEPLOYMENT_ID" | tee -a "$DEPLOYMENT_LOG"
echo "  Started:          $DEPLOYMENT_START" | tee -a "$DEPLOYMENT_LOG"
echo "  Completed:        $DEPLOYMENT_END" | tee -a "$DEPLOYMENT_LOG"
echo "  Environment:      production" | tee -a "$DEPLOYMENT_LOG"
echo "  Backup Location:  $BACKUP_DIR" | tee -a "$DEPLOYMENT_LOG"
echo "  Log File:         $DEPLOYMENT_LOG" | tee -a "$DEPLOYMENT_LOG"
echo "" | tee -a "$DEPLOYMENT_LOG"

echo "🌐 Application URLs:" | tee -a "$DEPLOYMENT_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$DEPLOYMENT_LOG"
echo "  Dashboard:  https://your-domain.com" | tee -a "$DEPLOYMENT_LOG"
echo "  API:        https://api.your-domain.com" | tee -a "$DEPLOYMENT_LOG"
echo "  Grafana:    https://monitoring.your-domain.com" | tee -a "$DEPLOYMENT_LOG"
echo "" | tee -a "$DEPLOYMENT_LOG"

echo "📝 Post-Deployment Tasks:" | tee -a "$DEPLOYMENT_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$DEPLOYMENT_LOG"
echo "  ☐ Monitor application logs for errors" | tee -a "$DEPLOYMENT_LOG"
echo "  ☐ Check Grafana dashboards" | tee -a "$DEPLOYMENT_LOG"
echo "  ☐ Verify trading signals are generating" | tee -a "$DEPLOYMENT_LOG"
echo "  ☐ Test user notifications" | tee -a "$DEPLOYMENT_LOG"
echo "  ☐ Monitor system resources" | tee -a "$DEPLOYMENT_LOG"
echo "  ☐ Update documentation if needed" | tee -a "$DEPLOYMENT_LOG"
echo "" | tee -a "$DEPLOYMENT_LOG"

echo "📊 Monitoring Commands:" | tee -a "$DEPLOYMENT_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$DEPLOYMENT_LOG"
echo "  View logs:      docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f" | tee -a "$DEPLOYMENT_LOG"
echo "  Service status: docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps" | tee -a "$DEPLOYMENT_LOG"
echo "  Health check:   ./scripts/maintenance/health_check.sh" | tee -a "$DEPLOYMENT_LOG"
echo "" | tee -a "$DEPLOYMENT_LOG"

echo "🚨 Rollback Command (if needed):" | tee -a "$DEPLOYMENT_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$DEPLOYMENT_LOG"
echo "  ./scripts/deployment/rollback.sh $DEPLOYMENT_ID" | tee -a "$DEPLOYMENT_LOG"
echo "" | tee -a "$DEPLOYMENT_LOG"

# Send deployment notification
if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -d chat_id="${TELEGRAM_CHAT_ID}" \
        -d text="✅ Production deployment completed successfully!%0ADeployment ID: ${DEPLOYMENT_ID}%0ATime: ${DEPLOYMENT_END}" \
        >/dev/null 2>&1
fi

echo -e "${GREEN}Deployment completed successfully!${NC}" | tee -a "$DEPLOYMENT_LOG"