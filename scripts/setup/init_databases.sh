#!/bin/bash

# ============================================
# scripts/setup/init_databases.sh
# Initialize Databases
# Crypto Trading Signal System
# ============================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║            Initializing Databases          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo -e "${GREEN}✓${NC} Environment variables loaded"
else
    echo -e "${RED}✗${NC} .env file not found"
    echo "Please run: ./scripts/setup/generate_env_files.sh"
    exit 1
fi

echo ""

# ==================== START DATABASES ====================

echo "🚀 Starting database containers..."
echo ""

docker-compose up -d mysql timescaledb redis mongodb rabbitmq

echo ""
echo "⏳ Waiting for databases to be ready..."
echo ""

# Wait for MySQL
echo -n "MySQL: "
for i in {1..60}; do
    if docker-compose exec -T mysql mysqladmin ping -h localhost -u root -p${MYSQL_ROOT_PASSWORD} >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Ready${NC}"
        break
    fi
    echo -n "."
    sleep 2
done

# Wait for TimescaleDB
echo -n "TimescaleDB: "
for i in {1..60}; do
    if docker-compose exec -T timescaledb pg_isready -U ${TIMESCALE_USER} >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Ready${NC}"
        break
    fi
    echo -n "."
    sleep 2
done

# Wait for Redis
echo -n "Redis: "
for i in {1..30}; do
    if docker-compose exec -T redis redis-cli ping >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Ready${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# Wait for MongoDB
echo -n "MongoDB: "
for i in {1..60}; do
    if docker-compose exec -T mongodb mongosh --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Ready${NC}"
        break
    fi
    echo -n "."
    sleep 2
done

# Wait for RabbitMQ
echo -n "RabbitMQ: "
for i in {1..60}; do
    if docker-compose exec -T rabbitmq rabbitmqctl status >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Ready${NC}"
        break
    fi
    echo -n "."
    sleep 2
done

echo ""

# ==================== INITIALIZE MYSQL ====================

echo "📊 Initializing MySQL database..."
echo ""

# Check if database exists
DB_EXISTS=$(docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
    -e "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME='${MYSQL_DATABASE}';" \
    | grep -c ${MYSQL_DATABASE} || true)

if [ "$DB_EXISTS" -eq "0" ]; then
    echo "Creating database ${MYSQL_DATABASE}..."
    docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
        -e "CREATE DATABASE IF NOT EXISTS ${MYSQL_DATABASE};"
    echo -e "${GREEN}✓${NC} Database created"
else
    echo -e "${YELLOW}!${NC} Database ${MYSQL_DATABASE} already exists"
    read -p "Drop and recreate? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
            -e "DROP DATABASE ${MYSQL_DATABASE}; CREATE DATABASE ${MYSQL_DATABASE};"
        echo -e "${GREEN}✓${NC} Database recreated"
    fi
fi

# Import schema
if [ -f "./database/schemas/complete_schema.sql" ]; then
    echo "Importing schema..."
    docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
        ${MYSQL_DATABASE} < ./database/schemas/complete_schema.sql
    echo -e "${GREEN}✓${NC} Schema imported"
else
    echo -e "${YELLOW}!${NC} Schema file not found, skipping"
fi

# Create database user
echo "Creating database user..."
docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} <<EOF
CREATE USER IF NOT EXISTS '${MYSQL_USER}'@'%' IDENTIFIED BY '${MYSQL_PASSWORD}';
GRANT ALL PRIVILEGES ON ${MYSQL_DATABASE}.* TO '${MYSQL_USER}'@'%';
FLUSH PRIVILEGES;
EOF
echo -e "${GREEN}✓${NC} User created with privileges"

echo ""

# ==================== INITIALIZE TIMESCALEDB ====================

echo "📈 Initializing TimescaleDB..."
echo ""

# Check if database exists
DB_EXISTS=$(docker-compose exec -T timescaledb psql -U ${TIMESCALE_USER} -lqt \
    | cut -d \| -f 1 | grep -wc ${TIMESCALE_DB} || true)

if [ "$DB_EXISTS" -eq "0" ]; then
    echo "Creating database ${TIMESCALE_DB}..."
    docker-compose exec -T timescaledb psql -U ${TIMESCALE_USER} \
        -c "CREATE DATABASE ${TIMESCALE_DB};"
    echo -e "${GREEN}✓${NC} Database created"
else
    echo -e "${YELLOW}!${NC} Database ${TIMESCALE_DB} already exists"
fi

# Enable TimescaleDB extension
echo "Enabling TimescaleDB extension..."
docker-compose exec -T timescaledb psql -U ${TIMESCALE_USER} -d ${TIMESCALE_DB} \
    -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
echo -e "${GREEN}✓${NC} TimescaleDB extension enabled"

# Import schema
if [ -f "./database/schemas/timescale_schema.sql" ]; then
    echo "Importing TimescaleDB schema..."
    docker-compose exec -T timescaledb psql -U ${TIMESCALE_USER} -d ${TIMESCALE_DB} \
        < ./database/schemas/timescale_schema.sql
    echo -e "${GREEN}✓${NC} Schema imported"
fi

echo ""

# ==================== INITIALIZE REDIS ====================

echo "💾 Configuring Redis..."
echo ""

