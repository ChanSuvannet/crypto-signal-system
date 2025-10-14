"$OPTIMIZE_LOG"
./scripts/backup/backup_database.sh
echo "" | tee -a "$OPTIMIZE_LOG"

# ==================== OPTIMIZE MYSQL ====================

echo "🗄️  Optimizing MySQL..." | tee -a "$OPTIMIZE_LOG"
echo "" | tee -a "$OPTIMIZE_LOG"

# Get list of tables
TABLES=$(docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
    ${MYSQL_DATABASE} -s -N -e "SHOW TABLES;")

echo "Tables to optimize:" | tee -a "$OPTIMIZE_LOG"
echo "$TABLES" | tee -a "$OPTIMIZE_LOG"
echo "" | tee -a "$OPTIMIZE_LOG"

# Optimize each table
for table in $TABLES; do
    echo "Optimizing table: $table" | tee -a "$OPTIMIZE_LOG"
    docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
        ${MYSQL_DATABASE} -e "OPTIMIZE TABLE ${table};" 2>&1 | tee -a "$OPTIMIZE_LOG"
done

# Analyze tables for query optimization
echo "" | tee -a "$OPTIMIZE_LOG"
echo "Analyzing tables..." | tee -a "$OPTIMIZE_LOG"
for table in $TABLES; do
    docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
        ${MYSQL_DATABASE} -e "ANALYZE TABLE ${table};" 2>&1 | tee -a "$OPTIMIZE_LOG"
done

# Update table statistics
echo "" | tee -a "$OPTIMIZE_LOG"
echo "Updating statistics..." | tee -a "$OPTIMIZE_LOG"
docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
    -e "FLUSH TABLES;" 2>&1 | tee -a "$OPTIMIZE_LOG"

# Show table sizes after optimization
echo "" | tee -a "$OPTIMIZE_LOG"
echo "MySQL Table Sizes After Optimization:" | tee -a "$OPTIMIZE_LOG"
docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} -e \
    "SELECT 
        table_name AS 'Table',
        ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)',
        table_rows AS 'Rows'
     FROM information_schema.tables
     WHERE table_schema = '${MYSQL_DATABASE}'
     ORDER BY (data_length + index_length) DESC;" | tee -a "$OPTIMIZE_LOG"

echo "" | tee -a "$OPTIMIZE_LOG"
echo -e "${GREEN}✓${NC} MySQL optimization complete" | tee -a "$OPTIMIZE_LOG"
echo "" | tee -a "$OPTIMIZE_LOG"

# ==================== OPTIMIZE TIMESCALEDB ====================

echo "📈 Optimizing TimescaleDB..." | tee -a "$OPTIMIZE_LOG"
echo "" | tee -a "$OPTIMIZE_LOG"

# Vacuum and analyze
echo "Running VACUUM ANALYZE..." | tee -a "$OPTIMIZE_LOG"
docker-compose exec -T timescaledb psql -U ${TIMESCALE_USER} -d ${TIMESCALE_DB} -c \
    "VACUUM ANALYZE;" 2>&1 | tee -a "$OPTIMIZE_LOG"

# Reindex
echo "Reindexing database..." | tee -a "$OPTIMIZE_LOG"
docker-compose exec -T timescaledb psql -U ${TIMESCALE_USER} -d ${TIMESCALE_DB} -c \
    "REINDEX DATABASE ${TIMESCALE_DB};" 2>&1 | tee -a "$OPTIMIZE_LOG"

# Refresh continuous aggregates
echo "Refreshing continuous aggregates..." | tee -a "$OPTIMIZE_LOG"
docker-compose exec -T timescaledb psql -U ${TIMESCALE_USER} -d ${TIMESCALE_DB} -c \
    "CALL refresh_continuous_aggregate('price_data_1h', NULL, NULL);
     CALL refresh_continuous_aggregate('price_data_4h', NULL, NULL);
     CALL refresh_continuous_aggregate('price_data_1d', NULL, NULL);" \
    2>&1 | tee -a "$OPTIMIZE_LOG"

