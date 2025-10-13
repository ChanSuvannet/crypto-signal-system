#!/bin/bash

# ============================================
# scripts/setup/generate_env_files.sh
# Generate Environment Files
# Crypto Trading Signal System
# ============================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Environment File Generator               ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""

# Function to generate random password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Function to generate JWT secret
generate_jwt_secret() {
    openssl rand -hex 64
}

# Check if .env already exists
if [ -f .env ]; then
    echo -e "${YELLOW}!${NC} .env file already exists"
    read -p "Overwrite existing .env file? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled"
        exit 0
    fi
    # Backup existing .env
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo -e "${GREEN}✓${NC} Backed up existing .env file"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Environment Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Select environment
echo "Select environment:"
echo "1) Development"
echo "2) Staging"
echo "3) Production"
read -p "Choice (1-3): " env_choice

case $env_choice in
    1) NODE_ENV="development" ;;
    2) NODE_ENV="staging" ;;
    3) NODE_ENV="production" ;;
    *) NODE_ENV="development" ;;
esac

echo -e "${GREEN}✓${NC} Environment: $NODE_ENV"
echo ""

# Generate secure passwords
echo "Generating secure passwords..."
MYSQL_ROOT_PASSWORD=$(generate_password)
MYSQL_PASSWORD=$(generate_password)
TIMESCALE_PASSWORD=$(generate_password)
MONGO_PASSWORD=$(generate_password)
RABBITMQ_PASSWORD=$(generate_password)
JWT_SECRET=$(generate_jwt_secret)
echo -e "${GREEN}✓${NC} Passwords generated"
echo ""

# Collect API keys
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "API Keys Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Enter your API keys (press Enter to skip):"
echo ""

read -p "Binance API Key: " BINANCE_API_KEY
read -p "Binance API Secret: " BINANCE_API_SECRET
echo ""

read -p "NewsAPI Key: " NEWSAPI_KEY
read -p "CryptoPanic API Key: " CRYPTOPANIC_API_KEY
echo ""

read -p "Telegram Bot Token: " TELEGRAM_BOT_TOKEN
read -p "Telegram Chat ID: " TELEGRAM_CHAT_ID
echo ""

read -p "Discord Webhook URL: " DISCORD_WEBHOOK_URL
echo ""

read -p "Hugging Face Token: " HUGGINGFACE_TOKEN
echo ""

# Trading symbols
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Trading Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "Trading Symbols (comma-separated) [BTC/USDT,ETH/USDT,SOL/USDT]: " CRYPTO_SYMBOLS
CRYPTO_SYMBOLS=${CRYPTO_SYMBOLS:-BTC/USDT,ETH/USDT,SOL/USDT}
echo ""

read -p "Minimum Risk-Reward Ratio [4.0]: " MIN_RR_RATIO
MIN_RR_RATIO=${MIN_RR_RATIO:-4.0}
echo ""

read -p "Minimum Confidence [60]: " MIN_CONFIDENCE
MIN_CONFIDENCE=${MIN_CONFIDENCE:-60}
echo ""

# Create .env file
echo "📝 Creating .env file..."

cat > .env <<EOF
# ============================================
# CRYPTO TRADING SIGNAL SYSTEM
# Environment: $NODE_ENV
# Generated: $(date)
# ============================================

# ==================== GENERAL ====================
NODE_ENV=$NODE_ENV
APP_NAME=Crypto Signal System
APP_URL=http://localhost
LOG_LEVEL=${NODE_ENV == "production" && echo "warn" || echo "debug"}

# ==================== DATABASE ====================

# MySQL
MYSQL_ROOT_PASSWORD=$MYSQL_ROOT_PASSWORD
MYSQL_DATABASE=crypto_trading_bot
MYSQL_USER=crypto_user
MYSQL_PASSWORD=$MYSQL_PASSWORD

# TimescaleDB
TIMESCALE_DB=crypto_timeseries
TIMESCALE_USER=timescale_user
TIMESCALE_PASSWORD=$TIMESCALE_PASSWORD

# MongoDB
MONGO_DATABASE=crypto_ml_models
MONGO_USER=mongo_user
MONGO_PASSWORD=$MONGO_PASSWORD

# ==================== CACHE & MESSAGE QUEUE ====================

# Redis
REDIS_PASSWORD=

# RabbitMQ
RABBITMQ_USER=rabbitmq_user
RABBITMQ_PASSWORD=$RABBITMQ_PASSWORD

# ==================== API GATEWAY ====================

# JWT Authentication
JWT_SECRET=$JWT_SECRET
JWT_EXPIRATION=7d

# CORS
CORS_ORIGIN=http://localhost:3001

# Rate Limiting
RATE_LIMIT_WINDOW=15m
RATE_LIMIT_MAX=100

# ==================== EXCHANGE APIs ====================

# Binance
BINANCE_API_KEY=$BINANCE_API_KEY
BINANCE_API_SECRET=$BINANCE_API_SECRET
BINANCE_TESTNET=false

# ==================== NEWS APIs ====================

# NewsAPI
NEWSAPI_KEY=$NEWSAPI_KEY

# CryptoPanic
CRYPTOPANIC_API_KEY=$CRYPTOPANIC_API_KEY

# ==================== NOTIFICATION CHANNELS ====================

# Telegram
TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID

# Discord
DISCORD_WEBHOOK_URL=$DISCORD_WEBHOOK_URL

# Email (Configure as needed)
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USER=
EMAIL_PASSWORD=
EMAIL_FROM=noreply@cryptosignal.com
EMAIL_TO=