# Redis doesn't need initialization, just verify it's working
if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
    echo -e "${GREEN}✓${NC} Redis is working"
else
    echo -e "${RED}✗${NC} Redis configuration failed"
    exit 1
fi

echo ""

# ==================== INITIALIZE MONGODB ====================

echo "🍃 Initializing MongoDB..."
echo ""

# Create database and user
docker-compose exec -T mongodb mongosh admin --eval "
    db.createUser({
        user: '${MONGO_USER}',
        pwd: '${MONGO_PASSWORD}',
        roles: [
            { role: 'readWrite', db: '${MONGO_DATABASE}' },
            { role: 'dbAdmin', db: '${MONGO_DATABASE}' }
        ]
    });
" 2>/dev/null || echo -e "${YELLOW}!${NC} User may already exist"

# Create collections
docker-compose exec -T mongodb mongosh ${MONGO_DATABASE} \
    --username ${MONGO_USER} --password ${MONGO_PASSWORD} --eval "
    db.createCollection('ml_models');
    db.createCollection('model_versions');
    db.createCollection('training_logs');
    db.ml_models.createIndex({ 'model_name': 1, 'version': 1 }, { unique: true });
" >/dev/null 2>&1

echo -e "${GREEN}✓${NC} MongoDB initialized"
echo ""

# ==================== INITIALIZE RABBITMQ ====================

echo "🐰 Configuring RabbitMQ..."
echo ""

# Create exchanges and queues
docker-compose exec -T rabbitmq rabbitmqadmin declare exchange \
    name=crypto_signals type=topic durable=true 2>/dev/null || true

docker-compose exec -T rabbitmq rabbitmqadmin declare exchange \
    name=crypto_events type=topic durable=true 2>/dev/null || true

# Create queues
for queue in market_data news_data technical_signals sentiment_signals \
             itc_signals pattern_signals aggregated_signals notifications; do
    docker-compose exec -T rabbitmq rabbitmqadmin declare queue \
        name=${queue} durable=true 2>/dev/null || true
done

echo -e "${GREEN}✓${NC} RabbitMQ configured"
echo ""

# ==================== RUN MIGRATIONS ====================

echo "🔄 Running database migrations..."
echo ""

# Run MySQL migrations
if [ -d "./database/migrations/mysql" ]; then
    for migration in ./database/migrations/mysql/*.sql; do
        if [ -f "$migration" ]; then
            filename=$(basename "$migration")
            echo "Running migration: $filename"
            docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
                ${MYSQL_DATABASE} < "$migration"
            echo -e "${GREEN}✓${NC} $filename applied"
        fi
    done
fi

# Run TimescaleDB migrations
if [ -d "./database/migrations/timescaledb" ]; then
    for migration in ./database/migrations/timescaledb/*.sql; do
        if [ -f "$migration" ]; then
            filename=$(basename "$migration")
            echo "Running migration: $filename"
            docker-compose exec -T timescaledb psql -U ${TIMESCALE_USER} \
                -d ${TIMESCALE_DB} < "$migration"
            echo -e "${GREEN}✓${NC} $filename applied"
        fi
    done
fi

echo ""

# ==================== SEED DATA (OPTIONAL) ====================

read -p "Load seed data for development? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "📝 Loading seed data..."
    
    if [ -f "./database/seeds/seed_data.sql" ]; then
        docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
            ${MYSQL_DATABASE} < ./database/seeds/seed_data.sql
        echo -e "${GREEN}✓${NC} Seed data loaded"
    else
        echo -e "${YELLOW}!${NC} No seed data file found"
    fi
fi

echo ""

# ==================== VERIFY INITIALIZATION ====================

echo "🔍 Verifying database initialization..."
echo ""

# Check MySQL tables
TABLE_COUNT=$(docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
    ${MYSQL_DATABASE} -e "SHOW TABLES;" | wc -l)
echo "MySQL tables: $((TABLE_COUNT - 1))"

# Check TimescaleDB hypertables
HYPERTABLE_COUNT=$(docker-compose exec -T timescaledb psql -U ${TIMESCALE_USER} \
    -d ${TIMESCALE_DB} -t -c "SELECT COUNT(*) FROM timescaledb_information.hypertables;" \
    | tr -d ' ')
echo "TimescaleDB hypertables: $HYPERTABLE_COUNT"

# Check MongoDB collections
COLLECTION_COUNT=$(docker-compose exec -T mongodb mongosh ${MONGO_DATABASE} \
    --username ${MONGO_USER} --password ${MONGO_PASSWORD} --quiet \
    --eval "db.getCollectionNames().length")
echo "MongoDB collections: $COLLECTION_COUNT"

echo ""

# ==================== CREATE BACKUP ====================

echo "💾 Creating initial backup..."
./scripts/backup/backup_database.sh
echo ""

# ==================== SUMMARY ====================

echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Database Initialization Complete!       ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo "Database URLs:"
echo "  MySQL:        localhost:3306/${MYSQL_DATABASE}"
echo "  TimescaleDB:  localhost:5432/${TIMESCALE_DB}"
echo "  Redis:        localhost:6379"
echo "  MongoDB:      localhost:27017/${MONGO_DATABASE}"
echo "  RabbitMQ:     localhost:5672 (Management: http://localhost:15672)"
echo ""
echo "Next step:"
echo "  docker-compose up -d"
echo ""