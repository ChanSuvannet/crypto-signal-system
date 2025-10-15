# ============================================
# Crypto Trading Signal System
# backed/bots/shared/database/redis_client.py
# Deception: Async Redis client for caching and real-time data.
# ============================================

import json
from typing import Optional, Any, Dict, List, Union
from datetime import timedelta
import redis.asyncio as redis
from redis.asyncio import Redis

from ..core.config import Config
from ..core.logger import get_logger
from ..core.exceptions import BotConnectionError, BotDatabaseError, retry_on_error


class RedisClient:
    """
    Async Redis client for caching and pub/sub.

    Features:
    - Key-value operations
    - Caching with TTL
    - Pub/Sub messaging
    - JSON serialization
    - Connection pooling
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize Redis client.

        Args:
            config: Configuration instance
        """
        self.config = config or Config()
        self.logger = get_logger("redis_client")

        self.client: Optional[Redis] = None
        self._is_connected = False
        self.default_ttl = self.config.get("CACHE_TTL", 300)  # 5 minutes

    async def connect(self):
        """Establish Redis connection."""
        if self._is_connected:
            self.logger.warning("Redis client is already connected")
            return

        try:
            # Get Redis URL
            redis_url = self.config.get_redis_url()

            # Create Redis client
            self.client = await redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=self.config.get("DB_POOL_MAX", 10),
                socket_keepalive=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
            )

            # Test connection
            await self.client.ping()

            self._is_connected = True
            self.logger.info("✓ Connected to Redis")

        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            raise BotConnectionError(
                f"Redis connection failed: {str(e)}", service="Redis"
            ) from e

    async def disconnect(self):
        """Close Redis connection."""
        if not self._is_connected:
            return

        try:
            if self.client:
                await self.client.close()

            self._is_connected = False
            self.logger.info("✓ Disconnected from Redis")

        except Exception as e:
            self.logger.error(f"Error disconnecting from Redis: {e}")

    @retry_on_error(max_attempts=3)
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value by key.

        Args:
            key: Cache key

        Returns:
            Value or None if not found
        """
        try:
            value = await self.client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            self.logger.error(f"Get failed for key {key}: {e}")
            raise BotDatabaseError(f"Redis GET failed: {str(e)}")

    @retry_on_error(max_attempts=3)
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value with optional TTL.

        Args:
            key: Cache key
            value: Value to store
            ttl: Time to live in seconds (None = default TTL)
        """
        try:
            # Serialize value
            if not isinstance(value, str):
                value = json.dumps(value)

            # Set with TTL
            ttl = ttl if ttl is not None else self.default_ttl
            await self.client.setex(key, ttl, value)

        except Exception as e:
            self.logger.error(f"Set failed for key {key}: {e}")
            raise BotDatabaseError(f"Redis SET failed: {str(e)}")

    async def delete(self, key: str) -> bool:
        """
        Delete key.

        Args:
            key: Cache key

        Returns:
            True if key was deleted
        """
        try:
            result = await self.client.delete(key)
            return result > 0
        except Exception as e:
            self.logger.error(f"Delete failed for key {key}: {e}")
            raise BotDatabaseError from e


async def exists(self, key: str) -> bool:
    """
    Check if key exists.

    Args:
        key: Cache key

    Returns:
        True if key exists
    """
    try:
        result = await self.client.exists(key)
        return result > 0
    except Exception as e:
        self.logger.error(f"Exists check failed for key {key}: {e}")
        raise BotDatabaseError(f"Redis EXISTS failed: {str(e)}")


async def increment(self, key: str, amount: int = 1) -> int:
    """
    Increment numeric value.

    Args:
        key: Cache key
        amount: Amount to increment by

    Returns:
        New value after increment
    """
    try:
        return await self.client.incrby(key, amount)
    except Exception as e:
        self.logger.error(f"Increment failed for key {key}: {e}")
        raise BotDatabaseError(f"Redis INCRBY failed: {str(e)}")


