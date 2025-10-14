#!/bin/bash

# ============================================
# System Health Check
# Crypto Trading Signal System
# ============================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   System Health Check                     ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════╝${NC}"
echo ""

HEALTH_LOG="./logs/health_check_$(date +%Y%m%d_%H%M%S).log"
mkdir -p ./logs

echo "Health check started: $(date)" | tee -a "$HEALTH_LOG"
echo "" | tee -a "$HEALTH_LOG"

# Load environment
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

OVERALL_HEALTH=0  # 0 = healthy, 1 = warnings, 2 = critical

# ==================== DOCKER STATUS ====================

echo "🐳 Docker Status:" | tee -a "$HEALTH_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$HEALTH_LOG"

if docker info >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Docker daemon is running" | tee -a "$HEALTH_LOG"
else
    echo -e "${RED}✗${NC} Docker daemon is not running" | tee -a "$HEALTH_LOG"
    OVERALL_HEALTH=2
fi

# Docker version
DOCKER_VERSION=$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo "unknown")
echo "  Version: $DOCKER_VERSION" | tee -a "$HEALTH_LOG"

echo "" | tee -a "$HEALTH_LOG"

# ==================== CONTAINER STATUS ====================

echo "📦 Container Status:" | tee -a "$HEALTH_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$HEALTH_LOG"

CONTAINERS=(
    "mysql"
    "timescaledb"
    "redis"
    "mongodb"
    "rabbitmq"
    "api-gateway"
    "market-data-bot"
    "news-collector-bot"
    "technical-analysis-bot"
    "sentiment-analysis-bot"
    "itc-analysis-bot"
    "signal-aggregator-bot"
    "ml-learning-engine"
    "notification-bot"
    "feedback-processor-bot"
    "frontend"
    "prometheus"
    "grafana"
)

RUNNING_COUNT=0
STOPPED_COUNT=0
UNHEALTHY_COUNT=0

for container in "${CONTAINERS[@]}"; do
    STATUS=$(docker-compose ps "$container" 2>/dev/null | grep "$container" | awk '{print $NF}' || echo "not found")
    
    if [[ "$STATUS" == *"Up"* ]]; then
        echo -e "${GREEN}✓${NC} $container: Running" | tee -a "$HEALTH_LOG"
        RUNNING_COUNT=$((RUNNING_COUNT + 1))
    elif [[ "$STATUS" == *"Exit"* ]]; then
        echo -e "${RED}✗${NC} $container: Stopped" | tee -a "$HEALTH_LOG"
        STOPPED_COUNT=$((STOPPED_COUNT + 1))
        OVERALL_HEALTH=2
    else
        echo -e "${YELLOW}!${NC} $container: $STATUS" | tee -a "$HEALTH_LOG"
        UNHEALTHY_COUNT=$((UNHEALTHY_COUNT + 1))
        [ $OVERALL_HEALTH -lt 1 ] && OVERALL_HEALTH=1
    fi
done

echo "" | tee -a "$HEALTH_LOG"
echo "Summary: $RUNNING_COUNT running, $STOPPED_COUNT stopped, $UNHEALTHY_COUNT unknown" | tee -a "$HEALTH_LOG"
echo "" | tee -a "$HEALTH_LOG"

# ==================== DATABASE CONNECTIVITY ====================

echo "🗄️  Database Connectivity:" | tee -a "$HEALTH_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$HEALTH_LOG"

# MySQL
if docker-compose exec -T mysql mysqladmin ping -h localhost -u root -p${MYSQL_ROOT_PASSWORD} >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} MySQL: Connected" | tee -a "$HEALTH_LOG"
    
    # Check connections
    MYSQL_CONNECTIONS=$(docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} -s -N -e \
        "SHOW STATUS LIKE 'Threads_connected';" | awk '{print $2}')
    echo "  Active connections: $MYSQL_CONNECTIONS" | tee -a "$HEALTH_LOG"
else
    echo -e "${RED}✗${NC} MySQL: Connection failed" | tee -a "$HEALTH_LOG"
    OVERALL_HEALTH=2
fi