# Show hypertable statistics
echo "" | tee -a "$OPTIMIZE_LOG"
echo "TimescaleDB Hypertable Statistics:" | tee -a "$OPTIMIZE_LOG"
docker-compose exec -T timescaledb psql -U ${TIMESCALE_USER} -d ${TIMESCALE_DB} -c \
    "SELECT 
        hypertable_name,
        pg_size_pretty(hypertable_size(format('%I.%I', hypertable_schema, hypertable_name)::regclass)) AS size,
        num_chunks,
        compression_enabled
     FROM timescaledb_information.hypertables;" | tee -a "$OPTIMIZE_LOG"

echo "" | tee -a "$OPTIMIZE_LOG"
echo -e "${GREEN}✓${NC} TimescaleDB optimization complete" | tee -a "$OPTIMIZE_LOG"
echo "" | tee -a "$OPTIMIZE_LOG"

# ==================== OPTIMIZE MONGODB ====================

echo "🍃 Optimizing MongoDB..." | tee -a "$OPTIMIZE_LOG"
echo "" | tee -a "$OPTIMIZE_LOG"

# Compact collections
COLLECTIONS=$(docker-compose exec -T mongodb mongosh ${MONGO_DATABASE} \
    --username ${MONGO_USER} --password ${MONGO_PASSWORD} --quiet \
    --eval "db.getCollectionNames().join(' ')")

for collection in $COLLECTIONS; do
    echo "Compacting collection: $collection" | tee -a "$OPTIMIZE_LOG"
    docker-compose exec -T mongodb mongosh ${MONGO_DATABASE} \
        --username ${MONGO_USER} --password ${MONGO_PASSWORD} --quiet \
        --eval "db.runCommand({ compact: '${collection}' })" \
        2>&1 | tee -a "$OPTIMIZE_LOG"
done

# Rebuild indexes
echo "" | tee -a "$OPTIMIZE_LOG"
echo "Rebuilding indexes..." | tee -a "$OPTIMIZE_LOG"
docker-compose exec -T mongodb mongosh ${MONGO_DATABASE} \
    --username ${MONGO_USER} --password ${MONGO_PASSWORD} --quiet \
    --eval "db.getCollectionNames().forEach(function(col) {
        print('Reindexing: ' + col);
        db[col].reIndex();
    });" 2>&1 | tee -a "$OPTIMIZE_LOG"

# Show collection statistics
echo "" | tee -a "$OPTIMIZE_LOG"
echo "MongoDB Collection Statistics:" | tee -a "$OPTIMIZE_LOG"
docker-compose exec -T mongodb mongosh ${MONGO_DATABASE} \
    --username ${MONGO_USER} --password ${MONGO_PASSWORD} --quiet \
    --eval "db.getCollectionNames().forEach(function(col) {
        var stats = db[col].stats();
        print(col + ': ' + (stats.size / 1024 / 1024).toFixed(2) + ' MB, ' + stats.count + ' documents');
    });" | tee -a "$OPTIMIZE_LOG"

echo "" | tee -a "$OPTIMIZE_LOG"
echo -e "${GREEN}✓${NC} MongoDB optimization complete" | tee -a "$OPTIMIZE_LOG"
echo "" | tee -a "$OPTIMIZE_LOG"

# ==================== OPTIMIZE REDIS ====================

echo "💎 Optimizing Redis..." | tee -a "$OPTIMIZE_LOG"
echo "" | tee -a "$OPTIMIZE_LOG"

# Defragmentation
echo "Defragmenting Redis..." | tee -a "$OPTIMIZE_LOG"
docker-compose exec -T redis redis-cli MEMORY PURGE 2>&1 | tee -a "$OPTIMIZE_LOG"

# Save to disk
echo "Saving Redis to disk..." | tee -a "$OPTIMIZE_LOG"
docker-compose exec -T redis redis-cli BGSAVE 2>&1 | tee -a "$OPTIMIZE_LOG"

