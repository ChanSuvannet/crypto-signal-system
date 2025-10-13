#!/bin/bash

# ============================================
# Rollback Deployment
# Crypto Trading Signal System
# ============================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${YELLOW}╔════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║   DEPLOYMENT ROLLBACK                     ║${NC}"
echo -e "${YELLOW}╚════════════════════════════════════════════╝${NC}"
echo ""

DEPLOYMENT_ID=${1:-"latest"}
ROLLBACK_LOG="./logs/rollback_$(date +%Y%m%d_%H%M%S).log"

mkdir -p ./logs

echo "Rollback started: $(date)" | tee -a "$ROLLBACK_LOG"
echo "Target deployment: $DEPLOYMENT_ID" | tee -a "$ROLLBACK_LOG"
echo "" | tee -a "$ROLLBACK_LOG"

# ==================== CONFIRMATION ====================

echo -e "${RED}⚠️  WARNING: You are about to rollback the deployment${NC}"
echo ""
read -p "Are you sure you want to rollback? (yes/no) " -r
if [[ ! $REPLY =~ ^yes$ ]]; then
    echo "Rollback cancelled"
    exit 0
fi
echo ""

# ==================== FIND BACKUP ====================

echo "🔍 Looking for backup..." | tee -a "$ROLLBACK_LOG"

if [ "$DEPLOYMENT_ID" = "latest" ]; then
    # Find the most recent backup
    BACKUP_DIR=$(ls -td ./backups/pre_deploy_* 2>/dev/null | head -1)
else
    BACKUP_DIR="./backups/pre_deploy_${DEPLOYMENT_ID}"
fi

if [ -z "$BACKUP_DIR" ] || [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}✗${NC} Backup not found: $BACKUP_DIR" | tee -a "$ROLLBACK_LOG"
    exit 1
fi

echo -e "${GREEN}✓${NC} Found backup: $BACKUP_DIR" | tee -a "$ROLLBACK_LOG"
echo "" | tee -a "$ROLLBACK_LOG"

# ==================== STOP CURRENT SERVICES ====================

echo "🛑 Stopping current services..." | tee -a "$ROLLBACK_LOG"
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down 2>&1 | tee -a "$ROLLBACK_LOG"
echo -e "${GREEN}✓${NC} Services stopped" | tee -a "$ROLLBACK_LOG"
echo "" | tee -a "$ROLLBACK_LOG"

# ==================== RESTORE CONFIGURATION ====================

echo "🔧 Restoring configuration..." | tee -a "$ROLLBACK_LOG"

if [ -f "$BACKUP_DIR/.env.production.backup" ]; then
    cp "$BACKUP_DIR/.env.production.backup" .env.production
    echo -e "${GREEN}✓${NC} Configuration restored" | tee -a "$ROLLBACK_LOG"
else
    echo -e "${YELLOW}!${NC} Configuration backup not found" | tee -a "$ROLLBACK_LOG"
fi

echo "" | tee -a "$ROLLBACK_LOG"

# ==================== RESTORE DATABASES ====================

echo "💾 Restoring databases..." | tee -a "$ROLLBACK_LOG"

# Start databases
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d \
    mysql timescaledb mongodb

echo "⏳ Waiting for databases to be ready..."
sleep 20

# Load environment
if [ -f .env.production ]; then
    export $(cat .env.production | grep -v '^#' | xargs)
fi

# Restore MySQL
if [ -f "$BACKUP_DIR/mysql_backup.sql" ]; then
    echo "Restoring MySQL database..." | tee -a "$ROLLBACK_LOG"
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec -T mysql \
        mysql -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} \
        < "$BACKUP_DIR/mysql_backup.sql" 2>&1 | tee -a "$ROLLBACK_LOG"
    echo -e "${GREEN}✓${NC} MySQL restored" | tee -a "$ROLLBACK_LOG"
else
    echo -e "${YELLOW}!${NC} MySQL backup not found" | tee -a "$ROLLBACK_LOG"
fi

# Restore TimescaleDB
if [ -f "$BACKUP_DIR/timescale_backup.sql" ]; then
    echo "Restoring TimescaleDB..." | tee -a "$ROLLBACK_LOG"
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec -T timescaledb \
        psql -U ${TIMESCALE_USER} ${TIMESCALE_DB} \
        < "$BACKUP_DIR/timescale_backup.sql" 2>&1 | tee -a "$ROLLBACK_LOG"
    echo -e "${GREEN}✓${NC} TimescaleDB restored" | tee -a "$ROLLBACK_LOG"
else
    echo -e "${YELLOW}!${NC} TimescaleDB backup not found" | tee -a "$ROLLBACK_LOG"
fi

# Restore MongoDB
if [ -f "$BACKUP_DIR/mongodb_backup.archive" ]; then
    echo "Restoring MongoDB..." | tee -a "$ROLLBACK_LOG"
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec -T mongodb \
        mongorestore --username=${MONGO_USER} --password=${MONGO_PASSWORD} \
        --db=${MONGO_DATABASE} --archive \
        < "$BACKUP_DIR/mongodb_backup.archive" 2>&1 | tee -a "$ROLLBACK_LOG"
    echo -e "${GREEN}✓${NC} MongoDB restored" | tee -a "$ROLLBACK_LOG"
else
    echo -e "${YELLOW}!${NC} MongoDB backup not found" | tee -a "$ROLLBACK_LOG"
fi

echo "" | tee -a "$ROLLBACK_LOG"

# ==================== RESTORE DOCKER IMAGES ====================

echo "🐳 Restoring Docker images..." | tee -a "$ROLLBACK_LOG"