# TimescaleDB
if docker-compose exec -T timescaledb pg_isready -U ${TIMESCALE_USER} >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} TimescaleDB: Connected" | tee -a "$HEALTH_LOG"
    
    # Check connections
    TIMESCALE_CONNECTIONS=$(docker-compose exec -T timescaledb psql -U ${TIMESCALE_USER} -d ${TIMESCALE_DB} -t -c \
        "SELECT count(*) FROM pg_stat_activity;" | tr -d ' ')
    echo "  Active connections: $TIMESCALE_CONNECTIONS" | tee -a "$HEALTH_LOG"
else
    echo -e "${RED}✗${NC} TimescaleDB: Connection failed" | tee -a "$HEALTH_LOG"
    OVERALL_HEALTH=2
fi

# Redis
if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
    echo -e "${GREEN}✓${NC} Redis: Connected" | tee -a "$HEALTH_LOG"
    
    # Check memory
    REDIS_MEMORY=$(docker-compose exec -T redis redis-cli INFO memory | grep used_memory_human | cut -d':' -f2 | tr -d '\r ')
    echo "  Memory used: $REDIS_MEMORY" | tee -a "$HEALTH_LOG"
else
    echo -e "${RED}✗${NC} Redis: Connection failed" | tee -a "$HEALTH_LOG"
    OVERALL_HEALTH=2
fi

# MongoDB
if docker-compose exec -T mongodb mongosh --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} MongoDB: Connected" | tee -a "$HEALTH_LOG"
else
    echo -e "${RED}✗${NC} MongoDB: Connection failed" | tee -a "$HEALTH_LOG"
    OVERALL_HEALTH=2
fi

# RabbitMQ
if docker-compose exec -T rabbitmq rabbitmqctl status >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} RabbitMQ: Connected" | tee -a "$HEALTH_LOG"
    
    # Check queues
    QUEUE_COUNT=$(docker-compose exec -T rabbitmq rabbitmqctl list_queues 2>/dev/null | wc -l)
    echo "  Queues: $((QUEUE_COUNT - 2))" | tee -a "$HEALTH_LOG"
else
    echo -e "${RED}✗${NC} RabbitMQ: Connection failed" | tee -a "$HEALTH_LOG"
    OVERALL_HEALTH=2
fi

echo "" | tee -a "$HEALTH_LOG"

# ==================== API HEALTH ====================

echo "🌐 API Health:" | tee -a "$HEALTH_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$HEALTH_LOG"

# API Gateway
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/health 2>/dev/null || echo "000")
API_RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" http://localhost:3000/health 2>/dev/null || echo "0")

if [ "$API_STATUS" = "200" ]; then
    echo -e "${GREEN}✓${NC} API Gateway: Healthy (${API_RESPONSE_TIME}s)" | tee -a "$HEALTH_LOG"
else
    echo -e "${RED}✗${NC} API Gateway: Unhealthy (HTTP $API_STATUS)" | tee -a "$HEALTH_LOG"
    OVERALL_HEALTH=2
fi

# Frontend
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001 2>/dev/null || echo "000")

if [ "$FRONTEND_STATUS" = "200" ]; then
    echo -e "${GREEN}✓${NC} Frontend: Accessible" | tee -a "$HEALTH_LOG"
else
    echo -e "${RED}✗${NC} Frontend: Inaccessible (HTTP $FRONTEND_STATUS)" | tee -a "$HEALTH_LOG"
    OVERALL_HEALTH=2
fi

echo "" | tee -a "$HEALTH_LOG"

# ==================== SYSTEM RESOURCES ====================

echo "💻 System Resources:" | tee -a "$HEALTH_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$HEALTH_LOG"

# Disk space
DISK_USAGE=$(df -h . | tail -1 | awk '{print $5}' | sed 's/%//')
DISK_AVAIL=$(df -h . | tail -1 | awk '{print $4}')

if [ "$DISK_USAGE" -lt 80 ]; then
    echo -e "${GREEN}✓${NC} Disk: $DISK_USAGE% used ($DISK_AVAIL available)" | tee -a "$HEALTH_LOG"
elif [ "$DISK_USAGE" -lt 90 ]; then
    echo -e "${YELLOW}!${NC} Disk: $DISK_USAGE% used ($DISK_AVAIL available) - Consider cleanup" | tee -a "$HEALTH_LOG"
    [ $OVERALL_HEALTH -lt 1 ] && OVERALL_HEALTH=1
