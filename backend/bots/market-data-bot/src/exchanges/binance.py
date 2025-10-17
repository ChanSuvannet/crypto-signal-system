
# ============================================
# Crypto Trading Signal System
# backed/bots/market-data-bot/src/exchanges/binance.py
# Deception: Binance Exchange Connector: Handles data collection from Binance exchange
# ============================================
import asyncio
import json
from datetime import datetime
from decimal import Decimal
from typing import Callable, Dict, List, Optional

import ccxt.async_support as ccxt

from backend.shared_libs.python.crypto_trading_shared.enums import \
    TimeFrameEnum
from backend.shared_libs.python.crypto_trading_shared.types import (
    OHLCVData, OrderBookData)


class BinanceConnector:
    """
    Binance exchange connector using CCXT library
    """

    def __init__(self, config: Dict, logger):
        """Initialize Binance connector"""
        self.config = config
        self.logger = logger

        self.exchange: Optional[ccxt.binance] = None
        self.ws_client = None
        self.is_connected = False

        self.logger.info("BinanceConnector initialized")

    async def connect(self):
        """Connect to Binance exchange"""
        try:
            self.logger.info("Connecting to Binance...")

            # Initialize CCXT Binance client
            self.exchange = ccxt.binance(
                {
                    "apiKey": self.config.get("api_key"),
                    "secret": self.config.get("api_secret"),
                    "enableRateLimit": True,
                    "rateLimit": 1200,  # Default Binance rate limit
                    "timeout": self.config.get("timeout", 30000),
                    "options": {
                        "defaultType": "spot",  # spot, future, margin
                        "adjustForTimeDifference": True,
                    },
                }
            )

            # Test connection
            await self.exchange.load_markets()

            # Get server time to verify connection
            server_time = await self.exchange.fetch_time()
            self.logger.info(
                f"Connected to Binance (Server time: {datetime.fromtimestamp(server_time/1000)})"
            )

            self.is_connected = True

        except Exception as e:
            self.logger.error(f"Binance connection failed: {e}", exc_info=True)
            raise

    async def fetch_ohlcv(
        self, symbol: str, timeframe: str, limit: int = 100, since: Optional[int] = None
    ) -> List[OHLCVData]:
        """
        Fetch OHLCV (candlestick) data

        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            timeframe: Timeframe (e.g., "1h", "4h", "1d")
            limit: Number of candles to fetch
            since: Timestamp in milliseconds

        Returns:
            List of OHLCVData objects
        """
        try:
            # Fetch from exchange
            ohlcv = await self.exchange.fetch_ohlcv(
                symbol=symbol, timeframe=timeframe, limit=limit, since=since
            )

            # Convert to OHLCVData objects
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
                        exchange="binance",
                    )
                )

            self.logger.debug(
                f"Fetched {len(result)} OHLCV candles for {symbol} {timeframe}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            raise

    async def fetch_orderbook(
        self, symbol: str, limit: int = 20
    ) -> Optional[OrderBookData]:
        """
        Fetch order book data

        Args:
            symbol: Trading pair
            limit: Depth of order book

        Returns:
            OrderBookData object
        """
        try:
            # Fetch from exchange
            orderbook = await self.exchange.fetch_order_book(symbol, limit=limit)

            # Convert to OrderBookData
            result = OrderBookData(
                symbol=symbol,
                timestamp=(
                    datetime.fromtimestamp(orderbook["timestamp"] / 1000)
                    if orderbook.get("timestamp")
                    else datetime.now()
                ),
                bids=[
                    (Decimal(str(price)), Decimal(str(amount)))
                    for price, amount in orderbook["bids"]
                ],
                asks=[
                    (Decimal(str(price)), Decimal(str(amount)))
                    for price, amount in orderbook["asks"]
                ],
                exchange="binance",
            )

            self.logger.debug(
                f"Fetched orderbook for {symbol}: {len(result.bids)} bids, {len(result.asks)} asks"
            )
            return result

        except Exception as e:
            self.logger.error(f"Error fetching orderbook for {symbol}: {e}")
            return None

    async def fetch_trades(
        self, symbol: str, limit: int = 100, since: Optional[int] = None
    ) -> List[Dict]:
        """
        Fetch recent trades

        Args:
            symbol: Trading pair
            limit: Number of trades to fetch
            since: Timestamp in milliseconds

        Returns:
            List of trade dictionaries
        """
        try:
            # Fetch from exchange
            trades = await self.exchange.fetch_trades(
                symbol=symbol, limit=limit, since=since
            )

            # Format trades
            result = []
            result.extend(
                {
                    "symbol": symbol,
                    "id": trade.get("id"),
                    "timestamp": datetime.fromtimestamp(trade["timestamp"] / 1000),
                    "price": Decimal(str(trade["price"])),
                    "amount": Decimal(str(trade["amount"])),
                    "side": trade.get("side"),  # 'buy' or 'sell'
                    "exchange": "binance",
                }
                for trade in trades
            )
            self.logger.debug(f"Fetched {len(result)} trades for {symbol}")
            return result

        except Exception as e:
            self.logger.error(f"Error fetching trades for {symbol}: {e}")
            return []

    async def fetch_ticker(self, symbol: str) -> Dict:
        """
        Fetch ticker (24h statistics)

        Args:
            symbol: Trading pair

        Returns:
            Ticker dictionary
        """
        try:
            ticker = await self.exchange.fetch_ticker(symbol)

            return {
                "symbol": symbol,
                "timestamp": datetime.fromtimestamp(ticker["timestamp"] / 1000),
                "last": Decimal(str(ticker["last"])),
                "bid": Decimal(str(ticker["bid"])) if ticker.get("bid") else None,
                "ask": Decimal(str(ticker["ask"])) if ticker.get("ask") else None,
                "volume": (
                    Decimal(str(ticker["baseVolume"]))
                    if ticker.get("baseVolume")
                    else None
                ),
                "quote_volume": (
                    Decimal(str(ticker["quoteVolume"]))
                    if ticker.get("quoteVolume")
                    else None
                ),
                "high": Decimal(str(ticker["high"])) if ticker.get("high") else None,
                "low": Decimal(str(ticker["low"])) if ticker.get("low") else None,
                "change": ticker.get("change"),
                "percentage": ticker.get("percentage"),
                "exchange": "binance",
            }

        except Exception as e:
            self.logger.error(f"Error fetching ticker for {symbol}: {e}")
            return {}

    async def stream(self, symbols: List[str], callback: Callable):
        """
        Stream real-time data via WebSocket

        Args:
            symbols: List of symbols to stream
            callback: Callback function to handle incoming data
        """
        try:
            self.logger.info(f"Starting WebSocket stream for {len(symbols)} symbols")

            # Note: CCXT Pro is needed for WebSocket streaming
            # This is a placeholder - you'll need ccxt.pro for full WebSocket support
            # For now, we'll poll at high frequency

            while True:
                for symbol in symbols:
                    try:
                        # Fetch ticker
                        ticker = await self.fetch_ticker(symbol)

                        if ticker:
                            await callback({"type": "ticker", **ticker})

                    except Exception as e:
                        self.logger.error(f"Stream error for {symbol}: {e}")

                # Wait before next poll (simulate streaming)
                await asyncio.sleep(1)

        except Exception as e:
            self.logger.error(f"WebSocket stream error: {e}", exc_info=True)
            raise

    async def get_exchange_info(self) -> Dict:
        """Get exchange information"""
        try:
            return {
                "name": "Binance",
                "markets": len(self.exchange.markets) if self.exchange else 0,
                "has": {
                    "fetchOHLCV": (
                        self.exchange.has["fetchOHLCV"] if self.exchange else False
                    ),
                    "fetchOrderBook": (
                        self.exchange.has["fetchOrderBook"] if self.exchange else False
                    ),
                    "fetchTrades": (
                        self.exchange.has["fetchTrades"] if self.exchange else False
                    ),
                    "fetchTicker": (
                        self.exchange.has["fetchTicker"] if self.exchange else False
                    ),
                },
            }
        except Exception as e:
            self.logger.error(f"Error getting exchange info: {e}")
            return {}

    async def close(self):
        """Close exchange connection"""
        try:
            if self.exchange:
                await self.exchange.close()
                self.logger.info("Binance connection closed")
                self.is_connected = False
        except Exception as e:
            self.logger.error(f"Error closing connection: {e}")