# Get memory info
echo "" | tee -a "$OPTIMIZE_LOG"
echo "Redis Memory Statistics:" | tee -a "$OPTIMIZE_LOG"
docker-compose exec -T redis redis-cli INFO memory | grep -E "used_memory_human|used_memory_peak_human|mem_fragmentation_ratio" | tee -a "$OPTIMIZE_LOG"

echo "" | tee -a "$OPTIMIZE_LOG"
echo -e "${GREEN}✓${NC} Redis optimization complete" | tee -a "$OPTIMIZE_LOG"
echo "" | tee -a "$OPTIMIZE_LOG"

# ==================== CHECK INDEX USAGE ====================

echo "📊 Analyzing Index Usage..." | tee -a "$OPTIMIZE_LOG"
echo "" | tee -a "$OPTIMIZE_LOG"

# MySQL unused indexes
echo "MySQL Unused Indexes:" | tee -a "$OPTIMIZE_LOG"
docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} -e \
    "SELECT 
        object_schema AS 'Database',
        object_name AS 'Table',
        index_name AS 'Index'
     FROM performance_schema.table_io_waits_summary_by_index_usage
     WHERE index_name IS NOT NULL
     AND count_star = 0
     AND object_schema = '${MYSQL_DATABASE}'
     ORDER BY object_schema, object_name;" | tee -a "$OPTIMIZE_LOG"

echo "" | tee -a "$OPTIMIZE_LOG"

# MySQL slow queries
echo "MySQL Slow Query Analysis:" | tee -a "$OPTIMIZE_LOG"
docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} -e \
    "SELECT 
        digest_text AS 'Query',
        count_star AS 'Executions',
        ROUND(avg_timer_wait / 1000000000000, 2) AS 'Avg Time (s)',
        ROUND(sum_timer_wait / 1000000000000, 2) AS 'Total Time (s)'
     FROM performance_schema.events_statements_summary_by_digest
     WHERE schema_name = '${MYSQL_DATABASE}'
     ORDER BY sum_timer_wait DESC
     LIMIT 10;" 2>&1 | tee -a "$OPTIMIZE_LOG"

echo "" | tee -a "$OPTIMIZE_LOG"

# ==================== SUGGESTIONS ====================

echo "💡 Optimization Suggestions:" | tee -a "$OPTIMIZE_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$OPTIMIZE_LOG"

