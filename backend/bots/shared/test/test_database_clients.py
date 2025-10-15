
### `test_database_clients.py`
"""
Test Database Clients
=====================
Test script to verify all database connections.
"""

import asyncio
from shared.core import Config, setup_logger
from shared.database import (
    MySQLClient,
    TimescaleClient,
    RedisClient,
    MongoDBClient,
)


async def test_mysql():
    """Test MySQL client."""
    logger = setup_logger('test_mysql')
    logger.info("Testing MySQL client...")
    
    async with MySQLClient() as client:
        # Test query
        result = await client.fetch_one("SELECT 1 as test")
        logger.info(f"MySQL test query result: {result}")
        
        # Health check
        health = await client.health_check()
        logger.info(f"MySQL health: {health}")


async def test_timescale():
    """Test TimescaleDB client."""
    logger = setup_logger('test_timescale')
    logger.info("Testing TimescaleDB client...")

    async with TimescaleClient() as client:
        # Test query
        result = await client.execute("SELECT 1 as test")
        logger.info("TimescaleDB test query executed")

        # Health check
        health = await client.health_check()
        logger.info(f"TimescaleDB health: {health}")


async def test_redis():
    """Test Redis client."""
    logger = setup_logger('test_redis')
    logger.info("Testing Redis client...")
    
    async with RedisClient() as client:
        # Test set/get
        await client.set('test_key', {'message': 'Hello Redis!'})
        value = await client.get('test_key')
        logger.info(f"Redis test value: {value}")
        
        # Health check
        health = await client.health_check()
        logger.info(f"Redis health: {health}")
        
        # Cleanup
        await client.delete('test_key')


async def test_mongodb():
    """Test MongoDB client."""
    logger = setup_logger('test_mongodb')
    logger.info("Testing MongoDB client...")
    
    async with MongoDBClient() as client:
        # Test insert
        doc_id = await client.insert_one('test_collection', {
            'message': 'Hello MongoDB!',
            'value': 42
        })
        logger.info(f"MongoDB inserted document: {doc_id}")
        
        # Test find
        doc = await client.find_one('test_collection', {'_id': doc_id})
        logger.info(f"MongoDB found document: {doc}")
        
        # Health check
        health = await client.health_check()
        logger.info(f"MongoDB health: {health}")
        
        # Cleanup
        await client.delete_one('test_collection', {'_id': doc_id})


async def main():
    """Run all tests."""
    logger = setup_logger('test_main')
    
    try:
        logger.info("🚀 Starting database clients tests...")
        
        await test_mysql()
        await test_timescale()
        await test_redis()
        await test_mongodb()
        
        logger.info("✅ All database clients tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)


if __name__ == '__main__':
    asyncio.run(main())
