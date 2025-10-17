
# ============================================
# Crypto Trading Signal System
# backed/bots/market-data-bot/src/processors/orderbook_processor.py
# Deception: OrderBook Data Processor: Validates and processes order book data
# ============================================
from decimal import Decimal
from typing import Dict, Optional

from backend.shared_libs.python.crypto_trading_shared.types import \
    OrderBookData


class OrderBookProcessor:
    """
    Processes and analyzes order book data
    """

    def __init__(self, config: Dict, logger):
        """Initialize processor"""
        self.config = config
        self.logger = logger

        self.logger.info("OrderBookProcessor initialized")

    async def process(self, orderbook_data: Dict) -> Optional[OrderBookData]:
        """
        Process raw orderbook data

        Args:
            orderbook_data: Raw orderbook from exchange

        Returns:
            Processed OrderBookData or None
        """
        try:
            if not orderbook_data:
                return None

            # Validate
            if not self._validate(orderbook_data):
                self.logger.warning("Invalid orderbook data")
                return None

            # Already converted in connector, but process here if needed
            return orderbook_data if isinstance(orderbook_data, OrderBookData) else None
        except Exception as e:
            self.logger.error(f"Error processing orderbook: {e}")
            return None

    def _validate(self, orderbook) -> bool:
        """Validate orderbook data"""
        if isinstance(orderbook, OrderBookData):
            return len(orderbook.bids) > 0 and len(orderbook.asks) > 0
        return False

    def calculate_spread(self, orderbook: OrderBookData) -> Dict:
        """Calculate bid-ask spread"""
        try:
            if not orderbook.bids or not orderbook.asks:
                return {}

            best_bid = orderbook.bids[0][0]
            best_ask = orderbook.asks[0][0]

            spread = best_ask - best_bid
            spread_percent = (spread / best_bid) * 100

            return {
                "spread": float(spread),
                "spread_percent": float(spread_percent),
                "best_bid": float(best_bid),
                "best_ask": float(best_ask),
            }

        except Exception as e:
            self.logger.error(f"Error calculating spread: {e}")
            return {}

    def calculate_depth(self, orderbook: OrderBookData, levels: int = 10) -> Dict:
        """Calculate order book depth"""
        try:
            bid_volume = sum(amount for _, amount in orderbook.bids[:levels])
            ask_volume = sum(amount for _, amount in orderbook.asks[:levels])

            total_volume = bid_volume + ask_volume
            bid_ratio = (bid_volume / total_volume * 100) if total_volume > 0 else 0

            return {
                "bid_volume": float(bid_volume),
                "ask_volume": float(ask_volume),
                "total_volume": float(total_volume),
                "bid_ratio": float(bid_ratio),
                "ask_ratio": float(100 - bid_ratio),
            }

        except Exception as e:
            self.logger.error(f"Error calculating depth: {e}")
            return {}
