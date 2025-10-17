
# ============================================
# Crypto Trading Signal System
# backed/bots/market-data-bot/src/processors/trade_processor.py
# Deception: Trade Data Processor: Validates and processes individual trade data
# ============================================
from typing import Dict, List


class TradeProcessor:
    """
    Processes and analyzes individual trades
    """

    def __init__(self, config: Dict, logger):
        """Initialize processor"""
        self.config = config
        self.logger = logger

        self.logger.info("TradeProcessor initialized")

    async def process(self, trades: List[Dict]) -> List[Dict]:
        """
        Process trade data

        Args:
            trades: List of trade dictionaries

        Returns:
            List of validated trades
        """
        if not trades:
            return []

        processed = []

        for trade in trades:
            try:
                # Validate
                if self._validate(trade):
                    processed.append(trade)
                else:
                    self.logger.warning(f"Invalid trade data: {trade}")

            except Exception as e:
                self.logger.error(f"Error processing trade: {e}")

        return processed

    def _validate(self, trade: Dict) -> bool:
        """Validate trade data"""
        required_fields = ["symbol", "timestamp", "price", "amount"]

        for field in required_fields:
            if field not in trade:
                return False

        # Check values
        if trade["price"] <= 0 or trade["amount"] <= 0:
            return False

        return True

    def aggregate_trades(self, trades: List[Dict], window_seconds: int = 60) -> Dict:
        """
        Aggregate trades within a time window

        Args:
            trades: List of trades
            window_seconds: Time window for aggregation

        Returns:
            Aggregated trade statistics
        """
        try:
            if not trades:
                return {}

            # Sort by timestamp
            sorted_trades = sorted(trades, key=lambda x: x["timestamp"])

            total_volume = sum(float(t["amount"]) for t in sorted_trades)
            buy_volume = sum(
                float(t["amount"]) for t in sorted_trades if t.get("side") == "buy"
            )
            sell_volume = total_volume - buy_volume

            prices = [float(t["price"]) for t in sorted_trades]

            return {
                "trade_count": len(sorted_trades),
                "total_volume": total_volume,
                "buy_volume": buy_volume,
                "sell_volume": sell_volume,
                "buy_sell_ratio": (buy_volume / sell_volume) if sell_volume > 0 else 0,
                "avg_price": sum(prices) / len(prices),
                "min_price": min(prices),
                "max_price": max(prices),
                "first_timestamp": sorted_trades[0]["timestamp"],
                "last_timestamp": sorted_trades[-1]["timestamp"],
            }

        except Exception as e:
            self.logger.error(f"Error aggregating trades: {e}")
            return {}