# Check for missing indexes
MISSING_INDEXES=$(docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
    ${MYSQL_DATABASE} -s -N -e \
    "SELECT COUNT(*) FROM information_schema.tables 
     WHERE table_schema = '${MYSQL_DATABASE}' 
     AND table_rows > 10000 
     AND table_name NOT IN (
         SELECT DISTINCT table_name 
         FROM information_schema.statistics 
         WHERE table_schema = '${MYSQL_DATABASE}'
     );")

if [ "$MISSING_INDEXES" -gt 0 ]; then
    echo "⚠️  Found $MISSING_INDEXES large tables without indexes" | tee -a "$OPTIMIZE_LOG"
else
    echo "✓ All large tables have indexes" | tee -a "$OPTIMIZE_LOG"
fi

# Check table fragmentation
FRAGMENTED_TABLES=$(docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
    ${MYSQL_DATABASE} -s -N -e \
    "SELECT COUNT(*) FROM information_schema.tables 
     WHERE table_schema = '${MYSQL_DATABASE}' 
     AND data_free > 0 
     AND (data_free / (data_length + index_length)) > 0.1;")

if [ "$FRAGMENTED_TABLES" -gt 0 ]; then
    echo "⚠️  Found $FRAGMENTED_TABLES fragmented tables (>10% free space)" | tee -a "$OPTIMIZE_LOG"
    echo "   Consider running OPTIMIZE TABLE regularly" | tee -a "$OPTIMIZE_LOG"
else
    echo "✓ Tables are well-optimized" | tee -a "$OPTIMIZE_LOG"
fi

# Check TimescaleDB chunk size
LARGE_CHUNKS=$(docker-compose exec -T timescaledb psql -U ${TIMESCALE_USER} -d ${TIMESCALE_DB} -t -c \
    "SELECT COUNT(*) FROM timescaledb_information.chunks 
     WHERE pg_size_pretty(total_bytes::bigint) LIKE '%GB%';" | tr -d ' ')

if [ "$LARGE_CHUNKS" -gt 0 ]; then
    echo "⚠️  Found $LARGE_CHUNKS large chunks in TimescaleDB" | tee -a "$OPTIMIZE_LOG"
    echo "   Consider adjusting chunk_time_interval" | tee -a "$OPTIMIZE_LOG"
else
    echo "✓ TimescaleDB chunk sizes are optimal" | tee -a "$OPTIMIZE_LOG"
fi

echo "" | tee -a "$OPTIMIZE_LOG"

# ==================== FINAL STATISTICS ====================

echo "📈 Final Database Statistics:" | tee -a "$OPTIMIZE_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$OPTIMIZE_LOG"

# Total database size
MYSQL_SIZE=$(docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} -s -N -e \
    "SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) 
     FROM information_schema.tables 
     WHERE table_schema = '${MYSQL_DATABASE}';")
echo "MySQL size: ${MYSQL_SIZE} MB" | tee -a "$OPTIMIZE_LOG"

TIMESCALE_SIZE=$(docker-compose exec -T timescaledb psql -U ${TIMESCALE_USER} -d ${TIMESCALE_DB} -t -c \
    "SELECT pg_size_pretty(pg_database_size('${TIMESCALE_DB}'));" | tr -d ' ')
echo "TimescaleDB size: $TIMESCALE_SIZE" | tee -a "$OPTIMIZE_LOG"

MONGO_SIZE=$(docker-compose exec -T mongodb mongosh ${MONGO_DATABASE} \
    --username ${MONGO_USER} --password ${MONGO_PASSWORD} --quiet \
    --eval "Math.round(db.stats().dataSize / 1024 / 1024 * 100) / 100")
echo "MongoDB size: ${MONGO_SIZE} MB" | tee -a "$OPTIMIZE_LOG"

REDIS_MEMORY=$(docker-compose exec -T redis redis-cli INFO memory | grep used_memory_human | cut -d':' -f2 | tr -d '\r ')
echo "Redis memory: $REDIS_MEMORY" | tee -a "$OPTIMIZE_LOG"

echo "" | tee -a "$OPTIMIZE_LOG"

# ==================== OPTIMIZATION SUMMARY ====================

echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}" | tee -a "$OPTIMIZE_LOG"
echo -e "${GREEN}║   Database Optimization Complete!         ║${NC}" | tee -a "$OPTIMIZE_LOG"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}" | tee -a "$OPTIMIZE_LOG"
echo "" | tee -a "$OPTIMIZE_LOG"

echo "📋 Optimization Summary:" | tee -a "$OPTIMIZE_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$OPTIMIZE_LOG"
echo "  Completed:           $(date)" | tee -a "$OPTIMIZE_LOG"
echo "  Log file:            $OPTIMIZE_LOG" | tee -a "$OPTIMIZE_LOG"
echo "  MySQL tables:        Optimized and analyzed" | tee -a "$OPTIMIZE_LOG"
echo "  TimescaleDB:         Vacuumed and reindexed" | tee -a "$OPTIMIZE_LOG"
echo "  MongoDB:             Compacted and reindexed" | tee -a "$OPTIMIZE_LOG"
echo "  Redis:               Defragmented and saved" | tee -a "$OPTIMIZE_LOG"
echo "" | tee -a "$OPTIMIZE_LOG"

echo "📝 Recommendations:" | tee -a "$OPTIMIZE_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$OPTIMIZE_LOG"
echo "  • Run optimization weekly during low-traffic periods" | tee -a "$OPTIMIZE_LOG"
echo "  • Monitor slow queries and add indexes as needed" | tee -a "$OPTIMIZE_LOG"
echo "  • Consider partitioning large tables (>10M rows)" | tee -a "$OPTIMIZE_LOG"
echo "  • Enable TimescaleDB compression for old data" | tee -a "$OPTIMIZE_LOG"
echo "  • Review and clean up unused indexes" | tee -a "$OPTIMIZE_LOG"
echo "" | tee -a "$OPTIMIZE_LOG"
"$OPTIMIZE_LOG"
./scripts/backup/backup_database.sh
echo "" | tee -a "$OPTIMIZE_LOG"

# ==================== OPTIMIZE MYSQL ====================

echo "🗄️  Optimizing MySQL..." | tee -a "$OPTIMIZE_LOG"
echo "" | tee -a "$OPTIMIZE_LOG"

# Get list of tables
TABLES=$(docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
    ${MYSQL_DATABASE} -s -N -e "SHOW TABLES;")

echo "Tables to optimize:" | tee -a "$OPTIMIZE_LOG"
echo "$TABLES" | tee -a "$OPTIMIZE_LOG"
echo "" | tee -a "$OPTIMIZE_LOG"

# Optimize each table
for table in $TABLES; do
    echo "Optimizing table: $table" | tee -a "$OPTIMIZE_LOG"
    docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
        ${MYSQL_DATABASE} -e "OPTIMIZE TABLE ${table};" 2>&1 | tee -a "$OPTIMIZE_LOG"
done

# Analyze tables for query optimization
echo "" | tee -a "$OPTIMIZE_LOG"
echo "Analyzing tables..." | tee -a "$OPTIMIZE_LOG"
for table in $TABLES; do
    docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
        ${MYSQL_DATABASE} -e "ANALYZE TABLE ${table};" 2>&1 | tee -a "$OPTIMIZE_LOG"
done

# Update table statistics
echo "" | tee -a "$OPTIMIZE_LOG"
echo "Updating statistics..." | tee -a "$OPTIMIZE_LOG"
docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
    -e "FLUSH TABLES;" 2>&1 | tee -a "$OPTIMIZE_LOG"

# Show table sizes after optimization
echo "" | tee -a "$OPTIMIZE_LOG"
echo "MySQL Table Sizes After Optimization:" | tee -a "$OPTIMIZE_LOG"
docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} -e \
    "SELECT 
        table_name AS 'Table',
        ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)',
        table_rows AS 'Rows'
     FROM information_schema.tables
     WHERE table_schema = '${MYSQL_DATABASE}'
     ORDER BY (data_length + index_length) DESC;" | tee -a "$OPTIMIZE_LOG"

