
# ============================================
# Crypto Trading Signal System
# backed/bots/market-data-bot/src/collector.py
# Deception: Market Data Collector: Coordinates data collection from exchanges
# ============================================

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

import ccxt.async_support as ccxt
from exchanges.binance import BinanceConnector
from exchanges.coinbase import CoinbaseConnector
from exchanges.kraken import KrakenConnector
from processors.ohlcv_processor import OHLCVProcessor
from processors.orderbook_processor import OrderBookProcessor
from processors.trade_processor import TradeProcessor
from storage.timescale_writer import TimescaleWriter

from backend.shared_libs.python.crypto_trading_shared.types import (
    OHLCVData, OrderBookData)


class MarketDataCollector:
    """
    Coordinates market data collection from multiple exchanges
    """

    def __init__(self, config: Dict, db_clients: Dict, mq_client, logger):
        """Initialize collector"""
        self.config = config
        self.db_clients = db_clients
        self.mq_client = mq_client
        self.logger = logger

        # Exchange connectors
        self.exchanges: Dict[str, any] = {}

        # Data processors
        self.ohlcv_processor = OHLCVProcessor(config, logger)
        self.orderbook_processor = OrderBookProcessor(config, logger)
        self.trade_processor = TradeProcessor(config, logger)

        # Storage writer
        self.writer = TimescaleWriter(db_clients["timescaledb"], logger)

        # Metrics
        self.metrics = {
            "total_collected": 0,
            "total_errors": 0,
            "last_collection": None,
            "latency_samples": [],
        }

        # Data buffers for batch processing
        self.ohlcv_buffer: List[OHLCVData] = []
        self.orderbook_buffer: List[OrderBookData] = []
        self.trade_buffer: List = []

        self.logger.info("MarketDataCollector initialized")

    async def setup(self):
        """Setup exchange connections"""
        try:
            self.logger.info("Setting up exchange connectors...")

            # Initialize enabled exchanges
            exchange_config = self.config.get("exchanges", {})

            if exchange_config.get("binance", {}).get("enabled", False):
                self.exchanges["binance"] = BinanceConnector(
                    exchange_config["binance"], self.logger
                )
                await self.exchanges["binance"].connect()
                self.logger.info("✅ Binance connector ready")

            if exchange_config.get("coinbase", {}).get("enabled", False):
                self.exchanges["coinbase"] = CoinbaseConnector(
                    exchange_config["coinbase"], self.logger
                )
                await self.exchanges["coinbase"].connect()
                self.logger.info("✅ Coinbase connector ready")

            if exchange_config.get("kraken", {}).get("enabled", False):
                self.exchanges["kraken"] = KrakenConnector(
                    exchange_config["kraken"], self.logger
                )
                await self.exchanges["kraken"].connect()
                self.logger.info("✅ Kraken connector ready")

            if not self.exchanges:
                raise ValueError("No exchanges enabled in configuration")

            self.logger.info(
                f"Exchange connectors setup complete ({len(self.exchanges)} exchanges)"
            )

        except Exception as e:
            self.logger.error(f"Setup failed: {e}", exc_info=True)
            raise

    async def start(self):
        """Start collectors"""
        self.logger.info("Starting data collection...")
        # Initialization complete, actual collection happens in main loop

    async def collect_ohlcv(self):
        """Collect OHLCV data from all exchanges"""
        start_time = datetime.now()

        try:
            symbols = self.config.get("collection", {}).get("symbols", [])
            timeframes = self.config.get("collection", {}).get("timeframes", [])

            # Get primary exchange (highest priority)
            primary_exchange = self._get_primary_exchange()

            if not primary_exchange:
                self.logger.warning("No primary exchange available")
                return

            collected_count = 0

            # Collect for each symbol and timeframe
            for symbol in symbols:
                for timeframe in timeframes:
                    try:
                        # Fetch OHLCV data
                        ohlcv_data = await primary_exchange.fetch_ohlcv(
                            symbol=symbol,
                            timeframe=timeframe,
                            limit=1,  # Get latest candle
                        )

                        if ohlcv_data:
                            # Process and buffer
                            processed = await self.ohlcv_processor.process(ohlcv_data)
                            self.ohlcv_buffer.extend(processed)
                            collected_count += len(processed)

                    except Exception as e:
                        self.logger.error(
                            f"Error collecting OHLCV for {symbol} {timeframe}: {e}"
                        )
                        self.metrics["total_errors"] += 1

            # Update metrics
            self.metrics["total_collected"] += collected_count
            self.metrics["last_collection"] = datetime.now()

            # Calculate latency
            latency = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics["latency_samples"].append(latency)

            # Keep only last 100 samples
            if len(self.metrics["latency_samples"]) > 100:
                self.metrics["latency_samples"] = self.metrics["latency_samples"][-100:]

            self.logger.debug(
                f"OHLCV collection complete: {collected_count} candles in {latency:.2f}ms"
            )

            # Write to cache
            await self._cache_latest_prices()

        except Exception as e:
            self.logger.error(f"OHLCV collection failed: {e}", exc_info=True)
            self.metrics["total_errors"] += 1

    async def collect_orderbook(self):
        """Collect orderbook data"""
        start_time = datetime.now()

        try:
            symbols = self.config.get("collection", {}).get("symbols", [])
            primary_exchange = self._get_primary_exchange()

            if not primary_exchange:
                return

            collected_count = 0

            for symbol in symbols:
                try:
                    # Fetch orderbook
                    orderbook = await primary_exchange.fetch_orderbook(
                        symbol=symbol, limit=20  # Top 20 bids/asks
                    )

                    if orderbook:
                        # Process and buffer
                        processed = await self.orderbook_processor.process(orderbook)
                        if processed:
                            self.orderbook_buffer.append(processed)
                            collected_count += 1

                except Exception as e:
                    self.logger.error(f"Error collecting orderbook for {symbol}: {e}")
                    self.metrics["total_errors"] += 1

            # Update metrics
            self.metrics["total_collected"] += collected_count

            latency = (datetime.now() - start_time).total_seconds() * 1000
            self.logger.debug(
                f"Orderbook collection complete: {collected_count} books in {latency:.2f}ms"
            )

        except Exception as e:
            self.logger.error(f"Orderbook collection failed: {e}", exc_info=True)
            self.metrics["total_errors"] += 1

    async def collect_trades(self):
        """Collect recent trades"""
        start_time = datetime.now()

        try:
            symbols = self.config.get("collection", {}).get("symbols", [])
            primary_exchange = self._get_primary_exchange()

            if not primary_exchange:
                return

            collected_count = 0

            for symbol in symbols:
                try:
                    # Fetch recent trades
                    trades = await primary_exchange.fetch_trades(
                        symbol=symbol, limit=100
                    )

                    if trades:
                        # Process and buffer
                        processed = await self.trade_processor.process(trades)
                        self.trade_buffer.extend(processed)
                        collected_count += len(processed)

                except Exception as e:
                    self.logger.error(f"Error collecting trades for {symbol}: {e}")
                    self.metrics["total_errors"] += 1

            # Update metrics
            self.metrics["total_collected"] += collected_count

            latency = (datetime.now() - start_time).total_seconds() * 1000
            self.logger.debug(
                f"Trade collection complete: {collected_count} trades in {latency:.2f}ms"
            )

        except Exception as e:
            self.logger.error(f"Trade collection failed: {e}", exc_info=True)
            self.metrics["total_errors"] += 1

    async def stream_websocket(self):
        """Stream real-time data via WebSocket"""
        try:
            primary_exchange = self._get_primary_exchange()

            if not primary_exchange or not hasattr(primary_exchange, "stream"):
                self.logger.warning("WebSocket streaming not supported")
                return

            symbols = self.config.get("collection", {}).get("priority_symbols", [])

            self.logger.info(f"Starting WebSocket stream for {len(symbols)} symbols")

            # Start streaming (this will run continuously)
            await primary_exchange.stream(
                symbols=symbols, callback=self._handle_websocket_data
            )

        except Exception as e:
            self.logger.error(f"WebSocket streaming error: {e}", exc_info=True)
            raise

    async def _handle_websocket_data(self, data: Dict):
        """Handle incoming WebSocket data"""
        try:
            data_type = data.get("type")

            if data_type == "trade":
                # Process trade
                processed = await self.trade_processor.process([data])
                self.trade_buffer.extend(processed)

            elif data_type == "ticker":
                # Cache ticker data
                await self._cache_ticker(data)

            elif data_type == "kline":
                # Process candlestick
                processed = await self.ohlcv_processor.process([data])
                self.ohlcv_buffer.extend(processed)

            self.metrics["total_collected"] += 1

        except Exception as e:
            self.logger.error(f"WebSocket data handling error: {e}")
            self.metrics["total_errors"] += 1

    async def process_batch(self):
        """Process and write buffered data in batches"""
        try:
            batch_size = self.config.get("processing", {}).get("batch_size", 100)

            # Process OHLCV buffer
            if len(self.ohlcv_buffer) >= batch_size:
                batch = self.ohlcv_buffer[:batch_size]
                self.ohlcv_buffer = self.ohlcv_buffer[batch_size:]

                await self.writer.write_ohlcv_batch(batch)
                await self._publish_to_queue(batch, "ohlcv")

                self.logger.debug(f"Processed OHLCV batch: {len(batch)} records")

            # Process orderbook buffer
            if len(self.orderbook_buffer) >= batch_size // 10:  # Smaller batches
                batch = self.orderbook_buffer[: batch_size // 10]
                self.orderbook_buffer = self.orderbook_buffer[batch_size // 10 :]

                await self.writer.write_orderbook_batch(batch)

                self.logger.debug(f"Processed orderbook batch: {len(batch)} records")

            # Process trade buffer
            if len(self.trade_buffer) >= batch_size:
                batch = self.trade_buffer[:batch_size]
                self.trade_buffer = self.trade_buffer[batch_size:]

                await self.writer.write_trades_batch(batch)

                self.logger.debug(f"Processed trade batch: {len(batch)} records")

        except Exception as e:
            self.logger.error(f"Batch processing error: {e}", exc_info=True)
            self.metrics["total_errors"] += 1

    async def _cache_latest_prices(self):
        """Cache latest prices in Redis"""
        try:
            redis = self.db_clients.get("redis")
            if not redis:
                return

            # Cache latest OHLCV data
            for ohlcv in self.ohlcv_buffer[-10:]:  # Last 10 records
                cache_key = f"price:{ohlcv.symbol}:{ohlcv.timeframe}"
                ttl = (
                    self.config.get("database", {})
                    .get("redis", {})
                    .get("cache_ttl", {})
                    .get("price", 60)
                )

                await redis.setex(cache_key, ttl, ohlcv.model_dump_json())

        except Exception as e:
            self.logger.error(f"Cache update error: {e}")

    async def _cache_ticker(self, ticker: Dict):
        """Cache ticker data"""
        try:
            redis = self.db_clients.get("redis")
            if not redis:
                return

            symbol = ticker.get("symbol")
            cache_key = f"ticker:{symbol}"
            ttl = 60

            await redis.setex(cache_key, ttl, str(ticker))

        except Exception as e:
            self.logger.error(f"Ticker cache error: {e}")

    async def _publish_to_queue(self, data: List, data_type: str):
        """Publish data to RabbitMQ"""
        try:
            if not self.mq_client:
                return

            exchange = (
                self.config.get("rabbitmq", {})
                .get("exchanges", {})
                .get("market_data", "market_data_exchange")
            )

            routing_key = f"market.{data_type}.update"

            # Publish each record
            for record in data:
                message = {
                    "type": data_type,
                    "data": (
                        record.model_dump() if hasattr(record, "model_dump") else record
                    ),
                    "timestamp": datetime.now().isoformat(),
                }

                await self.mq_client.publish(
                    exchange=exchange, routing_key=routing_key, message=message
                )

        except Exception as e:
            self.logger.error(f"Queue publish error: {e}")

    def _get_primary_exchange(self):
        """Get the primary exchange (highest priority)"""
        if not self.exchanges:
            return None

        # Get exchange with highest priority
        exchange_config = self.config.get("exchanges", {})

        primary = None
        min_priority = float("inf")

        for name, exchange in self.exchanges.items():
            priority = exchange_config.get(name, {}).get("priority", 999)
            if priority < min_priority:
                min_priority = priority
                primary = exchange

        return primary

    async def get_metrics(self) -> Dict:
        """Get collector metrics"""
        total = self.metrics["total_collected"]
        errors = self.metrics["total_errors"]

        success_rate = ((total - errors) / total * 100) if total > 0 else 100.0

        # Calculate average latency
        latency_samples = self.metrics.get("latency_samples", [])
        avg_latency = (
            sum(latency_samples) / len(latency_samples) if latency_samples else 0
        )

        if last_collection := self.metrics.get("last_collection"):
            last_collection_seconds = (datetime.now() - last_collection).total_seconds()
        else:
            last_collection_seconds = 0
        return {
            "total_collected": total,
            "total_errors": errors,
            "success_rate": success_rate,
            "error_rate": (errors / total * 100) if total > 0 else 0,
            "avg_latency_ms": avg_latency,
            "last_collection_seconds": last_collection_seconds,
            "buffer_sizes": {
                "ohlcv": len(self.ohlcv_buffer),
                "orderbook": len(self.orderbook_buffer),
                "trades": len(self.trade_buffer),
            },
        }

    async def stop(self):
        
        """Stop collector and cleanup"""
        try:
            self.logger.info("Stopping collector...")

            # Process remaining buffered data
            if self.ohlcv_buffer:
                await self.writer.write_ohlcv_batch(self.ohlcv_buffer)
                self.logger.info(f"Flushed {len(self.ohlcv_buffer)} OHLCV records")

            if self.orderbook_buffer:
                await self.writer.write_orderbook_batch(self.orderbook_buffer)
                self.logger.info(
                    f"Flushed {len(self.orderbook_buffer)} orderbook records"
                )

            if self.trade_buffer:
                await self.writer.write_trades_batch(self.trade_buffer)
                self.logger.info(f"Flushed {len(self.trade_buffer)} trade records")

            # Close exchange connections
            for name, exchange in self.exchanges.items():
                await exchange.close()
                self.logger.info(f"Closed {name} connection")

            self.logger.info("Collector stopped")

        except Exception as e:
            self.logger.error(f"Stop error: {e}", exc_info=True)
# Global instance
market_data_Collector = MarketDataCollector()