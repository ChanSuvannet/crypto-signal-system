
#!/bin/bash

# ============================================
# scripts/setup/cleanup_old_data.sh
# Cleanup Old Data
# Crypto Trading Signal System
# ============================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Data Cleanup                            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Load environment
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

CLEANUP_LOG="./logs/cleanup_$(date +%Y%m%d_%H%M%S).log"
mkdir -p ./logs

echo "Cleanup started: $(date)" | tee -a "$CLEANUP_LOG"
echo "" | tee -a "$CLEANUP_LOG"

# ==================== CONFIGURATION ====================

# Data retention periods (in days)
SIGNAL_RETENTION=${SIGNAL_RETENTION:-90}
NEWS_RETENTION=${NEWS_RETENTION:-60}
PRICE_DATA_RETENTION=${PRICE_DATA_RETENTION:-180}
LOG_RETENTION=${LOG_RETENTION:-30}
BACKUP_RETENTION=${BACKUP_RETENTION:-30}
PERFORMANCE_RETENTION=${PERFORMANCE_RETENTION:-365}

echo "📋 Cleanup Configuration:" | tee -a "$CLEANUP_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$CLEANUP_LOG"
echo "  Signals:         Keep last ${SIGNAL_RETENTION} days" | tee -a "$CLEANUP_LOG"
echo "  News:            Keep last ${NEWS_RETENTION} days" | tee -a "$CLEANUP_LOG"
echo "  Price Data:      Keep last ${PRICE_DATA_RETENTION} days" | tee -a "$CLEANUP_LOG"
echo "  Logs:            Keep last ${LOG_RETENTION} days" | tee -a "$CLEANUP_LOG"
echo "  Backups:         Keep last ${BACKUP_RETENTION} days" | tee -a "$CLEANUP_LOG"
echo "  Performance:     Keep last ${PERFORMANCE_RETENTION} days" | tee -a "$CLEANUP_LOG"
echo "" | tee -a "$CLEANUP_LOG"

# Confirmation
read -p "Continue with cleanup? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled"
    exit 0
fi
echo ""

# ==================== BACKUP BEFORE CLEANUP ====================

echo "💾 Creating backup before cleanup..." | tee -a "$CLEANUP_LOG"
./scripts/backup/backup_database.sh
echo "" | tee -a "$CLEANUP_LOG"

# ==================== CLEAN MYSQL DATA ====================

echo "🗄️  Cleaning MySQL data..." | tee -a "$CLEANUP_LOG"

# Clean old signals
echo "Cleaning old signals..." | tee -a "$CLEANUP_LOG"
DELETED_SIGNALS=$(docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
    ${MYSQL_DATABASE} -s -N -e \
    "DELETE FROM signals WHERE generated_at < DATE_SUB(NOW(), INTERVAL ${SIGNAL_RETENTION} DAY); SELECT ROW_COUNT();")
echo "  Deleted signals: $DELETED_SIGNALS" | tee -a "$CLEANUP_LOG"

# Clean old signal outcomes
echo "Cleaning old signal outcomes..." | tee -a "$CLEANUP_LOG"
DELETED_OUTCOMES=$(docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
    ${MYSQL_DATABASE} -s -N -e \
    "DELETE FROM signal_outcomes WHERE created_at < DATE_SUB(NOW(), INTERVAL ${SIGNAL_RETENTION} DAY); SELECT ROW_COUNT();")
echo "  Deleted outcomes: $DELETED_OUTCOMES" | tee -a "$CLEANUP_LOG"

# Clean old news
echo "Cleaning old news..." | tee -a "$CLEANUP_LOG"
DELETED_NEWS=$(docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
    ${MYSQL_DATABASE} -s -N -e \
    "DELETE FROM news_articles WHERE collected_at < DATE_SUB(NOW(), INTERVAL ${NEWS_RETENTION} DAY); SELECT ROW_COUNT();")
echo "  Deleted news articles: $DELETED_NEWS" | tee -a "$CLEANUP_LOG"

# Clean old system events
echo "Cleaning old system events..." | tee -a "$CLEANUP_LOG"
DELETED_EVENTS=$(docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
    ${MYSQL_DATABASE} -s -N -e \
    "DELETE FROM system_events WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY); SELECT ROW_COUNT();")
echo "  Deleted events: $DELETED_EVENTS" | tee -a "$CLEANUP_LOG"

# Clean old API usage logs
echo "Cleaning old API usage logs..." | tee -a "$CLEANUP_LOG"
DELETED_API_LOGS=$(docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
    ${MYSQL_DATABASE} -s -N -e \
    "DELETE FROM api_usage WHERE requested_at < DATE_SUB(NOW(), INTERVAL 7 DAY); SELECT ROW_COUNT();")