echo "" | tee -a "$OPTIMIZE_LOG"
echo -e "${GREEN}✓${NC} MySQL optimization complete" | tee -a "$OPTIMIZE_LOG"
echo "" | tee -a "$OPTIMIZE_LOG"

# ==================== OPTIMIZE TIMESCALEDB ====================

echo "📈 Optimizing TimescaleDB..." | tee -a "$OPTIMIZE_LOG"
echo "" | tee -a "$OPTIMIZE_LOG"

# Vacuum and analyze
echo "Running VACUUM ANALYZE..." | tee -a "$OPTIMIZE_LOG"
docker-compose exec -T timescaledb psql -U ${TIMESCALE_USER} -d ${TIMESCALE_DB} -c \
    "VACUUM ANALYZE;" 2>&1 | tee -a "$OPTIMIZE_LOG"

# Reindex
echo "Reindexing database..." | tee -a "$OPTIMIZE_LOG"
docker-compose exec -T timescaledb psql -U ${TIMESCALE_USER} -d ${TIMESCALE_DB} -c \
    "REINDEX DATABASE ${TIMESCALE_DB};" 2>&1 | tee -a "$OPTIMIZE_LOG"

# Refresh continuous aggregates
echo "Refreshing continuous aggregates..." | tee -a "$OPTIMIZE_LOG"
docker-compose exec -T timescaledb psql -U ${TIMESCALE_USER} -d ${TIMESCALE_DB} -c \
    "CALL refresh_continuous_aggregate('price_data_1h', NULL, NULL);
     CALL refresh_continuous_aggregate('price_data_4h', NULL, NULL);
     CALL refresh_continuous_aggregate('price_data_1d', NULL, NULL);" \
    2>&1 | tee -a "$OPTIMIZE_LOG"