# ==================== MACHINE LEARNING ====================

# Hugging Face
HUGGINGFACE_TOKEN=$HUGGINGFACE_TOKEN

# ML Configuration
ML_TRAINING_INTERVAL=86400
ML_AUTO_RETRAIN=true
ML_MODEL_PATH=/app/models

# ==================== BOT CONFIGURATION ====================

# Trading Symbols
CRYPTO_SYMBOLS=$CRYPTO_SYMBOLS

# Collection Intervals (seconds)
DATA_COLLECTION_INTERVAL=60
NEWS_COLLECTION_INTERVAL=300
TECH_ANALYSIS_INTERVAL=60
SENTIMENT_ANALYSIS_INTERVAL=300
ITC_ANALYSIS_INTERVAL=300

# Timeframes
TIMEFRAMES=1h,4h,1d

# Signal Validation
MIN_RR_RATIO=$MIN_RR_RATIO
MIN_CONFIDENCE=$MIN_CONFIDENCE
MIN_WIN_RATE=60

# Position Sizing
DEFAULT_RISK_PERCENTAGE=1.0
MAX_POSITION_SIZE=5000

# ==================== FRONTEND ====================

VITE_API_URL=http://localhost:3000
VITE_WS_URL=ws://localhost:3000
VITE_APP_NAME=Crypto Signal System
VITE_APP_VERSION=1.0.0

# ==================== MONITORING ====================

GRAFANA_USER=admin
GRAFANA_PASSWORD=admin

# ==================== PERFORMANCE ====================

DB_POOL_MIN=2
DB_POOL_MAX=10
CACHE_TTL_SIGNALS=300
CACHE_TTL_NEWS=600
CACHE_TTL_PERFORMANCE=3600
WORKER_THREADS=4

# ==================== FEATURE FLAGS ====================

ENABLE_MARKET_DATA_BOT=true
ENABLE_NEWS_COLLECTOR_BOT=true
ENABLE_TECHNICAL_BOT=true
ENABLE_SENTIMENT_BOT=true
ENABLE_ITC_BOT=true
ENABLE_PATTERN_BOT=true
ENABLE_SIGNAL_AGGREGATOR=true
ENABLE_ML_ENGINE=true
ENABLE_NOTIFICATION_BOT=true
ENABLE_FEEDBACK_PROCESSOR=true

ENABLE_MULTI_TIMEFRAME=true
ENABLE_CORRELATION_ANALYSIS=true
ENABLE_MARKET_REGIME_DETECTION=true
ENABLE_AB_TESTING=true
ENABLE_AUTO_LEARNING=true
EOF

echo -e "${GREEN}✓${NC} .env file created"
echo ""

# Create environment-specific files
if [ "$NODE_ENV" = "development" ]; then
    cat > .env.development <<EOF
# Development overrides
DEBUG=true
VERBOSE_LOGGING=true
USE_MOCK_BINANCE=false
SEED_DATABASE=true
EOF
    echo -e "${GREEN}✓${NC} .env.development created"
fi

if [ "$NODE_ENV" = "production" ]; then
    cat > .env.production <<EOF
# Production overrides
DEBUG=false
VERBOSE_LOGGING=false
SSL_ENABLED=true
ENABLE_MONITORING=true
BACKUP_ENABLED=true
EOF
    echo -e "${GREEN}✓${NC} .env.production created"
fi

# Set permissions
chmod 600 .env*
echo -e "${GREEN}✓${NC} Secure permissions set"
echo ""

# Create credentials summary
cat > .credentials.txt <<EOF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRYPTO TRADING SIGNAL SYSTEM - CREDENTIALS
Generated: $(date)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IMPORTANT: Store these credentials securely!

Database Credentials:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MySQL Root Password:    $MYSQL_ROOT_PASSWORD
MySQL User:             crypto_user
MySQL Password:         $MYSQL_PASSWORD

TimescaleDB User:       timescale_user
TimescaleDB Password:   $TIMESCALE_PASSWORD

MongoDB User:           mongo_user
MongoDB Password:       $MONGO_PASSWORD

RabbitMQ User:          rabbitmq_user
RabbitMQ Password:      $RABBITMQ_PASSWORD

JWT Secret:             $JWT_SECRET

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Service URLs:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Dashboard:      http://localhost:3001
API:            http://localhost:3000
RabbitMQ UI:    http://localhost:15672
Grafana:        http://localhost:3002
Adminer:        http://localhost:8080

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECURITY REMINDERS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Never commit .env files to git
2. Store this file in a secure location
3. Delete this file after saving credentials
4. Rotate passwords regularly
5. Use different passwords for production

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF

chmod 600 .credentials.txt
echo -e "${GREEN}✓${NC} Credentials saved to .credentials.txt"
echo ""

echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Environment Configuration Complete!     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo "Files created:"
echo "  ✓ .env"
[ -f .env.development ] && echo "  ✓ .env.development"
[ -f .env.production ] && echo "  ✓ .env.production"
echo "  ✓ .credentials.txt"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT:${NC}"
echo "1. Review and customize .env file as needed"
echo "2. Add your API keys if not provided"
echo "3. Save .credentials.txt securely and delete it"
echo "4. Keep .env files out of version control"
echo ""
echo "Next steps:"
echo "  1. Review .env file: nano .env"
echo "  2. Initialize databases: ./scripts/setup/init_databases.sh"
echo "  3. Start the system: docker-compose up -d"
echo ""