echo "  Deleted API logs: $DELETED_API_LOGS" | tee -a "$CLEANUP_LOG"

# Clean expired patterns
echo "Cleaning expired patterns..." | tee -a "$CLEANUP_LOG"
DELETED_PATTERNS=$(docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
    ${MYSQL_DATABASE} -s -N -e \
    "DELETE FROM detected_patterns WHERE detected_at < DATE_SUB(NOW(), INTERVAL 60 DAY); SELECT ROW_COUNT();")
echo "  Deleted patterns: $DELETED_PATTERNS" | tee -a "$CLEANUP_LOG"

# Clean old bot performance data (keep aggregated)
echo "Cleaning old bot performance data..." | tee -a "$CLEANUP_LOG"
DELETED_PERF=$(docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
    ${MYSQL_DATABASE} -s -N -e \
    "DELETE FROM bot_performance WHERE date < DATE_SUB(CURDATE(), INTERVAL ${PERFORMANCE_RETENTION} DAY); SELECT ROW_COUNT();")
echo "  Deleted performance records: $DELETED_PERF" | tee -a "$CLEANUP_LOG"

echo -e "${GREEN}✓${NC} MySQL cleanup complete" | tee -a "$CLEANUP_LOG"
echo "" | tee -a "$CLEANUP_LOG"

# ==================== CLEAN TIMESCALEDB DATA ====================

echo "📈 Cleaning TimescaleDB data..." | tee -a "$CLEANUP_LOG"

# Clean old price data (1-minute data)
echo "Cleaning old 1-minute price data..." | tee -a "$CLEANUP_LOG"
docker-compose exec -T timescaledb psql -U ${TIMESCALE_USER} -d ${TIMESCALE_DB} -c \
    "DELETE FROM price_data WHERE timeframe = '1m' AND time < NOW() - INTERVAL '${PRICE_DATA_RETENTION} days';" \
    2>&1 | tee -a "$CLEANUP_LOG"

# Clean old indicator data
echo "Cleaning old indicator data..." | tee -a "$CLEANUP_LOG"
docker-compose exec -T timescaledb psql -U ${TIMESCALE_USER} -d ${TIMESCALE_DB} -c \
    "DELETE FROM realtime_indicators WHERE time < NOW() - INTERVAL '${PRICE_DATA_RETENTION} days';" \
    2>&1 | tee -a "$CLEANUP_LOG"

# Clean old orderbook snapshots
echo "Cleaning old orderbook snapshots..." | tee -a "$CLEANUP_LOG"
docker-compose exec -T timescaledb psql -U ${TIMESCALE_USER} -d ${TIMESCALE_DB} -c \
    "DELETE FROM orderbook_snapshots WHERE time < NOW() - INTERVAL '7 days';" \
    2>&1 | tee -a "$CLEANUP_LOG"

echo -e "${GREEN}✓${NC} TimescaleDB cleanup complete" | tee -a "$CLEANUP_LOG"
echo "" | tee -a "$CLEANUP_LOG"

# ==================== CLEAN MONGODB DATA ====================

echo "🍃 Cleaning MongoDB data..." | tee -a "$CLEANUP_LOG"

# Clean old ML model versions (keep last 10 versions per model)
echo "Cleaning old ML model versions..." | tee -a "$CLEANUP_LOG"
docker-compose exec -T mongodb mongosh ${MONGO_DATABASE} \
    --username ${MONGO_USER} --password ${MONGO_PASSWORD} --quiet --eval "
    db.ml_models.aggregate([
        { \$sort: { model_name: 1, deployed_at: -1 } },
        { \$group: { _id: '\$model_name', versions: { \$push: '\$\$ROOT' } } },
        { \$project: { toDelete: { \$slice: ['\$versions', 10, 1000] } } }
    ]).forEach(function(doc) {
        doc.toDelete.forEach(function(model) {
            db.ml_models.deleteOne({ _id: model._id });
        });
    });
    print('Cleaned old ML models');
" 2>&1 | tee -a "$CLEANUP_LOG"

echo -e "${GREEN}✓${NC} MongoDB cleanup complete" | tee -a "$CLEANUP_LOG"
echo "" | tee -a "$CLEANUP_LOG"

# ==================== CLEAN REDIS CACHE ====================

echo "💎 Cleaning Redis cache..." | tee -a "$CLEANUP_LOG"

# Flush expired keys (Redis does this automatically, but we can trigger it)
docker-compose exec -T redis redis-cli SAVE >/dev/null 2>&1

# Get cache info
REDIS_KEYS=$(docker-compose exec -T redis redis-cli DBSIZE | grep -oE '[0-9]+')
REDIS_MEMORY=$(docker-compose exec -T redis redis-cli INFO memory | grep used_memory_human | cut -d':' -f2 | tr -d '\r')