# Show hypertable statistics
echo "" | tee -a "$OPTIMIZE_LOG"
echo "TimescaleDB Hypertable Statistics:" | tee -a "$OPTIMIZE_LOG"
docker-compose exec -T timescaledb psql -U ${TIMESCALE_USER} -d ${TIMESCALE_DB} -c \
    "SELECT 
        hypertable_name,
        pg_size_pretty(hypertable_size(format('%I.%I', hypertable_schema, hypertable_name)::regclass)) AS size,
        num_chunks,
        compression_enabled
     FROM timescaledb_information.hypertables;" | tee -a "$OPTIMIZE_LOG"

echo "" | tee -a "$OPTIMIZE_LOG"
echo -e "${GREEN}✓${NC} TimescaleDB optimization complete" | tee -a "$OPTIMIZE_LOG"
echo "" | tee -a "$OPTIMIZE_LOG"

# ==================== OPTIMIZE MONGODB ====================

echo "🍃 Optimizing MongoDB..." | tee -a "$OPTIMIZE_LOG"
echo "" | tee -a "$OPTIMIZE_LOG"

# Compact collections
COLLECTIONS=$(docker-compose exec -T mongodb mongosh ${MONGO_DATABASE} \
    --username ${MONGO_USER} --password ${MONGO_PASSWORD} --quiet \
    --eval "db.getCollectionNames().join(' ')")

for collection in $COLLECTIONS; do
    echo "Compacting collection: $collection" | tee -a "$OPTIMIZE_LOG"
    docker-compose exec -T mongodb mongosh ${MONGO_DATABASE} \
        --username ${MONGO_USER} --password ${MONGO_PASSWORD} --quiet \
        --eval "db.runCommand({ compact: '${collection}' })" \
        2>&1 | tee -a "$OPTIMIZE_LOG"
done

# Rebuild indexes
echo "" | tee -a "$OPTIMIZE_LOG"
echo "Rebuilding indexes..." | tee -a "$OPTIMIZE_LOG"
docker-compose exec -T mongodb mongosh ${MONGO_DATABASE} \
    --username ${MONGO_USER} --password ${MONGO_PASSWORD} --quiet \
    --eval "db.getCollectionNames().forEach(function(col) {
        print('Reindexing: ' + col);
        db[col].reIndex();
    });" 2>&1 | tee -a "$OPTIMIZE_LOG"

# Show collection statistics
echo "" | tee -a "$OPTIMIZE_LOG"
echo "MongoDB Collection Statistics:" | tee -a "$OPTIMIZE_LOG"
docker-compose exec -T mongodb mongosh ${MONGO_DATABASE} \
    --username ${MONGO_USER} --password ${MONGO_PASSWORD} --quiet \
    --eval "db.getCollectionNames().forEach(function(col) {
        var stats = db[col].stats();
        print(col + ': ' + (stats.size / 1024 / 1024).toFixed(2) + ' MB, ' + stats.count + ' documents');
    });" | tee -a "$OPTIMIZE_LOG"

echo "" | tee -a "$OPTIMIZE_LOG"
echo -e "${GREEN}✓${NC} MongoDB optimization complete" | tee -a "$OPTIMIZE_LOG"
echo "" | tee -a "$OPTIMIZE_LOG"

# ==================== OPTIMIZE REDIS ====================

echo "💎 Optimizing Redis..." | tee -a "$OPTIMIZE_LOG"
echo "" | tee -a "$OPTIMIZE_LOG"

# Defragmentation
echo "Defragmenting Redis..." | tee -a "$OPTIMIZE_LOG"
docker-compose exec -T redis redis-cli MEMORY PURGE 2>&1 | tee -a "$OPTIMIZE_LOG"

# Save to disk
echo "Saving Redis to disk..." | tee -a "$OPTIMIZE_LOG"
docker-compose exec -T redis redis-cli BGSAVE 2>&1 | tee -a "$OPTIMIZE_LOG"

# Get memory info
echo "" | tee -a "$OPTIMIZE_LOG"
echo "Redis Memory Statistics:" | tee -a "$OPTIMIZE_LOG"
docker-compose exec -T redis redis-cli INFO memory | grep -E "used_memory_human|used_memory_peak_human|mem_fragmentation_ratio" | tee -a "$OPTIMIZE_LOG"