else
    echo -e "${RED}✗${NC} Disk: $DISK_USAGE% used ($DISK_AVAIL available) - Critical!" | tee -a "$HEALTH_LOG"
    OVERALL_HEALTH=2
fi

# Memory
if command -v free >/dev/null 2>&1; then
    MEM_USAGE=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100)}')
    MEM_AVAIL=$(free -h | grep Mem | awk '{print $7}')
    
    if [ "$MEM_USAGE" -lt 80 ]; then
        echo -e "${GREEN}✓${NC} Memory: $MEM_USAGE% used ($MEM_AVAIL available)" | tee -a "$HEALTH_LOG"
    elif [ "$MEM_USAGE" -lt 90 ]; then
        echo -e "${YELLOW}!${NC} Memory: $MEM_USAGE% used ($MEM_AVAIL available)" | tee -a "$HEALTH_LOG"
        [ $OVERALL_HEALTH -lt 1 ] && OVERALL_HEALTH=1
    else
        echo -e "${RED}✗${NC} Memory: $MEM_USAGE% used ($MEM_AVAIL available) - Critical!" | tee -a "$HEALTH_LOG"
        OVERALL_HEALTH=2
    fi
fi

# CPU Load
if command -v uptime >/dev/null 2>&1; then
    LOAD_AVG=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    echo "  CPU Load Average: $LOAD_AVG" | tee -a "$HEALTH_LOG"
fi

echo "" | tee -a "$HEALTH_LOG"

# ==================== DATA INTEGRITY ====================

echo "📊 Data Integrity:" | tee -a "$HEALTH_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$HEALTH_LOG"

# Recent signals
RECENT_SIGNALS=$(docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} -s -N -e \
    "SELECT COUNT(*) FROM signals WHERE generated_at > DATE_SUB(NOW(), INTERVAL 1 HOUR);" 2>/dev/null || echo "0")
echo "  Signals (last hour): $RECENT_SIGNALS" | tee -a "$HEALTH_LOG"

# Recent news
RECENT_NEWS=$(docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} -s -N -e \
    "SELECT COUNT(*) FROM news_articles WHERE collected_at > DATE_SUB(NOW(), INTERVAL 1 HOUR);" 2>/dev/null || echo "0")
echo "  News articles (last hour): $RECENT_NEWS" | tee -a "$HEALTH_LOG"

# Price data freshness
LATEST_PRICE=$(docker-compose exec -T timescaledb psql -U ${TIMESCALE_USER} -d ${TIMESCALE_DB} -t -c \
    "SELECT EXTRACT(EPOCH FROM (NOW() - MAX(time)))::integer FROM price_data;" 2>/dev/null | tr -d ' ' || echo "999999")
if [ "$LATEST_PRICE" -lt 300 ]; then  # 5 minutes
    echo -e "${GREEN}✓${NC} Price data: Fresh (${LATEST_PRICE}s ago)" | tee -a "$HEALTH_LOG"
elif [ "$LATEST_PRICE" -lt 600 ]; then  # 10 minutes
    echo -e "${YELLOW}!${NC} Price data: Stale (${LATEST_PRICE}s ago)" | tee -a "$HEALTH_LOG"
    [ $OVERALL_HEALTH -lt 1 ] && OVERALL_HEALTH=1
else
    echo -e "${RED}✗${NC} Price data: Very stale (${LATEST_PRICE}s ago)" | tee -a "$HEALTH_LOG"
    OVERALL_HEALTH=2
fi

echo "" | tee -a "$HEALTH_LOG"

# ==================== BOT PERFORMANCE ====================

echo "🤖 Bot Performance:" | tee -a "$HEALTH_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$HEALTH_LOG"

# Get bot health from database
BOT_HEALTH=$(docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} -t -e \
    "SELECT bot_name, status, TIMESTAMPDIFF(MINUTE, last_heartbeat, NOW()) AS 'Minutes Since Heartbeat', error_rate \
     FROM bot_health WHERE checked_at > DATE_SUB(NOW(), INTERVAL 10 MINUTE) ORDER BY bot_name;" 2>/dev/null || echo "No data")
