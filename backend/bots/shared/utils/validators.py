# ============================================
# Crypto Trading Signal System
# backed/bots/shared/utils/validators.py
# Deception: Validators = Data validation utilities.
# ============================================

import re
from typing import Any, List, Dict, Optional, Union
from datetime import datetime
from decimal import Decimal, InvalidOperation

from ..core.logger import get_logger
from ..core.exceptions import BotValidationError

logger = get_logger("validators")


class DataValidator:
    """Validate various data types and formats."""

    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """
        Validate trading symbol format.

        Args:
            symbol: Trading symbol (e.g., BTCUSDT)

        Returns:
            True if valid
        """
        if not symbol or not isinstance(symbol, str):
            raise BotValidationError(
                "Symbol must be a non-empty string", field="symbol"
            )

        # Check format (e.g., BTCUSDT, BTC/USDT, BTC-USDT)
        pattern = r"^[A-Z]{2,10}[/\-]?[A-Z]{2,10}$"
        if not re.match(pattern, symbol):
            raise BotValidationError(f"Invalid symbol format: {symbol}", field="symbol")

        return True

    @staticmethod
    def validate_price(price: Union[float, Decimal], field_name: str = "price") -> bool:
        """
        Validate price value.

        Args:
            price: Price value
            field_name: Field name for error messages

        Returns:
            True if valid
        """
        try:
            price_float = float(price)

            if price_float <= 0:
                raise BotValidationError(
                    f"{field_name} must be positive", field=field_name, value=price
                )

            if price_float > 1e10:  # Sanity check
                raise BotValidationError(
                    f"{field_name} value too large", field=field_name, value=price
                )

            return True

        except (ValueError, TypeError, InvalidOperation) as e:
            raise BotValidationError(
                f"Invalid {field_name} value", field=field_name, value=price
            ) from e

    @staticmethod
    def validate_volume(volume: Union[float, Decimal]) -> bool:
        """
        Validate volume value.

        Args:
            volume: Volume value

        Returns:
            True if valid
        """
        try:
            volume_float = float(volume)

            if volume_float < 0:
                raise BotValidationError(
                    "Volume cannot be negative", field="volume", value=volume
                )

            return True

        except (ValueError, TypeError, InvalidOperation):
            raise BotValidationError(
                "Invalid volume value", field="volume", value=volume
            )

    @staticmethod
    def validate_timeframe(timeframe: str) -> bool:
        """
        Validate timeframe format.

        Args:
            timeframe: Timeframe (e.g., 1m, 5m, 1h, 1d)

        Returns:
            True if valid
        """
        valid_timeframes = [
            "1m",
            "3m",
            "5m",
            "15m",
            "30m",
            "1h",
            "2h",
            "4h",
            "6h",
            "8h",
            "12h",
            "1d",
            "3d",
            "1w",
            "1M",
        ]

        if timeframe not in valid_timeframes:
            raise BotValidationError(
                f"Invalid timeframe: {timeframe}", field="timeframe", value=timeframe
            )

        return True

    @staticmethod
    def validate_signal_type(signal_type: str) -> bool:
        """
        Validate signal type.

        Args:
            signal_type: Signal type (BUY or SELL)

        Returns:
            True if valid
        """
        if signal_type.upper() not in ["BUY", "SELL"]:
            raise BotValidationError(
                f"Invalid signal type: {signal_type}",
                field="signal_type",
                value=signal_type,
            )

        return True

    @staticmethod
    def validate_confidence(confidence: float) -> bool:
        """
        Validate confidence score.

        Args:
            confidence: Confidence score (0-100)

        Returns:
            True if valid
        """
        if not 0 <= confidence <= 100:
            raise BotValidationError(
                "Confidence must be between 0 and 100",
                field="confidence",
                value=confidence,
            )

        return True

    @staticmethod
    def validate_ohlcv(
        open_price: float, high: float, low: float, close: float, volume: float
    ) -> bool:
        """
        Validate OHLCV data consistency.

        Args:
            open_price: Open price
            high: High price
            low: Low price
            close: Close price
            volume: Volume

        Returns:
            True if valid
        """
        # Validate individual values
        DataValidator.validate_price(open_price, "open")
        DataValidator.validate_price(high, "high")
        DataValidator.validate_price(low, "low")
        DataValidator.validate_price(close, "close")
        DataValidator.validate_volume(volume)

        # Validate relationships
        if not (low <= open_price <= high and low <= close <= high):
            raise BotValidationError("OHLC values are inconsistent")

        if high < low:
            raise BotValidationError("High cannot be less than Low")

        return True

    @staticmethod
    def validate_signal_data(
        symbol: str,
        signal_type: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        confidence: float,
        timeframe: str,
    ) -> bool:
        """
        Validate complete signal data.

        Args:
            symbol: Trading symbol
            signal_type: BUY or SELL
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            confidence: Confidence score
            timeframe: Timeframe

        Returns:
            True if valid
        """
        # Validate individual fields
        DataValidator.validate_symbol(symbol)
        DataValidator.validate_signal_type(signal_type)
        DataValidator.validate_price(entry_price, "entry_price")
        DataValidator.validate_price(stop_loss, "stop_loss")
        DataValidator.validate_price(take_profit, "take_profit")
        DataValidator.validate_confidence(confidence)
        DataValidator.validate_timeframe(timeframe)

        # Validate price logic
        if signal_type.upper() == "BUY":
            if not (stop_loss < entry_price < take_profit):
                raise BotValidationError(
                    "For BUY: stop_loss < entry_price < take_profit required"
                )
        else:  # SELL
            if not (take_profit < entry_price < stop_loss):
                raise BotValidationError(
                    "For SELL: take_profit < entry_price < stop_loss required"
                )

        return True

    @staticmethod
    def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
        """
        Validate date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            True if valid
        """
        if start_date >= end_date:
            raise BotValidationError("Start date must be before end date")

        # Check if dates are in the future
        now = datetime.utcnow()
        if end_date > now:
            raise BotValidationError("End date cannot be in the future")

        return True

    @staticmethod
    def validate_api_key(api_key: str, api_secret: str) -> bool:
        """
        Validate API key format.

        Args:
            api_key: API key
            api_secret: API secret

        Returns:
            True if valid
        """
        if not api_key or len(api_key) < 10:
            raise BotValidationError("Invalid API key")

        if not api_secret or len(api_secret) < 10:
            raise BotValidationError("Invalid API secret")

        return True

    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """
        Sanitize string input.

        Args:
            value: Input string
            max_length: Maximum allowed length

        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            value = str(value)

        # Remove potentially dangerous characters
        value = value.strip()
        value = re.sub(r"[<>]", "", value)

        # Limit length
        if len(value) > max_length:
            value = value[:max_length]

        return value

    @staticmethod
    def validate_percentage(value: float, field_name: str = "percentage") -> bool:
        """
        Validate percentage value.

        Args:
            value: Percentage value
            field_name: Field name for errors

        Returns:
            True if valid
        """
        if not 0 <= value <= 100:
            raise BotValidationError(
                f"{field_name} must be between 0 and 100", field=field_name, value=value
            )

        return True

    @staticmethod
    def validate_dict_keys(
        data: Dict[str, Any], required_keys: List[str], optional_keys: List[str] = None
    ) -> bool:
        """
        Validate dictionary has required keys.

        Args:
            data: Dictionary to validate
            required_keys: List of required keys
            optional_keys: List of optional keys

        Returns:
            True if valid
        """
        if not isinstance(data, dict):
            raise BotValidationError("Data must be a dictionary")

        # Check required keys
        missing_keys = set(required_keys) - set(data.keys())
        if missing_keys:
            raise BotValidationError(f"Missing required keys: {missing_keys}")

        # Check for unexpected keys if optional_keys provided
        if optional_keys is not None:
            allowed_keys = set(required_keys + optional_keys)
            unexpected_keys = set(data.keys()) - allowed_keys
            if unexpected_keys:
                logger.warning(f"Unexpected keys in data: {unexpected_keys}")

        return True

    # Convenience validation functions
    def validate_signal(self) -> bool:
        """
        Validate signal dictionary.

        Args:
            signal_data: Signal data dictionary

        Returns:
            True if valid
        """
        required_keys = [
            "symbol",
            "signal_type",
            "entry_price",
            "stop_loss",
            "take_profit",
            "confidence",
            "timeframe",
        ]

        DataValidator.validate_dict_keys(self, required_keys)

        return DataValidator.validate_signal_data(
            symbol=self["symbol"],
            signal_type=self["signal_type"],
            entry_price=self["entry_price"],
            stop_loss=self["stop_loss"],
            take_profit=self["take_profit"],
            confidence=self["confidence"],
            timeframe=self["timeframe"],
        )

    def validate_price_data(self) -> bool:
        """
        Validate price data dictionary.

        Args:
            price_data: Price data dictionary

        Returns:
            True if valid
        """
        required_keys = ["open", "high", "low", "close", "volume"]

        DataValidator.validate_dict_keys(self, required_keys)

        return DataValidator.validate_ohlcv(
            open_price=self["open"],
            high=self["high"],
            low=self["low"],
            close=self["close"],
            volume=self["volume"],
        )
