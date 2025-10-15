
# ============================================
# Crypto Trading Signal System
# backed/bots/shared/core/__init__.py
# Deception: Core functionality for all trading bots.
# ============================================
from .base_bot import BaseBot
from .config import Config
from .logger import (
    setup_logger,
    setup_daily_logger,
    get_logger,
    log_trade_signal,
    log_error_with_context,
    log_performance_metrics,
)
from .exceptions import (
    BotError,
    BotConfigError,
    BotConnectionError,
    BotDatabaseError,
    BotValidationError,
    BotAPIError,
    BotRateLimitError,
    BotDataError,
    BotTimeoutError,
    BotAuthenticationError,
    BotSignalError,
    BotIndicatorError,
    BotModelError,
    BotShutdownError,
    handle_bot_errors,
    retry_on_error,
)

__all__ = [
    # Base classes
    "BaseBot",
    "Config",
    # Logging
    "setup_logger",
    "setup_daily_logger",
    "get_logger",
    "log_trade_signal",
    "log_error_with_context",
    "log_performance_metrics",
    # Exceptions
    "BotError",
    "BotConfigError",
    "BotConnectionError",
    "BotDatabaseError",
    "BotValidationError",
    "BotAPIError",
    "BotRateLimitError",
    "BotDataError",
    "BotTimeoutError",
    "BotAuthenticationError",
    "BotSignalError",
    "BotIndicatorError",
    "BotModelError",
    "BotShutdownError",
    "handle_bot_errors",
    "retry_on_error",
]