if [ "$BOT_HEALTH" != "No data" ]; then
    echo "$BOT_HEALTH" | tee -a "$HEALTH_LOG"
else
    echo -e "${YELLOW}!${NC} No recent bot health data available" | tee -a "$HEALTH_LOG"
    [ $OVERALL_HEALTH -lt 1 ] && OVERALL_HEALTH=1
fi

echo "" | tee -a "$HEALTH_LOG"

# ==================== RECENT ERRORS ====================

echo "⚠️  Recent Errors:" | tee -a "$HEALTH_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$HEALTH_LOG"

ERROR_COUNT=$(docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} -s -N -e \
    "SELECT COUNT(*) FROM system_events WHERE severity IN ('ERROR', 'CRITICAL') \
     AND created_at > DATE_SUB(NOW(), INTERVAL 1 HOUR);" 2>/dev/null || echo "0")
if [ "$ERROR_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓${NC} No errors in the last hour" | tee -a "$HEALTH_LOG"
elif [ "$ERROR_COUNT" -lt 10 ]; then
    echo -e "${YELLOW}!${NC} $ERROR_COUNT errors in the last hour" | tee -a "$HEALTH_LOG"
    [ $OVERALL_HEALTH -lt 1 ] && OVERALL_HEALTH=1

    # Show recent errors
    docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} -t -e \
        "SELECT DATE_FORMAT(created_at, '%H:%i:%s') AS 'Time', source_bot AS 'Bot', LEFT(message, 50) AS 'Error Message' \
         FROM system_events WHERE severity IN ('ERROR', 'CRITICAL') \
         AND created_at > DATE_SUB(NOW(), INTERVAL 1 HOUR) ORDER BY created_at DESC LIMIT 5;" 2>/dev/null | tee -a "$HEALTH_LOG"
else
    echo -e "${RED}✗${NC} $ERROR_COUNT errors in the last hour - Critical!" | tee -a "$HEALTH_LOG"
    OVERALL_HEALTH=2

    # Show recent errors
    docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} -t -e \
        "SELECT DATE_FORMAT(created_at, '%H:%i:%s') AS 'Time', source_bot AS 'Bot', LEFT(message, 50) AS 'Error Message' \
         FROM system_events WHERE severity IN ('ERROR', 'CRITICAL') \
         AND created_at > DATE_SUB(NOW(), INTERVAL 1 HOUR) ORDER BY created_at DESC LIMIT 10;" 2>/dev/null | tee -a "$HEALTH_LOG"
fi

echo "" | tee -a "$HEALTH_LOG"

# ==================== SIGNAL QUALITY ====================

echo "📈 Signal Quality (Last 24h):" | tee -a "$HEALTH_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$HEALTH_LOG"

SIGNAL_STATS=$(docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} -t -e \
    "SELECT COUNT(*) AS 'Total Signals', \
            COUNT(CASE WHEN final_confidence >= 80 THEN 1 END) AS 'High Confidence (>=80%)', \
            ROUND(AVG(final_confidence), 2) AS 'Avg Confidence', \
            ROUND(AVG(risk_reward_ratio), 2) AS 'Avg RR Ratio' \
     FROM signals WHERE generated_at > DATE_SUB(NOW(), INTERVAL 24 HOUR);" 2>/dev/null || echo "No data")
if [ "$SIGNAL_STATS" != "No data" ]; then
    echo "$SIGNAL_STATS" | tee -a "$HEALTH_LOG"
else
    echo -e "${YELLOW}!${NC} No signal data available" | tee -a "$HEALTH_LOG"
    [ $OVERALL_HEALTH -lt 1 ] && OVERALL_HEALTH=1
fi

echo "" | tee -a "$HEALTH_LOG"

# ==================== BACKUP STATUS ====================

echo "💾 Backup Status:" | tee -a "$HEALTH_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$HEALTH_LOG"

