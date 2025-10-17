
# ============================================
# Crypto Trading Signal System
# backed/bots/shared-libs/python/crypto_trading_shared/__init__.py
# Deception: Shared code used across all trading bots
# ============================================
"""
Crypto Trading Shared Libraries
Shared code used across all trading bots
"""

from .constants import *
from .enums import *
from .types import *

__version__ = "1.0.0"
__author__ = "Crypto Trading System"

__all__ = [
    # Version info
    "__version__",
    "__author__",
    
    # Constants
    "TimeFrame",
    "SUPPORTED_EXCHANGES",
    "SUPPORTED_SYMBOLS",
    "DEFAULT_TIMEFRAMES",
    "API_ENDPOINTS",
    "DATABASE_NAMES",
    "RABBITMQ_EXCHANGES",
    "RABBITMQ_QUEUES",
    "REDIS_KEYS",
    "RISK_LIMITS",
    "SIGNAL_THRESHOLDS",
    "ML_MODEL_PATHS",
    
    # Enums
    "SignalType",
    "SignalStrength",
    "MarketRegime",
    "OrderType",
    "PositionSide",
    "SignalStatus",
    "BotStatus",
    "NewsImpact",
    "SentimentScore",
    "TimeFrameEnum",
    "IndicatorType",
    "PatternType",
    "ValidationStatus",
    "TradeOutcome",
    "NotificationChannel",
    "LogLevel",
    
    # Types
    "PriceData",
    "OHLCVData",
    "IndicatorData",
    "SignalData",
    "NewsData",
    "SentimentData",
    "PerformanceMetrics",
    "RiskRewardRatio",
    "TradeLevels",
    "BotHealthMetrics",
    "MLModelMetrics",
    "FeedbackData",
    "ValidationResult",
    "MessagePayload",
]