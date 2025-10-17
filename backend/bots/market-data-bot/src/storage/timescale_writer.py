
# ============================================
# Crypto Trading Signal System
# backed/bots/market-data-bot/src/storage/timescale_writer.py
# Deception: TimescaleDB Writer: Writes market data to TimescaleDB hypertables
# ============================================

from datetime import datetime
from decimal import Decimal
from typing import Dict, List

from backend.shared_libs.python.crypto_trading_shared.types import (
    OHLCVData, OrderBookData)


class TimescaleWriter:
    """
    Writes time-series market data to TimescaleDB
    """

    def __init__(self, db_client, logger):
        """Initialize writer"""
        self.db = db_client
        self.logger = logger

        self.logger.info("TimescaleWriter initialized")

    async def write_ohlcv_batch(self, data: List[OHLCVData]):
        """
        Write batch of OHLCV data to TimescaleDB

        Args:
            data: List of OHLCVData objects
        """
        if not data:
            return

        try:
            query = """
                INSERT INTO ohlcv_data 
                (symbol, timeframe, timestamp, open, high, low, close, volume, exchange)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (symbol, timeframe, timestamp) 
                DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume
            """

            # Prepare batch data
            records = [
                (
                    ohlcv.symbol,
                    ohlcv.timeframe.value,
                    ohlcv.timestamp,
                    float(ohlcv.open),
                    float(ohlcv.high),
                    float(ohlcv.low),
                    float(ohlcv.close),
                    float(ohlcv.volume),
                    ohlcv.exchange,
                )
                for ohlcv in data
            ]

            # Execute batch insert
            await self.db.executemany(query, records)

            self.logger.debug(f"Wrote {len(data)} OHLCV records to TimescaleDB")

        except Exception as e:
            self.logger.error(f"Error writing OHLCV batch: {e}", exc_info=True)
            raise

    async def write_orderbook_batch(self, data: List[OrderBookData]):
        """
        Write batch of orderbook data

        Args:
            data: List of OrderBookData objects
        """
        if not data:
            return

        try:
            query = """
                INSERT INTO orderbook_snapshots
                (symbol, timestamp, bids, asks, exchange)
                VALUES ($1, $2, $3, $4, $5)
            """

            # Prepare batch data
            records = [
                (
                    ob.symbol,
                    ob.timestamp,
                    [[float(p), float(a)] for p, a in ob.bids],  # Convert to JSON
                    [[float(p), float(a)] for p, a in ob.asks],
                    ob.exchange,
                )
                for ob in data
            ]

            # Execute batch insert
            await self.db.executemany(query, records)

            self.logger.debug(f"Wrote {len(data)} orderbook records to TimescaleDB")

        except Exception as e:
            self.logger.error(f"Error writing orderbook batch: {e}", exc_info=True)
            raise

    async def write_trades_batch(self, data: List[Dict]):
        """
        Write batch of trade data

        Args:
            data: List of trade dictionaries
        """
        if not data:
            return

        try:
            query = """
                INSERT INTO recent_trades
                (symbol, timestamp, price, amount, side, exchange, trade_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """

            # Prepare batch data
            records = [
                (
                    trade["symbol"],
                    trade["timestamp"],
                    float(trade["price"]),
                    float(trade["amount"]),
                    trade.get("side"),
                    trade["exchange"],
                    trade.get("id"),
                )
                for trade in data
            ]

            # Execute batch insert
            await self.db.executemany(query, records)

            self.logger.debug(f"Wrote {len(data)} trade records to TimescaleDB")

        except Exception as e:
            self.logger.error(f"Error writing trades batch: {e}", exc_info=True)
            raise

    async def get_latest_ohlcv(
        self, symbol: str, timeframe: str, limit: int = 100
    ) -> List[OHLCVData]:
        """
        Retrieve latest OHLCV data from database

        Args:
            symbol: Trading pair
            timeframe: Timeframe
            limit: Number of records

        Returns:
            List of OHLCVData
        """
        try:
            query = """
                SELECT symbol, timeframe, timestamp, open, high, low, close, volume, exchange
                FROM ohlcv_data
                WHERE symbol = $1 AND timeframe = $2
                ORDER BY timestamp DESC
                LIMIT $3
            """

            rows = await self.db.fetch(query, symbol, timeframe, limit)

            result = []
            result.extend(
                OHLCVData(
                    symbol=row["symbol"],
                    timeframe=row["timeframe"],
                    timestamp=row["timestamp"],
                    open=Decimal(str(row["open"])),
                    high=Decimal(str(row["high"])),
                    low=Decimal(str(row["low"])),
                    close=Decimal(str(row["close"])),
                    volume=Decimal(str(row["volume"])),
                    exchange=row["exchange"],
                )
                for row in rows
            )
            return result

        except Exception as e:
            self.logger.error(f"Error retrieving OHLCV: {e}")
            return []