if [ -d "./backups" ]; then
    LATEST_BACKUP=$(ls -1t ./backups | grep "^20" | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        BACKUP_AGE=$(find "./backups/$LATEST_BACKUP" -maxdepth 0 -mtime 0 2>/dev/null)
        
        if [ -n "$BACKUP_AGE" ]; then
            echo -e "${GREEN}✓${NC} Latest backup: $LATEST_BACKUP (today)" | tee -a "$HEALTH_LOG"
        else
            DAYS_OLD=$(find "./backups/$LATEST_BACKUP" -maxdepth 0 -mtime +1 -printf '%Cd\n' 2>/dev/null || echo "unknown")
            if [ "$DAYS_OLD" != "unknown" ] && [ "$DAYS_OLD" -lt 7 ]; then
                echo -e "${YELLOW}!${NC} Latest backup: $LATEST_BACKUP ($DAYS_OLD days ago)" | tee -a "$HEALTH_LOG"
                [ $OVERALL_HEALTH -lt 1 ] && OVERALL_HEALTH=1
            else
                echo -e "${RED}✗${NC} Latest backup: $LATEST_BACKUP (very old!)" | tee -a "$HEALTH_LOG"
                OVERALL_HEALTH=2
            fi
        fi
        
        BACKUP_COUNT=$(ls -1 ./backups | grep "^20" | wc -l)
        echo "  Total backups: $BACKUP_COUNT" | tee -a "$HEALTH_LOG"
    else
        echo -e "${RED}✗${NC} No backups found!" | tee -a "$HEALTH_LOG"
        OVERALL_HEALTH=2
    fi
else
    echo -e "${RED}✗${NC} Backup directory not found!" | tee -a "$HEALTH_LOG"
    OVERALL_HEALTH=2
fi

echo "" | tee -a "$HEALTH_LOG"

# ==================== NETWORK CONNECTIVITY ====================

echo "🌐 Network Connectivity:" | tee -a "$HEALTH_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$HEALTH_LOG"

# Test Binance API
if curl -s --max-time 5 https://api.binance.com/api/v3/ping >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Binance API: Reachable" | tee -a "$HEALTH_LOG"
else
    echo -e "${RED}✗${NC} Binance API: Unreachable" | tee -a "$HEALTH_LOG"
    OVERALL_HEALTH=2
fi

# Test internet connectivity
if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Internet: Connected" | tee -a "$HEALTH_LOG"
else
    echo -e "${RED}✗${NC} Internet: No connectivity" | tee -a "$HEALTH_LOG"
    OVERALL_HEALTH=2
fi

echo "" | tee -a "$HEALTH_LOG"

# ==================== SECURITY CHECKS ====================

echo "🔒 Security Status:" | tee -a "$HEALTH_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$HEALTH_LOG"

# Check if .env is not in git
if [ -d .git ]; then
    if git ls-files --error-unmatch .env >/dev/null 2>&1; then
        echo -e "${RED}✗${NC} .env file is tracked by git!" | tee -a "$HEALTH_LOG"
        OVERALL_HEALTH=2
    else
        echo -e "${GREEN}✓${NC} .env file is not tracked by git" | tee -a "$HEALTH_LOG"
    fi
fi

# Check file permissions
ENV_PERMS=$(stat -c %a .env 2>/dev/null || echo "000")
if [ "$ENV_PERMS" = "600" ] || [ "$ENV_PERMS" = "400" ]; then
    echo -e "${GREEN}✓${NC} .env file permissions: $ENV_PERMS (secure)" | tee -a "$HEALTH_LOG"
else
    echo -e "${YELLOW}!${NC} .env file permissions: $ENV_PERMS (recommend 600)" | tee -a "$HEALTH_LOG"
    [ $OVERALL_HEALTH -lt 1 ] && OVERALL_HEALTH=1
fi

# Check for default passwords
if grep -q "your_secure_password" .env 2>/dev/null || grep -q "change_this" .env 2>/dev/null; then
    echo -e "${RED}✗${NC} Default passwords detected in .env!" | tee -a "$HEALTH_LOG"
    OVERALL_HEALTH=2
else
    echo -e "${GREEN}✓${NC} No default passwords detected" | tee -a "$HEALTH_LOG"
fi

echo "" | tee -a "$HEALTH_LOG"

# ==================== MONITORING STATUS ====================

echo "📊 Monitoring Status:" | tee -a "$HEALTH_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$HEALTH_LOG"

# Check Prometheus
PROM_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9090/-/healthy 2>/dev/null || echo "000")
if [ "$PROM_STATUS" = "200" ]; then
    echo -e "${GREEN}✓${NC} Prometheus: Running" | tee -a "$HEALTH_LOG"