async def decrement(self, key: str, amount: int = 1) -> int:
    """
    Decrement numeric value.

    Args:
        key: Cache key
        amount: Amount to decrement by

    Returns:
        New value after decrement
    """
    try:
        return await self.client.decrby(key, amount)
    except Exception as e:
        self.logger.error(f"Decrement failed for key {key}: {e}")
        raise BotDatabaseError(f"Redis DECRBY failed: {str(e)}")


async def set_hash(self, key: str, mapping: Dict[str, Any]):
    """
    Set hash (dictionary).

    Args:
        key: Hash key
        mapping: Dictionary to store
    """
    try:
        # Serialize values
        serialized = {
            k: v if isinstance(v, str) else json.dumps(v)
            for k, v in mapping.items()
        }
        await self.client.hset(key, mapping=serialized)
    except Exception as e:
        self.logger.error(f"Set hash failed for key {key}: {e}")
        raise BotDatabaseError(f"Redis HSET failed: {str(e)}") from e


async def get_hash(self, key: str) -> Dict[str, Any]:
    """
    Get hash (dictionary).

    Args:
        key: Hash key

    Returns:
        Dictionary
    """
    try:
        data = await self.client.hgetall(key)

        # Deserialize values
        result = {}
        for k, v in data.items():
            try:
                result[k] = json.loads(v)
            except json.JSONDecodeError:
                result[k] = v

        return result
    except Exception as e:
        self.logger.error(f"Get hash failed for key {key}: {e}")
        raise BotDatabaseError(f"Redis HGETALL failed: {str(e)}")


async def get_hash_field(self, key: str, field: str) -> Optional[Any]:
    """
    Get single field from hash.

    Args:
        key: Hash key
        field: Field name

    Returns:
        Field value or None
    """
    try:
        value = await self.client.hget(key, field)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    except Exception as e:
        self.logger.error(f"Get hash field failed for key {key}, field {field}: {e}")
        raise BotDatabaseError(f"Redis HGET failed: {str(e)}") from e


async def push_list(self, key: str, *values: Any):
    """
    Push values to list (left push).

    Args:
        key: List key
        values: Values to push
    """
    try:
        serialized = [v if isinstance(v, str) else json.dumps(v) for v in values]
        await self.client.lpush(key, *serialized)
    except Exception as e:
        self.logger.error(f"Push list failed for key {key}: {e}")
        raise BotDatabaseError(f"Redis LPUSH failed: {str(e)}") from e