echo "" | tee -a "$OPTIMIZE_LOG"
echo -e "${GREEN}✓${NC} Redis optimization complete" | tee -a "$OPTIMIZE_LOG"
echo "" | tee -a "$OPTIMIZE_LOG"

# ==================== CHECK INDEX USAGE ====================

echo "📊 Analyzing Index Usage..." | tee -a "$OPTIMIZE_LOG"
echo "" | tee -a "$OPTIMIZE_LOG"

# MySQL unused indexes
echo "MySQL Unused Indexes:" | tee -a "$OPTIMIZE_LOG"
docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} -e \
    "SELECT 
        object_schema AS 'Database',
        object_name AS 'Table',
        index_name AS 'Index'
     FROM performance_schema.table_io_waits_summary_by_index_usage
     WHERE index_name IS NOT NULL
     AND count_star = 0
     AND object_schema = '${MYSQL_DATABASE}'
     ORDER BY object_schema, object_name;" | tee -a "$OPTIMIZE_LOG"

echo "" | tee -a "$OPTIMIZE_LOG"

# MySQL slow queries
echo "MySQL Slow Query Analysis:" | tee -a "$OPTIMIZE_LOG"
docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} -e \
    "SELECT 
        digest_text AS 'Query',
        count_star AS 'Executions',
        ROUND(avg_timer_wait / 1000000000000, 2) AS 'Avg Time (s)',
        ROUND(sum_timer_wait / 1000000000000, 2) AS 'Total Time (s)'
     FROM performance_schema.events_statements_summary_by_digest
     WHERE schema_name = '${MYSQL_DATABASE}'
     ORDER BY sum_timer_wait DESC
     LIMIT 10;" 2>&1 | tee -a "$OPTIMIZE_LOG"

echo "" | tee -a "$OPTIMIZE_LOG"

# ==================== SUGGESTIONS ====================

echo "💡 Optimization Suggestions:" | tee -a "$OPTIMIZE_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$OPTIMIZE_LOG"

