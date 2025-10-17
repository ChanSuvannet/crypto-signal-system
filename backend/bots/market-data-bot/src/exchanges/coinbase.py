
# ============================================
# Crypto Trading Signal System
# backed/bots/market-data-bot/src/exchanges/coinbase.py
# Deception: Coinbase Exchange Connector: HHandles data collection from Coinbase exchange
# ============================================
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

import ccxt.async_support as ccxt

from backend.shared_libs.python.crypto_trading_shared.enums import \
    TimeFrameEnum
from backend.shared_libs.python.crypto_trading_shared.types import (
    OHLCVData, OrderBookData)


class CoinbaseConnector:
    """
    Coinbase exchange connector using CCXT library
    """

    def __init__(self, config: Dict, logger):
        """Initialize Coinbase connector"""
        self.config = config
        self.logger = logger
        self.exchange: Optional[ccxt.coinbase] = None
        self.is_connected = False

        self.logger.info("CoinbaseConnector initialized")

    async def connect(self):
        """Connect to Coinbase exchange"""
        try:
            self.logger.info("Connecting to Coinbase...")

            self.exchange = ccxt.coinbase(
                {
                    "apiKey": self.config.get("api_key"),
                    "secret": self.config.get("api_secret"),
                    "enableRateLimit": True,
                    "rateLimit": self.config.get("rate_limit", 100),
                    "timeout": self.config.get("timeout", 30000),
                }
            )

            await self.exchange.load_markets()
            self.is_connected = True

            self.logger.info("Connected to Coinbase")

        except Exception as e:
            self.logger.error(f"Coinbase connection failed: {e}", exc_info=True)
            raise

    async def fetch_ohlcv(
        self, symbol: str, timeframe: str, limit: int = 100, since: Optional[int] = None
    ) -> List[OHLCVData]:
        """Fetch OHLCV data"""
        try:
            ohlcv = await self.exchange.fetch_ohlcv(
                symbol, timeframe, limit=limit, since=since
            )

            result = []
            for candle in ohlcv:
                timestamp, open_price, high, low, close, volume = candle
                result.append(
                    OHLCVData(
                        symbol=symbol,
                        timeframe=TimeFrameEnum(timeframe),
                        timestamp=datetime.fromtimestamp(timestamp / 1000),
                        open=Decimal(str(open_price)),
                        high=Decimal(str(high)),
                        low=Decimal(str(low)),
                        close=Decimal(str(close)),
                        volume=Decimal(str(volume)),
                        exchange="coinbase",
                    )
                )

            return result

        except Exception as e:
            self.logger.error(f"Error fetching OHLCV: {e}")
            raise

    async def fetch_orderbook(
        self, symbol: str, limit: int = 20
    ) -> Optional[OrderBookData]:
        """Fetch order book"""
        try:
            orderbook = await self.exchange.fetch_order_book(symbol, limit=limit)

            return OrderBookData(
                symbol=symbol,
                timestamp=datetime.now(),
                bids=[(Decimal(str(p)), Decimal(str(a))) for p, a in orderbook["bids"]],
                asks=[(Decimal(str(p)), Decimal(str(a))) for p, a in orderbook["asks"]],
                exchange="coinbase",
            )

        except Exception as e:
            self.logger.error(f"Error fetching orderbook: {e}")
            return None

    async def fetch_trades(
        self, symbol: str, limit: int = 100, since: Optional[int] = None
    ) -> List[Dict]:
        """Fetch recent trades"""
        try:
            trades = await self.exchange.fetch_trades(symbol, limit=limit, since=since)

            return [
                {
                    "symbol": symbol,
                    "timestamp": datetime.fromtimestamp(t["timestamp"] / 1000),
                    "price": Decimal(str(t["price"])),
                    "amount": Decimal(str(t["amount"])),
                    "side": t.get("side"),
                    "exchange": "coinbase",
                }
                for t in trades
            ]

        except Exception as e:
            self.logger.error(f"Error fetching trades: {e}")
            return []

    async def close(self):
        """Close connection"""
        if self.exchange:
            await self.exchange.close()
            self.is_connected = False
