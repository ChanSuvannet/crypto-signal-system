# ============================================
# Crypto Trading Signal System
# backed/bots/shared/database/mysql_client.py
# Deception: Async MySQL database client using aiomysql and SQLAlchemy.
# ============================================

import asyncio
from typing import Optional, List, Dict, Any, Type
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy import text, select, insert, update, delete
from sqlalchemy.orm import DeclarativeBase

from ..core.config import Config
from ..core.logger import get_logger
from ..core.exceptions import BotDatabaseError, BotConnectionError, retry_on_error

class MySQLClient:
    """
    Async MySQL client for database operations.

    Features:
    - Connection pooling
    - Automatic reconnection
    - Transaction management
    - Query builder integration
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize MySQL client.

        Args:
            config: Configuration instance
        """
        self.config = config or Config()
        self.logger = get_logger("mysql_client")

        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None
        self._is_connected = False

    async def connect(self):
        """Establish database connection."""
        if self._is_connected:
            self.logger.warning("MySQL client is already connected")
            return

        try:
            # Get database URL
            db_url = self.config.get_database_url("mysql")

            # Create async engine
            self.engine = create_async_engine(
                db_url,
                echo=self.config.is_debug(),
                pool_size=self.config.get("DB_POOL_MAX", 10),
                max_overflow=self.config.get("DB_POOL_MAX", 10) * 2,
                pool_timeout=30,
                pool_recycle=3600,  # Recycle connections after 1 hour
                pool_pre_ping=True,  # Verify connections before using
            )

            # Create session factory
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )

            # Test connection
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))

            self._is_connected = True
            self.logger.info("✓ Connected to MySQL database")

        except Exception as e:
            self.logger.error(f"Failed to connect to MySQL: {e}")
            raise BotConnectionError(
                f"MySQL connection failed: {str(e)}", service="MySQL"
            ) from e

    async def disconnect(self):
        """Close database connection."""
        if not self._is_connected:
            return

        try:
            if self.engine:
                await self.engine.dispose()

            self._is_connected = False
            self.logger.info("✓ Disconnected from MySQL database")

        except Exception as e:
            self.logger.error(f"Error disconnecting from MySQL: {e}")

    @asynccontextmanager
    async def session(self):
        """
        Get database session context manager.

        Usage:
            async with client.session() as session:
                result = await session.execute(query)
        """
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
        """
        Execute raw SQL query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Query result
        """
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

    @retry_on_error(max_attempts=3)
    async def fetch_one(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch single row.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Single row as dictionary or None
        """
        try:
            async with self.session() as session:
                result = await session.execute(text(query), params or {})
                row = result.fetchone()
                return dict(row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Fetch one failed: {e}")
            raise BotDatabaseError(f"Fetch one failed: {str(e)}", query=query) from e

    @retry_on_error(max_attempts=3)
    async def fetch_all(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch all rows.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of rows as dictionaries
        """
        try:
            async with self.session() as session:
                result = await session.execute(text(query), params or {})
                rows = result.fetchall()

                return [dict(row._mapping) for row in rows]

        except Exception as e:
            self.logger.error(f"Fetch all failed: {e}")
            raise BotDatabaseError(f"Fetch all failed: {str(e)}", query=query) from e

    async def insert_one(
        self, table: Type[DeclarativeBase], data: Dict[str, Any]
    ) -> Any:
        """
        Insert single row using SQLAlchemy model.

        Args:
            table: SQLAlchemy model class
            data: Data to insert

        Returns:
            Inserted row ID
        """
        try:
            async with self.session() as session:
                stmt = insert(table).values(**data)
                result = await session.execute(stmt)
                await session.commit()
                return result.inserted_primary_key[0]

        except Exception as e:
            self.logger.error(f"Insert failed: {e}")
            raise BotDatabaseError(
                f"Insert failed: {str(e)}", table=table.__tablename__
            ) from e

    async def insert_many(
        self, table: Type[DeclarativeBase], data: List[Dict[str, Any]]
    ) -> int:
        """
        Insert multiple rows.

        Args:
            table: SQLAlchemy model class
            data: List of data dictionaries

        Returns:
            Number of rows inserted
        """
        try:
            async with self.session() as session:
                stmt = insert(table)
                await session.execute(stmt, data)
                await session.commit()
                return len(data)

        except Exception as e:
            self.logger.error(f"Bulk insert failed: {e}")
            raise BotDatabaseError(
                f"Bulk insert failed: {str(e)}", table=table.__tablename__
            )

    async def update_one(
        self,
        table: Type[DeclarativeBase],
        filters: Dict[str, Any],
        data: Dict[str, Any],
    ) -> int:
        """
        Update single row.

        Args:
            table: SQLAlchemy model class
            filters: Filter conditions
            data: Data to update

        Returns:
            Number of rows updated
        """
        try:
            async with self.session() as session:
                stmt = (
                    update(table)
                    .where(*[getattr(table, k) == v for k, v in filters.items()])
                    .values(**data)
                )
                result = await session.execute(stmt)
                await session.commit()
                return result.rowcount

        except Exception as e:
            self.logger.error(f"Update failed: {e}")
            raise BotDatabaseError(
                f"Update failed: {str(e)}", table=table.__tablename__
            ) from e

    async def delete_one(
        self, table: Type[DeclarativeBase], filters: Dict[str, Any]
    ) -> int:
        """
        Delete rows.

        Args:
            table: SQLAlchemy model class
            filters: Filter conditions

        Returns:
            Number of rows deleted
        """
        try:
            async with self.session() as session:
                stmt = delete(table).where(
                    *[getattr(table, k) == v for k, v in filters.items()]
                )
                result = await session.execute(stmt)
                await session.commit()
                return result.rowcount

        except Exception as e:
            self.logger.error(f"Delete failed: {e}")
            raise BotDatabaseError(
                f"Delete failed: {str(e)}", table=table.__tablename__
            ) from e

    async def select(
        self,
        table: Type[DeclarativeBase],
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
    ) -> List[Any]:
        """
        Select rows with filters.

        Args:
            table: SQLAlchemy model class
            filters: Filter conditions
            limit: Maximum number of rows
            offset: Number of rows to skip
            order_by: Column to order by

        Returns:
            List of model instances
        """
        try:
            async with self.session() as session:
                stmt = select(table)

                # Apply filters
                if filters:
                    for key, value in filters.items():
                        stmt = stmt.where(getattr(table, key) == value)

                # Apply ordering
                if order_by:
                    if order_by.startswith("-"):
                        stmt = stmt.order_by(getattr(table, order_by[1:]).desc())
                    else:
                        stmt = stmt.order_by(getattr(table, order_by))

                # Apply pagination
                if offset:
                    stmt = stmt.offset(offset)
                if limit:
                    stmt = stmt.limit(limit)

                result = await session.execute(stmt)
                return list(result.scalars().all())

        except Exception as e:
            self.logger.error(f"Select failed: {e}")
            raise BotDatabaseError(
                f"Select failed: {str(e)}", table=table.__tablename__
            ) from e

    async def count(
        self, table: Type[DeclarativeBase], filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count rows.

        Args:
            table: SQLAlchemy model class
            filters: Filter conditions

        Returns:
            Number of rows
        """
        try:
            from sqlalchemy import func
            
            async with self.session() as session:
                stmt = select(func.count()).select_from(table)

                if filters:
                    for key, value in filters.items():
                        stmt = stmt.where(getattr(table, key) == value)

                result = await session.execute(stmt)
                return result.scalar()

        except Exception as e:
            self.logger.error(f"Count failed: {e}")
            raise BotDatabaseError(
                f"Count failed: {str(e)}", table=table.__tablename__
            ) from e

    async def health_check(self) -> Dict[str, Any]:
        """
        Check database health.

        Returns:
            Health check results
        """
        try:
            async with self.session() as session:
                # Test query
                result = await session.execute(text("SELECT 1 as health"))
                row = result.fetchone()

                # Get connection pool stats
                pool = self.engine.pool

                return {
                    "healthy": True,
                    "connected": self._is_connected,
                    "pool_size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
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