# Get previous image tags from backup
if [ -f "$BACKUP_DIR/docker-compose-snapshot.yml" ]; then
    # Use the snapshot to pull old images
    docker-compose -f "$BACKUP_DIR/docker-compose-snapshot.yml" pull 2>&1 | tee -a "$ROLLBACK_LOG"
    echo -e "${GREEN}✓${NC} Docker images restored" | tee -a "$ROLLBACK_LOG"
else
    echo -e "${YELLOW}!${NC} Docker compose snapshot not found, using current images" | tee -a "$ROLLBACK_LOG"
fi

echo "" | tee -a "$ROLLBACK_LOG"

# ==================== START SERVICES ====================

echo "🚀 Starting services with previous version..." | tee -a "$ROLLBACK_LOG"

if [ -f "$BACKUP_DIR/docker-compose-snapshot.yml" ]; then
    docker-compose -f "$BACKUP_DIR/docker-compose-snapshot.yml" up -d 2>&1 | tee -a "$ROLLBACK_LOG"
else
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d 2>&1 | tee -a "$ROLLBACK_LOG"
fi

echo "⏳ Waiting for services to start..."
sleep 30
echo "" | tee -a "$ROLLBACK_LOG"

# ==================== HEALTH CHECKS ====================

echo "🏥 Running health checks..." | tee -a "$ROLLBACK_LOG"
echo "" | tee -a "$ROLLBACK_LOG"

ALL_HEALTHY=true

# Check API Gateway
API_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/health || echo "000")
if [ "$API_HEALTH" = "200" ]; then
    echo -e "${GREEN}✓${NC} API Gateway: Healthy" | tee -a "$ROLLBACK_LOG"
else
    echo -e "${RED}✗${NC} API Gateway: Unhealthy (HTTP $API_HEALTH)" | tee -a "$ROLLBACK_LOG"
    ALL_HEALTHY=false
fi

# Check Frontend
FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001 || echo "000")
if [ "$FRONTEND_HEALTH" = "200" ]; then
    echo -e "${GREEN}✓${NC} Frontend: Healthy" | tee -a "$ROLLBACK_LOG"
else
    echo -e "${RED}✗${NC} Frontend: Unhealthy (HTTP $FRONTEND_HEALTH)" | tee -a "$ROLLBACK_LOG"
    ALL_HEALTHY=false
fi

# Check Database connectivity
if docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec -T mysql \
    mysqladmin ping -h localhost -u root -p${MYSQL_ROOT_PASSWORD} >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} MySQL: Connected" | tee -a "$ROLLBACK_LOG"
else
    echo -e "${RED}✗${NC} MySQL: Connection failed" | tee -a "$ROLLBACK_LOG"
    ALL_HEALTHY=false
fi

echo "" | tee -a "$ROLLBACK_LOG"

# ==================== VERIFY DATA INTEGRITY ====================

echo "🔍 Verifying data integrity..." | tee -a "$ROLLBACK_LOG"

# Check MySQL tables
TABLE_COUNT=$(docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec -T mysql \
    mysql -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} \
    -e "SHOW TABLES;" | wc -l)
echo "MySQL tables: $((TABLE_COUNT - 1))" | tee -a "$ROLLBACK_LOG"

# Check recent signals
SIGNAL_COUNT=$(docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec -T mysql \
    mysql -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} -s -N \
    -e "SELECT COUNT(*) FROM signals WHERE generated_at > DATE_SUB(NOW(), INTERVAL 24 HOUR);")
echo "Signals (last 24h): $SIGNAL_COUNT" | tee -a "$ROLLBACK_LOG"

echo "" | tee -a "$ROLLBACK_LOG"

# ==================== ROLLBACK SUMMARY ====================

if [ "$ALL_HEALTHY" = true ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}" | tee -a "$ROLLBACK_LOG"
    echo -e "${GREEN}║   Rollback Completed Successfully!         ║${NC}" | tee -a "$ROLLBACK_LOG"
    echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}" | tee -a "$ROLLBACK_LOG"
else
    echo -e "${RED}╔════════════════════════════════════════════╗${NC}" | tee -a "$ROLLBACK_LOG"
    echo -e "${RED}║   Rollback Completed with Issues           ║${NC}" | tee -a "$ROLLBACK_LOG"
    echo -e "${RED}╚════════════════════════════════════════════╝${NC}" | tee -a "$ROLLBACK_LOG"
fi

echo "" | tee -a "$ROLLBACK_LOG"
echo "📋 Rollback Summary:" | tee -a "$ROLLBACK_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$ROLLBACK_LOG"
echo "  Completed:        $(date)" | tee -a "$ROLLBACK_LOG"
echo "  Restored from:    $BACKUP_DIR" | tee -a "$ROLLBACK_LOG"
echo "  Log file:         $ROLLBACK_LOG" | tee -a "$ROLLBACK_LOG"
echo "" | tee -a "$ROLLBACK_LOG"

echo "📝 Next Steps:" | tee -a "$ROLLBACK_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$ROLLBACK_LOG"
echo "  ☐ Monitor application logs" | tee -a "$ROLLBACK_LOG"
echo "  ☐ Verify all services are functioning" | tee -a "$ROLLBACK_LOG"
echo "  ☐ Check data integrity" | tee -a "$ROLLBACK_LOG"
echo "  ☐ Investigate root cause of deployment issue" | tee -a "$ROLLBACK_LOG"
echo "  ☐ Notify team of rollback" | tee -a "$ROLLBACK_LOG"
echo "" | tee -a "$ROLLBACK_LOG"

# Send rollback notification
if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -d chat_id="${TELEGRAM_CHAT_ID}" \
        -d text="⚠️ Deployment rollback completed%0ARestored from: ${BACKUP_DIR}%0ATime: $(date)" \
        >/dev/null 2>&1
fi