async def get_list(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
    """
    Get list range.

    Args:
        key: List key
        start: Start index
        end: End index (-1 = all)

    Returns:
        List of values
    """
    try:
        data = await self.client.lrange(key, start, end)

        result = []
        for item in data:
            try:
                result.append(json.loads(item))
            except json.JSONDecodeError:
                result.append(item)

        return result
    except Exception as e:
        self.logger.error(f"Get list failed for key {key}: {e}")
        raise BotDatabaseError(f"Redis LRANGE failed: {str(e)}") from e


async def add_to_set(self, key: str, *values: Any):
    """
    Add values to set.

    Args:
        key: Set key
        values: Values to add
    """
    try:
        serialized = [v if isinstance(v, str) else json.dumps(v) for v in values]
        await self.client.sadd(key, *serialized)
    except Exception as e:
        self.logger.error(f"Add to set failed for key {key}: {e}")
        raise BotDatabaseError(f"Redis SADD failed: {str(e)}") from e


async def get_set(self, key: str) -> set:
    """
    Get all members of set.

    Args:
        key: Set key

    Returns:
        Set of values
    """
    try:
        data = await self.client.smembers(key)

        result = set()
        for item in data:
            try:
                result.add(json.loads(item))
            except (json.JSONDecodeError, TypeError):
                result.add(item)

        return result
    except Exception as e:
        self.logger.error(f"Get set failed for key {key}: {e}")
        raise BotDatabaseError(f"Redis SMEMBERS failed: {str(e)}") from e


async def is_in_set(self, key: str, value: Any) -> bool:
    """
    Check if value is in set.

    Args:
        key: Set key
        value: Value to check

    Returns:
        True if value is in set
    """
    try:
        serialized = value if isinstance(value, str) else json.dumps(value)
        return await self.client.sismember(key, serialized)
    except Exception as e:
        self.logger.error(f"Set membership check failed for key {key}: {e}")
        raise BotDatabaseError(f"Redis SISMEMBER failed: {str(e)}")


async def publish(self, channel: str, message: Any):
    """
    Publish message to channel.

    Args:
        channel: Channel name
        message: Message to publish
    """
    try:
        serialized = message if isinstance(message, str) else json.dumps(message)
        await self.client.publish(channel, serialized)
    except Exception as e:
        self.logger.error(f"Publish failed for channel {channel}: {e}")
        raise BotDatabaseError(f"Redis PUBLISH failed: {str(e)}") from e


async def subscribe(self, *channels: str):
    """
    Subscribe to channels.

    Args:
        channels: Channel names

    Returns:
        PubSub instance
    """
    try:
        pubsub = self.client.pubsub()
        await pubsub.subscribe(*channels)
        return pubsub
    except Exception as e:
        self.logger.error(f"Subscribe failed: {e}")
        raise BotDatabaseError(f"Redis SUBSCRIBE failed: {str(e)}")


async def get_ttl(self, key: str) -> int:
    """
    Get TTL for key.

    Args:
        key: Cache key

    Returns:
        TTL in seconds (-1 = no expiry, -2 = key doesn't exist)
    """
    try:
        return await self.client.ttl(key)
    except Exception as e:
        self.logger.error(f"Get TTL failed for key {key}: {e}")
        raise BotDatabaseError(f"Redis TTL failed: {str(e)}")

async def expire(self, key: str, seconds: int) -> bool:
    """
    Set expiration for key.

    Args:
        key: Cache key
        seconds: Seconds until expiration

    Returns:
        True if expiration was set
    """
    try:
        return await self.client.expire(key, seconds)
    except Exception as e:
        self.logger.error(f"Expire failed for key {key}: {e}")
        raise BotDatabaseError(f"Redis EXPIRE failed: {str(e)}")


async def keys(self, pattern: str = "*") -> List[str]:
    """
    Get keys matching pattern.

    Args:
        pattern: Key pattern (e.g., "signal:*")

    Returns:
        List of matching keys
    """
    try:
        return await self.client.keys(pattern)
    except Exception as e:
        self.logger.error(f"Keys search failed for pattern {pattern}: {e}")
        raise BotDatabaseError(f"Redis KEYS failed: {str(e)}")


async def flush_db(self):
    """Flush current database (delete all keys)."""
    try:
        await self.client.flushdb()
        self.logger.warning("Redis database flushed")
    except Exception as e:
        self.logger.error(f"Flush DB failed: {e}")
        raise BotDatabaseError(f"Redis FLUSHDB failed: {str(e)}")


async def health_check(self) -> Dict[str, Any]:
    """Check Redis health."""
    try:
        # Ping
        ping_response = await self.client.ping()

        # Get info
        info = await self.client.info()

        # Get memory info
        memory_info = await self.client.info("memory")

        return {
            "healthy": True,
            "connected": self._is_connected,
            "ping": ping_response,
            "version": info.get("redis_version"),
            "uptime_seconds": info.get("uptime_in_seconds"),
            "connected_clients": info.get("connected_clients"),
            "used_memory": memory_info.get("used_memory_human"),
            "used_memory_peak": memory_info.get("used_memory_peak_human"),
        }
    except Exception as e:
        return {"healthy": False, "connected": False, "error": str(e)}


async def __aenter__(self):
    """Async context manager entry."""
    await self.connect()
    return self


async def __aexit__(self, exc_type, exc_val, exc_tb):
    """Async context manager exit."""
    await self.disconnect()