else
    echo -e "${YELLOW}!${NC} Prometheus: Not accessible" | tee -a "$HEALTH_LOG"
    [ $OVERALL_HEALTH -lt 1 ] && OVERALL_HEALTH=1
fi

# Check Grafana
GRAFANA_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3002/api/health 2>/dev/null || echo "000")
if [ "$GRAFANA_STATUS" = "200" ]; then
    echo -e "${GREEN}✓${NC} Grafana: Running" | tee -a "$HEALTH_LOG"
else
    echo -e "${YELLOW}!${NC} Grafana: Not accessible" | tee -a "$HEALTH_LOG"
    [ $OVERALL_HEALTH -lt 1 ] && OVERALL_HEALTH=1
fi

echo "" | tee -a "$HEALTH_LOG"

# ==================== RECOMMENDATIONS ====================

echo "💡 Recommendations:" | tee -a "$HEALTH_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$HEALTH_LOG"

if [ $OVERALL_HEALTH -eq 0 ]; then
    echo "  • System is healthy! Keep monitoring regularly" | tee -a "$HEALTH_LOG"
    echo "  • Consider running optimization: ./scripts/maintenance/optimize_database.sh" | tee -a "$HEALTH_LOG"
elif [ $OVERALL_HEALTH -eq 1 ]; then
    echo "  • Address warnings to prevent potential issues" | tee -a "$HEALTH_LOG"
    echo "  • Review logs for warning details" | tee -a "$HEALTH_LOG"
    echo "  • Run cleanup if disk space is low: ./scripts/maintenance/cleanup_old_data.sh" | tee -a "$HEALTH_LOG"
else
    echo "  ⚠️  CRITICAL ISSUES DETECTED!" | tee -a "$HEALTH_LOG"
    echo "  • Investigate failed services immediately" | tee -a "$HEALTH_LOG"
    echo "  • Check logs: docker-compose logs -f" | tee -a "$HEALTH_LOG"
    echo "  • Restart services: docker-compose restart" | tee -a "$HEALTH_LOG"
    echo "  • If issues persist, consider rollback: ./scripts/deployment/rollback.sh" | tee -a "$HEALTH_LOG"
fi

echo "" | tee -a "$HEALTH_LOG"

# ==================== HEALTH SUMMARY ====================

echo "═══════════════════════════════════════════" | tee -a "$HEALTH_LOG"
if [ $OVERALL_HEALTH -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}" | tee -a "$HEALTH_LOG"
    echo -e "${GREEN}║   ✓ System Health: HEALTHY                ║${NC}" | tee -a "$HEALTH_LOG"
    echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}" | tee -a "$HEALTH_LOG"
elif [ $OVERALL_HEALTH -eq 1 ]; then
    echo -e "${YELLOW}╔════════════════════════════════════════════╗${NC}" | tee -a "$HEALTH_LOG"
    echo -e "${YELLOW}║   ! System Health: WARNINGS                ║${NC}" | tee -a "$HEALTH_LOG"
    echo -e "${YELLOW}╚════════════════════════════════════════════╝${NC}" | tee -a "$HEALTH_LOG"
else
    echo -e "${RED}╔════════════════════════════════════════════╗${NC}" | tee -a "$HEALTH_LOG"
    echo -e "${RED}║   ✗ System Health: CRITICAL                ║${NC}" | tee -a "$HEALTH_LOG"
    echo -e "${RED}╚════════════════════════════════════════════╝${NC}" | tee -a "$HEALTH_LOG"
fi

echo "" | tee -a "$HEALTH_LOG"
echo "Health check completed: $(date)" | tee -a "$HEALTH_LOG"
echo "Full report: $HEALTH_LOG" | tee -a "$HEALTH_LOG"
echo "" | tee -a "$HEALTH_LOG"

# Send notification if critical
if [ $OVERALL_HEALTH -eq 2 ] && [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -d chat_id="${TELEGRAM_CHAT_ID}" \
        -d text="🚨 CRITICAL: System health check failed!%0ACheck logs: $HEALTH_LOG%0ATime: $(date)" \
        >/dev/null 2>&1
fi