# Crypto Trading Signal System
# backed/bots/shared/database/timescale_client.py
# Deception: Async PostgreSQL/TimescaleDB client for time-series data.
# ============================================

import asyncio
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy import text

from ..core.config import Config
from ..core.logger import get_logger
from ..core.exceptions import BotDatabaseError, BotConnectionError, retry_on_error


class TimescaleClient:
    """
    Async TimescaleDB client for time-series operations.

    Features:
    - Hypertable management
    - Time-based queries
    - Continuous aggregates
    - Data retention policies
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize TimescaleDB client.

        Args:
            config: Configuration instance
        """
        self.config = config or Config()
        self.logger = get_logger("timescale_client")

        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None
        self._is_connected = False

    async def connect(self):
        """Establish database connection."""
        if self._is_connected:
            self.logger.warning("TimescaleDB client is already connected")
            return

        try:
            # Get database URL
            db_url = self.config.get_database_url("timescale")

            # Create async engine
            self.engine = create_async_engine(
                db_url,
                echo=self.config.is_debug(),
                pool_size=self.config.get("DB_POOL_MAX", 10),
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=3600,
                pool_pre_ping=True,
            )

            # Create session factory
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            # Test connection and verify TimescaleDB
            async with self.engine.begin() as conn:
                result = await conn.execute(
                    text(
                        "SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'"
                    )
                )
                if version := result.scalar():
                    self.logger.info(f"✓ Connected to TimescaleDB {version}")
                else:
                    self.logger.warning("TimescaleDB extension not found")

            self._is_connected = True

        except Exception as e:
            self.logger.error(f"Failed to connect to TimescaleDB: {e}")
            raise BotConnectionError(
                f"TimescaleDB connection failed: {str(e)}", service="TimescaleDB"
            ) from e

    async def disconnect(self):
        """Close database connection."""
        if not self._is_connected:
            return

        try:
            if self.engine:
                await self.engine.dispose()

            self._is_connected = False
            self.logger.info("✓ Disconnected from TimescaleDB")

        except Exception as e:
            self.logger.error(f"Error disconnecting from TimescaleDB: {e}")

    @asynccontextmanager
    async def session(self):
        """Get database session context manager."""
        if not self._is_connected:
            await self.connect()

        async with self.session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                self.logger.error(f"Session error: {e}")
                raise
            finally:
                await session.close()

    @retry_on_error(max_attempts=3)
    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute raw SQL query."""
        try:
            async with self.session() as session:
                result = await session.execute(text(query), params or {})
                await session.commit()
                return result
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            raise BotDatabaseError(
                f"Query execution failed: {str(e)}", query=query
            ) from e

    async def insert_price_data(
        self,
        symbol: str,
        timeframe: str,
        timestamp: datetime,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: float,
    ):
        """
        Insert OHLCV price data.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe (1m, 5m, 1h, etc.)
            timestamp: Data timestamp
            open: Open price
            high: High price
            low: Low price
            close: Close price
            volume: Trading volume
        """
        query = """
            INSERT INTO price_data (time, symbol, timeframe, open, high, low, close, volume)
            VALUES (:time, :symbol, :timeframe, :open, :high, :low, :close, :volume)
            ON CONFLICT (time, symbol, timeframe) DO UPDATE
            SET open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume
        """

        params = {
            "time": timestamp,
            "symbol": symbol,
            "timeframe": timeframe,
            "open": open,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }

        await self.execute(query, params)

    async def insert_price_data_bulk(self, data: List[Dict[str, Any]]) -> int:
        """
        Insert multiple price data rows.

        Args:
            data: List of price data dictionaries

        Returns:
            Number of rows inserted
        """
        query = """
            INSERT INTO price_data (time, symbol, timeframe, open, high, low, close, volume)
            VALUES (:time, :symbol, :timeframe, :open, :high, :low, :close, :volume)
            ON CONFLICT (time, symbol, timeframe) DO NOTHING
        """

        try:
            async with self.session() as session:
                await session.execute(text(query), data)
                await session.commit()
                return len(data)
        except Exception as e:
            self.logger.error(f"Bulk insert failed: {e}")
            raise BotDatabaseError(f"Bulk insert failed: {str(e)}") from e

    async def get_latest_price(
        self, symbol: str, timeframe: str = "1m"
    ) -> Optional[Dict[str, Any]]:
        """
        Get latest price data for symbol.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe

        Returns:
            Latest price data or None
        """
        query = """
            SELECT * FROM price_data
            WHERE symbol = :symbol AND timeframe = :timeframe
            ORDER BY time DESC
            LIMIT 1
        """

        try:
            async with self.session() as session:
                result = await session.execute(
                    text(query), {"symbol": symbol, "timeframe": timeframe}
                )
                row = result.fetchone()

                return dict(row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Get latest price failed: {e}")
            raise BotDatabaseError(f"Get latest price failed: {str(e)}") from e

    async def get_price_history(
        self,
        symbol: str,
        timeframe: str = "1h",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """
        Get historical price data.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            start_time: Start timestamp
            end_time: End timestamp
            limit: Maximum number of rows

        Returns:
            List of price data
        """
        conditions = ["symbol = :symbol", "timeframe = :timeframe"]
        params = {"symbol": symbol, "timeframe": timeframe}

        if start_time:
            conditions.append("time >= :start_time")
            params["start_time"] = start_time

        if end_time:
            conditions.append("time <= :end_time")
            params["end_time"] = end_time

        query = f"""
            SELECT * FROM price_data
            WHERE {' AND '.join(conditions)}
            ORDER BY time DESC
            LIMIT :limit
        """
        params["limit"] = limit

        try:
            async with self.session() as session:
                result = await session.execute(text(query), params)
                rows = result.fetchall()
                return [dict(row._mapping) for row in rows]
        except Exception as e:
            self.logger.error(f"Get price history failed: {e}")
            raise BotDatabaseError(f"Get price history failed: {str(e)}") from e

    async def get_aggregated_data(
        self,
        symbol: str,
        interval: str = "1 hour",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get time-bucketed aggregated data.

        Args:
            symbol: Trading symbol
            interval: Time bucket interval (e.g., '1 hour', '1 day')
            start_time: Start timestamp
            end_time: End timestamp

        Returns:
            List of aggregated data
        """
        conditions = ["symbol = :symbol"]
        params = {"symbol": symbol, "interval": interval}

        if start_time:
            conditions.append("time >= :start_time")
            params["start_time"] = start_time

        if end_time:
            conditions.append("time <= :end_time")
            params["end_time"] = end_time

        query = f"""
            SELECT
                time_bucket(:interval, time) AS bucket,
                symbol,
                first(open, time) AS open,
                max(high) AS high,
                min(low) AS low,
                last(close, time) AS close,
                sum(volume) AS volume
            FROM price_data
            WHERE {' AND '.join(conditions)}
            GROUP BY bucket, symbol
            ORDER BY bucket DESC
        """

        try:
            async with self.session() as session:
                result = await session.execute(text(query), params)
                rows = result.fetchall()
                return [dict(row._mapping) for row in rows]
        except Exception as e:
            self.logger.error(f"Get aggregated data failed: {e}")
            raise BotDatabaseError(f"Get aggregated data failed: {str(e)}") from e

    async def delete_old_data(self, table: str, older_than_days: int = 180) -> int:
        """
        Delete data older than specified days.

        Args:
            table: Table name
            older_than_days: Delete data older than this many days

        Returns:
            Number of rows deleted
        """
        query = f"""
            DELETE FROM {table}
            WHERE time < NOW() - INTERVAL '{older_than_days} days'
        """

        try:
            result = await self.execute(query)
            return result.rowcount
        except Exception as e:
            self.logger.error(f"Delete old data failed: {e}")
            raise BotDatabaseError(f"Delete old data failed: {str(e)}") from e

    async def health_check(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            async with self.session() as session:
                # Test query
                result = await session.execute(text("SELECT 1 as health"))
                row = result.fetchone()

                # Get TimescaleDB info
                result = await session.execute(
                    text(
                        "SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'"
                    )
                )
                version = result.scalar()

                # Get database size
                result = await session.execute(
                    text("SELECT pg_size_pretty(pg_database_size(current_database()))")
                )
                db_size = result.scalar()

                return {
                    "healthy": True,
                    "connected": self._is_connected,
                    "timescaledb_version": version,
                    "database_size": db_size,
                    "query_test": row[0] == 1,
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
