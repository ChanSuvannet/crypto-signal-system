# ============================================
# Crypto Trading Signal System
# backed/bots/shared/core/base_bot.py
# Deception: Foundation class for all trading bots with common functionality.
# ============================================
import asyncio
import contextlib
import signal
import sys
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import traceback

from .config import Config
from .logger import setup_logger
from .exceptions import BotError, BotConfigError, BotConnectionError


class BaseBot(ABC):
    """
    Abstract base class for all trading bots.

    Provides:
    - Lifecycle management (start, stop, restart)
    - Error handling and recovery
    - Health monitoring
    - Graceful shutdown
    - Automatic reconnection
    """

    def __init__(
        self, bot_name: str, config: Optional[Config] = None, interval: int = 60
    ):
        """
        Initialize base bot.

        Args:
            bot_name: Unique name for this bot
            config: Configuration instance (creates default if None)
            interval: Processing interval in seconds
        """
        self.bot_name = bot_name
        self.config = config or Config()
        self.interval = interval

        # Setup logger
        self.logger = setup_logger(
            name=bot_name,
            log_file=f"logs/{bot_name}.log",
            level=self.config.get("LOG_LEVEL", "INFO"),
        )

        # Bot state
        self._running = False
        self._paused = False
        self._shutdown_event = asyncio.Event()
        self._last_heartbeat = None
        self._error_count = 0
        self._success_count = 0
        self._start_time = None

        # Dependencies (to be initialized by subclasses)
        self.db = None
        self.redis = None
        self.rabbitmq = None

        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()

        self.logger.info(f"🤖 {self.bot_name} initialized")

    def _setup_signal_handlers(self):
        """Setup handlers for graceful shutdown on SIGINT and SIGTERM."""
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.warning(
            f"Received signal {signum}, initiating graceful shutdown..."
        )
        asyncio.create_task(self.stop())

    @abstractmethod
    async def initialize(self):
        """
        Initialize bot resources (databases, connections, etc).
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    async def process(self):
        """
        Main processing logic.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    async def cleanup(self):
        """
        Cleanup resources before shutdown.
        Must be implemented by subclasses.
        """
        pass

    async def start(self):
        """Start the bot."""
        if self._running:
            self.logger.warning(f"{self.bot_name} is already running")
            return

        self.logger.info(f"🚀 Starting {self.bot_name}...")
        self._running = True
        self._start_time = datetime.now(timezone.utc)

        try:
            # Initialize resources
            await self.initialize()
            self.logger.info(f"✓ {self.bot_name} initialized successfully")

            # Start main loop
            await self._run_loop()

        except Exception as e:
            self.logger.error(f"Fatal error in {self.bot_name}: {e}")
            self.logger.error(traceback.format_exc())
            await self.stop()
            sys.exit(1)

    async def stop(self):
        """Stop the bot gracefully."""
        if not self._running:
            return

        self.logger.info(f"🛑 Stopping {self.bot_name}...")
        self._running = False
        self._shutdown_event.set()

        try:
            # Cleanup resources
            await self.cleanup()
            self.logger.info(f"✓ {self.bot_name} stopped successfully")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

        # Log statistics
        self._log_statistics()

    async def pause(self):
        """Pause bot processing."""
        if not self._running:
            self.logger.warning(f"{self.bot_name} is not running")
            return

        self.logger.info(f"⏸️  Pausing {self.bot_name}...")
        self._paused = True

    async def resume(self):
        """Resume bot processing."""
        if not self._paused:
            self.logger.warning(f"{self.bot_name} is not paused")
            return

        self.logger.info(f"▶️  Resuming {self.bot_name}...")
        self._paused = False

    async def restart(self):
        """Restart the bot."""
        self.logger.info(f"🔄 Restarting {self.bot_name}...")
        await self.stop()
        await asyncio.sleep(2)  # Brief pause before restart
        await self.start()

    async def _run_loop(self):
        """Main execution loop with error handling."""
        loop_count = 0

        while self._running:
            try:
                # Check if paused
                if self._paused:
                    await asyncio.sleep(1)
                    continue

                loop_count += 1
                self.logger.debug(f"Loop {loop_count} started")

                # Update heartbeat
                await self._update_heartbeat()

                # Execute main processing
                start_time = datetime.now(timezone.utc)
                await self.process()
                elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

                # Record metrics
                self._success_count += 1
                self._error_count = 0  # Reset error count on success

                self.logger.debug(f"Loop {loop_count} completed in {elapsed:.2f}s")

                # Wait for next interval
                await self._wait_interval()

            except BotError as e:
                # Custom bot error - handle gracefully
                self.logger.error(f"Bot error in loop {loop_count}: {e}")
                self._error_count += 1
                await self._handle_error(e)

            except Exception as e:
                # Unexpected error
                self.logger.error(f"Unexpected error in loop {loop_count}: {e}")
                self.logger.error(traceback.format_exc())
                self._error_count += 1
                await self._handle_error(e)

            # Check if too many consecutive errors
            if self._error_count >= self.config.get("MAX_CONSECUTIVE_ERRORS", 5):
                self.logger.critical(
                    f"Too many consecutive errors ({self._error_count}), stopping bot"
                )
                await self.stop()
                break

    async def _wait_interval(self):
        """Wait for next processing interval or shutdown signal."""
        with contextlib.suppress(asyncio.TimeoutError):
            await asyncio.wait_for(self._shutdown_event.wait(), timeout=self.interval)

    async def _handle_error(self, error: Exception):
        """
        Handle errors with retry logic.

        Args:
            error: The exception that occurred
        """
        retry_delay = min(60, 5 * self._error_count)  # Max 60 seconds
        self.logger.warning(f"Retrying in {retry_delay} seconds...")

        # Record error in database if available
        await self._record_error(error)

        await asyncio.sleep(retry_delay)

    async def _update_heartbeat(self):
        """Update bot heartbeat timestamp."""
        self._last_heartbeat = datetime.now(timezone.utc)

        # Update in database if available
        if self.db:
            try:
                await self._record_heartbeat()
            except Exception as e:
                self.logger.warning(f"Failed to record heartbeat: {e}")

    async def _record_heartbeat(self):
        """Record heartbeat in database."""
        # This will be implemented when we have database clients
        pass

    async def _record_error(self, error: Exception):
        """Record error in database."""
        # This will be implemented when we have database clients
        pass

    def _log_statistics(self):
        """Log bot statistics."""
        if self._start_time:
            uptime = datetime.now(timezone.utc) - self._start_time
            hours = uptime.total_seconds() / 3600

            self.logger.info(
                f"""
╔════════════════════════════════════════════╗
║         {self.bot_name} Statistics         ║
╚════════════════════════════════════════════╝
  Uptime:           {uptime}
  Success Count:    {self._success_count}
  Error Count:      {self._error_count}
  Success Rate:     {self._calculate_success_rate():.2f}%
  Avg per Hour:     {self._success_count / hours:.2f}
════════════════════════════════════════════
            """
            )

    def _calculate_success_rate(self) -> float:
        """Calculate success rate percentage."""
        total = self._success_count + self._error_count
        return 0.0 if total == 0 else (self._success_count / total) * 100

    def get_status(self) -> Dict[str, Any]:
        """
        Get current bot status.

        Returns:
            Dictionary with bot status information
        """
        uptime = None
        if self._start_time:
            uptime = (datetime.now(timezone.utc) - self._start_time).total_seconds()

        return {
            "bot_name": self.bot_name,
            "running": self._running,
            "paused": self._paused,
            "uptime_seconds": uptime,
            "last_heartbeat": self._last_heartbeat,
            "success_count": self._success_count,
            "error_count": self._error_count,
            "success_rate": self._calculate_success_rate(),
            "start_time": self._start_time,
        }

    def is_healthy(self) -> bool:
        """
        Check if bot is healthy.

        Returns:
            True if bot is running and has recent heartbeat
        """
        if not self._running:
            return False

        if self._last_heartbeat is None:
            return False

        # Check if heartbeat is recent (within 2x interval)
        time_since_heartbeat = (
            datetime.now(timezone.utc) - self._last_heartbeat
        ).total_seconds()
        return time_since_heartbeat < (self.interval * 2)

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check.

        Returns:
            Dictionary with health check results
        """
        health = {
            "healthy": self.is_healthy(),
            "status": self.get_status(),
            "checks": {},
        }

        # Check database connection
        if self.db:
            try:
                health["checks"]["database"] = await self._check_database_health()
            except Exception as e:
                health["checks"]["database"] = {"healthy": False, "error": str(e)}

        # Check Redis connection
        if self.redis:
            try:
                health["checks"]["redis"] = await self._check_redis_health()
            except Exception as e:
                health["checks"]["redis"] = {"healthy": False, "error": str(e)}

        # Check RabbitMQ connection
        if self.rabbitmq:
            try:
                health["checks"]["rabbitmq"] = await self._check_rabbitmq_health()
            except Exception as e:
                health["checks"]["rabbitmq"] = {"healthy": False, "error": str(e)}

        return health

    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database connection health."""
        # Will be implemented with database clients
        return {"healthy": True}

    async def _check_redis_health(self) -> Dict[str, Any]:
        """Check Redis connection health."""
        # Will be implemented with Redis client
        return {"healthy": True}

    async def _check_rabbitmq_health(self) -> Dict[str, Any]:
        """Check RabbitMQ connection health."""
        # Will be implemented with RabbitMQ client
        return {"healthy": True}

    def __repr__(self) -> str:
        """String representation of bot."""
        status = "running" if self._running else "stopped"
        if self._paused:
            status = "paused"
        return f"<{self.__class__.__name__}(name={self.bot_name}, status={status})>"
