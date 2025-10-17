# ============================================
# Crypto Trading Signal System
# backed/bots/market-data-bot/src/main.py
# Deception: Market Data Bot - Main Entry Point: Collects real-time market data from cryptocurrency exchanges
# ============================================

import asyncio
import os
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import yaml

# Add parent directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared" / "python"))


from collector import MarketDataCollector

from backend.bots.shared.core.base_bot import BaseBot
from backend.shared_libs.python.crypto_trading_shared.enums import (BotStatus,
                                                                    BotType)
from backend.shared_libs.python.crypto_trading_shared.types import \
    BotHealthMetrics


class MarketDataBot(BaseBot):
    """
    Market Data Collection Bot
    Collects OHLCV, orderbook, and trade data from exchanges
    """

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the market data bot"""
        super().__init__(
            bot_name="market-data-bot",
            bot_type=BotType.MARKET_DATA,
            config_path=config_path,
        )

        self.collector: MarketDataCollector = None
        self.tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()

        self.logger.info("Market Data Bot initialized")

    async def setup(self):
        """Setup bot components"""
        try:
            self.logger.info("Setting up Market Data Bot...")

            # Initialize collector
            self.collector = MarketDataCollector(
                config=self.config,
                db_clients=self.db_clients,
                mq_client=self.mq_client,
                logger=self.logger,
            )

            await self.collector.setup()

            # Setup signal handlers for graceful shutdown
            self._setup_signal_handlers()

            self.logger.info("Market Data Bot setup complete")

        except Exception as e:
            self.logger.error(f"Setup failed: {e}", exc_info=True)
            raise

    async def start(self):
        """Start the bot"""
        try:
            self.status = BotStatus.STARTING
            self.logger.info("Starting Market Data Bot...")

            # Start collector
            await self.collector.start()

            # Create collection tasks
            self.tasks = [
                asyncio.create_task(self._collect_ohlcv()),
                asyncio.create_task(self._collect_orderbook()),
                asyncio.create_task(self._collect_trades()),
                asyncio.create_task(self._process_data()),
                asyncio.create_task(self._health_check()),
            ]

            # Add WebSocket streaming if enabled
            if self.config.get("websocket", {}).get("enabled", False):
                self.tasks.append(asyncio.create_task(self._stream_websocket()))

            self.status = BotStatus.RUNNING
            self.logger.info("✅ Market Data Bot started successfully")

            # Wait for shutdown signal
            await self._shutdown_event.wait()

        except Exception as e:
            self.logger.error(f"Start failed: {e}", exc_info=True)
            self.status = BotStatus.ERROR
            raise

    async def _collect_ohlcv(self):
        """Collect OHLCV data periodically"""
        interval = (
            self.config.get("collection", {}).get("intervals", {}).get("ohlcv", 60)
        )

        self.logger.info(f"OHLCV collection started (interval: {interval}s)")

        while not self._shutdown_event.is_set():
            try:
                await self.collector.collect_ohlcv()
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"OHLCV collection error: {e}", exc_info=True)
                await asyncio.sleep(interval)

    async def _collect_orderbook(self):
        """Collect orderbook data periodically"""
        if not self.config.get("features", {}).get("orderbook_collection", True):
            return

        interval = (
            self.config.get("collection", {}).get("intervals", {}).get("orderbook", 5)
        )

        self.logger.info(f"Orderbook collection started (interval: {interval}s)")

        while not self._shutdown_event.is_set():
            try:
                await self.collector.collect_orderbook()
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Orderbook collection error: {e}", exc_info=True)
                await asyncio.sleep(interval)

    async def _collect_trades(self):
        """Collect recent trades periodically"""
        if not self.config.get("features", {}).get("trade_collection", True):
            return

        interval = (
            self.config.get("collection", {}).get("intervals", {}).get("trades", 10)
        )

        self.logger.info(f"Trade collection started (interval: {interval}s)")

        while not self._shutdown_event.is_set():
            try:
                await self.collector.collect_trades()
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Trade collection error: {e}", exc_info=True)
                await asyncio.sleep(interval)

    async def _stream_websocket(self):
        """Stream data via WebSocket"""
        self.logger.info("WebSocket streaming started")

        while not self._shutdown_event.is_set():
            try:
                await self.collector.stream_websocket()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"WebSocket streaming error: {e}", exc_info=True)

                # Reconnect after delay
                reconnect_delay = self.config.get("websocket", {}).get(
                    "reconnect_interval", 5
                )
                self.logger.info(f"Reconnecting in {reconnect_delay}s...")
                await asyncio.sleep(reconnect_delay)

    async def _process_data(self):
        """Process collected data"""
        batch_interval = self.config.get("processing", {}).get("batch_interval", 10)

        self.logger.info(f"Data processing started (interval: {batch_interval}s)")

        while not self._shutdown_event.is_set():
            try:
                await self.collector.process_batch()
                await asyncio.sleep(batch_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Data processing error: {e}", exc_info=True)
                await asyncio.sleep(batch_interval)

    async def _health_check(self):
        """Periodic health check"""
        interval = self.config.get("monitoring", {}).get("health_check_interval", 60)

        self.logger.info(f"Health check started (interval: {interval}s)")

        while not self._shutdown_event.is_set():
            try:
                # Get health metrics
                health = await self.get_health()

                # Log health status
                self.logger.info(
                    f"Health: {health.health_score}/100 | "
                    f"Status: {health.status.value} | "
                    f"Processed: {health.messages_processed} | "
                    f"Failed: {health.messages_failed}"
                )

                # Check for issues
                if health.health_score < 50:
                    self.logger.warning(f"Low health score: {health.health_score}")

                # Update Redis with health status
                await self._update_health_status(health)

                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check error: {e}", exc_info=True)
                await asyncio.sleep(interval)

    async def _update_health_status(self, health: BotHealthMetrics):
        """Update health status in Redis"""
        try:
            health_key = f"bot:status:{self.bot_name}"
            await self.db_clients["redis"].setex(
                health_key, 120, health.model_dump_json()  # Expire after 2 minutes
            )
        except Exception as e:
            self.logger.error(f"Failed to update health status: {e}")

    async def stop(self):
        """Stop the bot gracefully"""
        try:
            self.logger.info("Stopping Market Data Bot...")
            self.status = BotStatus.STOPPED

            # Signal shutdown
            self._shutdown_event.set()

            # Cancel all tasks
            for task in self.tasks:
                if not task.done():
                    task.cancel()

            # Wait for tasks to complete
            if self.tasks:
                await asyncio.gather(*self.tasks, return_exceptions=True)

            # Stop collector
            if self.collector:
                await self.collector.stop()

            # Close database connections
            await self.cleanup()

            self.logger.info("✅ Market Data Bot stopped successfully")

        except Exception as e:
            self.logger.error(f"Stop error: {e}", exc_info=True)
            raise

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""

        def signal_handler(sig, frame):
            self.logger.info(f"Received signal {sig}, shutting down...")
            self._shutdown_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def get_health(self) -> BotHealthMetrics:
        """Get current health metrics"""
        uptime = (
            (datetime.now() - self.started_at).total_seconds() if self.started_at else 0
        )

        # Get collector metrics
        collector_metrics = await self.collector.get_metrics() if self.collector else {}

        return BotHealthMetrics(
            bot_name=self.bot_name,
            bot_type=self.bot_type.value,
            status=self.status,
            started_at=self.started_at or datetime.now(),
            last_heartbeat=datetime.now(),
            uptime_seconds=int(uptime),
            messages_processed=collector_metrics.get("total_collected", 0),
            messages_failed=collector_metrics.get("total_errors", 0),
            success_rate=collector_metrics.get("success_rate", 100.0),
            avg_processing_time_ms=collector_metrics.get("avg_latency_ms", 0.0),
            error_count=collector_metrics.get("total_errors", 0),
            health_score=self._calculate_health_score(collector_metrics),
        )

    def _calculate_health_score(self, metrics: Dict) -> int:
        """Calculate health score (0-100)"""
        score = 100

        # Penalize for errors
        error_rate = metrics.get("error_rate", 0)
        score -= min(error_rate * 2, 50)  # Max 50 points penalty

        # Penalize for high latency
        avg_latency = metrics.get("avg_latency_ms", 0)
        if avg_latency > 1000:
            score -= min((avg_latency - 1000) / 100, 30)  # Max 30 points penalty

        # Penalize if not collecting data
        last_collection = metrics.get("last_collection_seconds", 0)
        if last_collection > 300:  # No data for 5 minutes
            score -= 50

        return max(0, min(100, int(score)))


async def main():
    """Main entry point"""
    print("=" * 80)
    print("🤖 CRYPTO SIGNAL SYSTEM - MARKET DATA BOT")
    print("=" * 80)
    print()

    # Get config path from environment or use default
    config_path = os.getenv("CONFIG_PATH", "config.yaml")

    # Create and run bot
    bot = MarketDataBot(config_path=config_path)

    try:
        # Setup
        await bot.setup()

        # Start
        await bot.start()

    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        # Cleanup
        await bot.stop()
        print("\n✅ Market Data Bot shutdown complete")


if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())
