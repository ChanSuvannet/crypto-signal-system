
# ============================================
# Crypto Trading Signal System
# backed/bots/market-data-bot/src/processors/ohlcv_processor.py
# Deception: BOHLCV Data Processor: Validates and processes OHLCV (candlestick) data
# ============================================
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from backend.shared_libs.python.crypto_trading_shared.constants import \
    VALIDATION_RULES
from backend.shared_libs.python.crypto_trading_shared.types import OHLCVData


class OHLCVProcessor:
    """
    Processes and validates OHLCV data
    """

    def __init__(self, config: Dict, logger):
        """Initialize processor"""
        self.config = config
        self.logger = logger

        # Validation settings
        self.validation_enabled = (
            config.get("processing", {}).get("validation", {}).get("enabled", True)
        )

        self.reject_invalid = (
            config.get("processing", {})
            .get("validation", {})
            .get("reject_invalid", False)
        )

        # Quality checks
        self.quality_checks = config.get("processing", {}).get("quality_checks", {})

        self.logger.info("OHLCVProcessor initialized")

    async def process(self, data: List[OHLCVData]) -> List[OHLCVData]:
        """
        Process OHLCV data

        Args:
            data: List of OHLCVData objects

        Returns:
            List of validated and processed OHLCVData
        """
        if not data:
            return []

        processed = []

        for ohlcv in data:
            try:
                # Validate
                if self.validation_enabled:
                    is_valid, reason = self._validate(ohlcv)

                    if not is_valid:
                        self.logger.warning(
                            f"Invalid OHLCV data for {ohlcv.symbol}: {reason}"
                        )

                        if self.reject_invalid:
                            continue

                # Check quality
                if self.quality_checks:
                    self._check_quality(ohlcv)

                processed.append(ohlcv)

            except Exception as e:
                self.logger.error(f"Error processing OHLCV: {e}")

        return processed

    def _validate(self, ohlcv: OHLCVData) -> tuple[bool, Optional[str]]:
        """
        Validate OHLCV data

        Returns:
            (is_valid, reason)
        """
        # Check required fields
        if not ohlcv.symbol:
            return False, "Missing symbol"

        if not ohlcv.timestamp:
            return False, "Missing timestamp"

        # Check price values
        price_rules = VALIDATION_RULES.get("price", {})
        min_price = Decimal(str(price_rules.get("min_value", 0.000001)))
        max_price = Decimal(str(price_rules.get("max_value", 1000000)))

        for price in [ohlcv.open, ohlcv.high, ohlcv.low, ohlcv.close]:
            if price < min_price or price > max_price:
                return False, f"Price out of range: {price}"

        # Check OHLC relationships
        if ohlcv.high < ohlcv.low:
            return False, f"High ({ohlcv.high}) < Low ({ohlcv.low})"

        if ohlcv.high < ohlcv.open or ohlcv.high < ohlcv.close:
            return False, "High is not the highest price"

        if ohlcv.low > ohlcv.open or ohlcv.low > ohlcv.close:
            return False, "Low is not the lowest price"

        # Check volume
        if ohlcv.volume < 0:
            return False, f"Negative volume: {ohlcv.volume}"

        return True, None

    def _check_quality(self, ohlcv: OHLCVData):
        """
        Perform quality checks on OHLCV data
        """
        # Check for suspicious price movements
        price_change = abs(ohlcv.close - ohlcv.open) / ohlcv.open * 100

        if price_change > 50:  # More than 50% change in one candle
            self.logger.warning(
                f"Suspicious price movement for {ohlcv.symbol}: {price_change:.2f}%"
            )

        # Check for zero volume
        if ohlcv.volume == 0:
            self.logger.debug(f"Zero volume for {ohlcv.symbol} at {ohlcv.timestamp}")

        # Check for duplicate timestamps (if we're tracking)
        # This would require maintaining state - implement if needed

    def calculate_indicators(self, ohlcv_list: List[OHLCVData]) -> Dict:
        # sourcery skip: extract-method
        """
        Calculate basic indicators from OHLCV data
        (This is a simple example - full indicator calculation happens in Technical Analysis Bot)

        Args:
            ohlcv_list: List of OHLCV data points

        Returns:
            Dictionary of calculated indicators
        """
        if len(ohlcv_list) < 2:
            return {}

        try:
            # Calculate simple metrics
            latest = ohlcv_list[-1]
            previous = ohlcv_list[-2]

            price_change = float(latest.close - previous.close)
            price_change_percent = (price_change / float(previous.close)) * 100

            volume_change = float(latest.volume - previous.volume)
            volume_change_percent = (
                (volume_change / float(previous.volume)) * 100
                if previous.volume > 0
                else 0
            )

            return {
                "price_change": price_change,
                "price_change_percent": price_change_percent,
                "volume_change": volume_change,
                "volume_change_percent": volume_change_percent,
                "high_low_range": float(latest.high - latest.low),
                "body_size": abs(float(latest.close - latest.open)),
            }

        except Exception as e:
            self.logger.error(f"Error calculating indicators: {e}")
            return {}

    def detect_gaps(self, ohlcv_list: List[OHLCVData]) -> List[Dict]:
        """
        Detect gaps in OHLCV data

        Args:
            ohlcv_list: Sorted list of OHLCV data

        Returns:
            List of detected gaps
        """
        gaps = []

        if len(ohlcv_list) < 2:
            return gaps

        try:
            # Sort by timestamp
            sorted_data = sorted(ohlcv_list, key=lambda x: x.timestamp)

            for i in range(1, len(sorted_data)):
                prev = sorted_data[i - 1]
                curr = sorted_data[i]

                # Calculate expected time difference based on timeframe
                # This is simplified - should use timeframe-specific logic
                time_diff = (curr.timestamp - prev.timestamp).total_seconds()

                # If gap is detected (this logic depends on timeframe)
                if time_diff > 3600:  # More than 1 hour gap (example)
                    gaps.append(
                        {
                            "symbol": curr.symbol,
                            "start": prev.timestamp,
                            "end": curr.timestamp,
                            "duration_seconds": time_diff,
                        }
                    )

            if gaps:
                self.logger.info(f"Detected {len(gaps)} gaps in OHLCV data")

        except Exception as e:
            self.logger.error(f"Error detecting gaps: {e}")

        return gaps