# Check for missing indexes
MISSING_INDEXES=$(docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
    ${MYSQL_DATABASE} -s -N -e \
    "SELECT COUNT(*) FROM information_schema.tables 
     WHERE table_schema = '${MYSQL_DATABASE}' 
     AND table_rows > 10000 
     AND table_name NOT IN (
         SELECT DISTINCT table_name 
         FROM information_schema.statistics 
         WHERE table_schema = '${MYSQL_DATABASE}'
     );")

if [ "$MISSING_INDEXES" -gt 0 ]; then
    echo "⚠️  Found $MISSING_INDEXES large tables without indexes" | tee -a "$OPTIMIZE_LOG"
else
    echo "✓ All large tables have indexes" | tee -a "$OPTIMIZE_LOG"
fi

# Check table fragmentation
FRAGMENTED_TABLES=$(docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} \
    ${MYSQL_DATABASE} -s -N -e \
    "SELECT COUNT(*) FROM information_schema.tables 
     WHERE table_schema = '${MYSQL_DATABASE}' 
     AND data_free > 0 
     AND (data_free / (data_length + index_length)) > 0.1;")

if [ "$FRAGMENTED_TABLES" -gt 0 ]; then
    echo "⚠️  Found $FRAGMENTED_TABLES fragmented tables (>10% free space)" | tee -a "$OPTIMIZE_LOG"
    echo "   Consider running OPTIMIZE TABLE regularly" | tee -a "$OPTIMIZE_LOG"
else
    echo "✓ Tables are well-optimized" | tee -a "$OPTIMIZE_LOG"
fi

# Check TimescaleDB chunk size
LARGE_CHUNKS=$(docker-compose exec -T timescaledb psql -U ${TIMESCALE_USER} -d ${TIMESCALE_DB} -t -c \
    "SELECT COUNT(*) FROM timescaledb_information.chunks 
     WHERE pg_size_pretty(total_bytes::bigint) LIKE '%GB%';" | tr -d ' ')

if [ "$LARGE_CHUNKS" -gt 0 ]; then
    echo "⚠️  Found $LARGE_CHUNKS large chunks in TimescaleDB" | tee -a "$OPTIMIZE_LOG"
    echo "   Consider adjusting chunk_time_interval" | tee -a "$OPTIMIZE_LOG"
else
    echo "✓ TimescaleDB chunk sizes are optimal" | tee -a "$OPTIMIZE_LOG"
fi

echo "" | tee -a "$OPTIMIZE_LOG"

# ==================== FINAL STATISTICS ====================

echo "📈 Final Database Statistics:" | tee -a "$OPTIMIZE_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$OPTIMIZE_LOG"

# Total database size
MYSQL_SIZE=$(docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} -s -N -e \
    "SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) 
     FROM information_schema.tables 
     WHERE table_schema = '${MYSQL_DATABASE}';")
echo "MySQL size: ${MYSQL_SIZE} MB" | tee -a "$OPTIMIZE_LOG"

TIMESCALE_SIZE=$(docker-compose exec -T timescaledb psql -U ${TIMESCALE_USER} -d ${TIMESCALE_DB} -t -c \
    "SELECT pg_size_pretty(pg_database_size('${TIMESCALE_DB}'));" | tr -d ' ')
echo "TimescaleDB size: $TIMESCALE_SIZE" | tee -a "$OPTIMIZE_LOG"

MONGO_SIZE=$(docker-compose exec -T mongodb mongosh ${MONGO_DATABASE} \
    --username ${MONGO_USER} --password ${MONGO_PASSWORD} --quiet \
    --eval "Math.round(db.stats().dataSize / 1024 / 1024 * 100) / 100")
echo "MongoDB size: ${MONGO_SIZE} MB" | tee -a "$OPTIMIZE_LOG"

REDIS_MEMORY=$(docker-compose exec -T redis redis-cli INFO memory | grep used_memory_human | cut -d':' -f2 | tr -d '\r ')
echo "Redis memory: $REDIS_MEMORY" | tee -a "$OPTIMIZE_LOG"

echo "" | tee -a "$OPTIMIZE_LOG"

# ==================== OPTIMIZATION SUMMARY ====================

echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}" | tee -a "$OPTIMIZE_LOG"
echo -e "${GREEN}║   Database Optimization Complete!          ║${NC}" | tee -a "$OPTIMIZE_LOG"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}" | tee -a "$OPTIMIZE_LOG"
echo "" | tee -a "$OPTIMIZE_LOG"

echo "📋 Optimization Summary:" | tee -a "$OPTIMIZE_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$OPTIMIZE_LOG"
echo "  Completed:           $(date)" | tee -a "$OPTIMIZE_LOG"
echo "  Log file:            $OPTIMIZE_LOG" | tee -a "$OPTIMIZE_LOG"
echo "  MySQL tables:        Optimized and analyzed" | tee -a "$OPTIMIZE_LOG"
echo "  TimescaleDB:         Vacuumed and reindexed" | tee -a "$OPTIMIZE_LOG"
echo "  MongoDB:             Compacted and reindexed" | tee -a "$OPTIMIZE_LOG"
echo "  Redis:               Defragmented and saved" | tee -a "$OPTIMIZE_LOG"
echo "" | tee -a "$OPTIMIZE_LOG"

echo "📝 Recommendations:" | tee -a "$OPTIMIZE_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$OPTIMIZE_LOG"
echo "  • Run optimization weekly during low-traffic periods" | tee -a "$OPTIMIZE_LOG"
echo "  • Monitor slow queries and add indexes as needed" | tee -a "$OPTIMIZE_LOG"
echo "  • Consider partitioning large tables (>10M rows)" | tee -a "$OPTIMIZE_LOG"
echo "  • Enable TimescaleDB compression for old data" | tee -a "$OPTIMIZE_LOG"
echo "  • Review and clean up unused indexes" | tee -a "$OPTIMIZE_LOG"
echo "" | tee -a "$OPTIMIZE_LOG"