echo "  Redis keys: $REDIS_KEYS" | tee -a "$CLEANUP_LOG"
echo "  Redis memory: $REDIS_MEMORY" | tee -a "$CLEANUP_LOG"

echo -e "${GREEN}✓${NC} Redis cleanup complete" | tee -a "$CLEANUP_LOG"
echo "" | tee -a "$CLEANUP_LOG"

# ==================== CLEAN LOG FILES ====================

echo "📝 Cleaning log files..." | tee -a "$CLEANUP_LOG"

# Clean old application logs
find ./logs -name "*.log" -mtime +${LOG_RETENTION} -delete 2>/dev/null || true
find ./backend/bots/*/logs -name "*.log" -mtime +${LOG_RETENTION} -delete 2>/dev/null || true

echo -e "${GREEN}✓${NC} Log files cleaned" | tee -a "$CLEANUP_LOG"
echo "" | tee -a "$CLEANUP_LOG"

# ==================== CLEAN OLD BACKUPS ====================

echo "💾 Cleaning old backups..." | tee -a "$CLEANUP_LOG"

BACKUP_COUNT_BEFORE=$(find ./backups -type d -name "20*" | wc -l)
find ./backups -type d -name "20*" -mtime +${BACKUP_RETENTION} -exec rm -rf {} + 2>/dev/null || true
BACKUP_COUNT_AFTER=$(find ./backups -type d -name "20*" | wc -l)

echo "  Backups before: $BACKUP_COUNT_BEFORE" | tee -a "$CLEANUP_LOG"
echo "  Backups after:  $BACKUP_COUNT_AFTER" | tee -a "$CLEANUP_LOG"
echo "  Deleted:        $((BACKUP_COUNT_BEFORE - BACKUP_COUNT_AFTER))" | tee -a "$CLEANUP_LOG"

echo -e "${GREEN}✓${NC} Backup cleanup complete" | tee -a "$CLEANUP_LOG"
echo "" | tee -a "$CLEANUP_LOG"

# ==================== CLEAN DOCKER ====================

echo "🐳 Cleaning Docker resources..." | tee -a "$CLEANUP_LOG"

# Remove unused images
docker image prune -af --filter "until=720h" 2>&1 | tee -a "$CLEANUP_LOG"

# Remove unused volumes
docker volume prune -f 2>&1 | tee -a "$CLEANUP_LOG"

# Remove build cache
docker builder prune -af --filter "until=720h" 2>&1 | tee -a "$CLEANUP_LOG"

echo -e "${GREEN}✓${NC} Docker cleanup complete" | tee -a "$CLEANUP_LOG"
echo "" | tee -a "$CLEANUP_LOG"

# ==================== DISK SPACE REPORT ====================

echo "💿 Disk Space Report:" | tee -a "$CLEANUP_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$CLEANUP_LOG"

df -h . | tee -a "$CLEANUP_LOG"

echo "" | tee -a "$CLEANUP_LOG"

# Database sizes
echo "Database Sizes:" | tee -a "$CLEANUP_LOG"
docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} -e \
    "SELECT table_schema AS 'Database', 
     ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)' 
     FROM information_schema.tables 
     WHERE table_schema = '${MYSQL_DATABASE}' 
     GROUP BY table_schema;" | tee -a "$CLEANUP_LOG"

echo "" | tee -a "$CLEANUP_LOG"

# ==================== CLEANUP SUMMARY ====================

echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}" | tee -a "$CLEANUP_LOG"
echo -e "${GREEN}║   Cleanup Complete!                        ║${NC}" | tee -a "$CLEANUP_LOG"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}" | tee -a "$CLEANUP_LOG"
echo "" | tee -a "$CLEANUP_LOG"

echo "📊 Cleanup Statistics:" | tee -a "$CLEANUP_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$CLEANUP_LOG"
echo "  Signals deleted:          $DELETED_SIGNALS" | tee -a "$CLEANUP_LOG"
echo "  News articles deleted:    $DELETED_NEWS" | tee -a "$CLEANUP_LOG"
echo "  Events deleted:           $DELETED_EVENTS" | tee -a "$CLEANUP_LOG"
echo "  Backups removed:          $((BACKUP_COUNT_BEFORE - BACKUP_COUNT_AFTER))" | tee -a "$CLEANUP_LOG"
echo "" | tee -a "$CLEANUP_LOG"
echo "  Cleanup completed: $(date)" | tee -a "$CLEANUP_LOG"
echo "  Log file: $CLEANUP_LOG" | tee -a "$CLEANUP_LOG"
echo "" | tee -a "$CLEANUP_LOG"