"""
Shared Enumerations
All system-wide enums used across bots
"""

from enum import Enum, IntEnum

# ============================================================================
# SIGNAL ENUMS
# ============================================================================

class SignalType(str, Enum):
    """Type of trading signal"""
    BUY = "buy"
    SELL = "sell"
    LONG = "long"
    SHORT = "short"


class SignalStrength(str, Enum):
    """Strength of the signal"""
    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


class SignalStatus(str, Enum):
    """Status of the signal"""
    PENDING = "pending"
    ACTIVE = "active"
    TRIGGERED = "triggered"
    CLOSED = "closed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class SignalSource(str, Enum):
    """Source that generated the signal"""
    TECHNICAL = "technical"
    SENTIMENT = "sentiment"
    ICT = "itc"
    PATTERN = "pattern"
    ML_MODEL = "ml_model"
    AGGREGATED = "aggregated"


# ============================================================================
# MARKET ENUMS
# ============================================================================

class MarketRegime(str, Enum):
    """Current market regime/condition"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    VOLATILE = "volatile"
    LOW_VOLUME = "low_volume"
    HIGH_VOLUME = "high_volume"
    CONSOLIDATION = "consolidation"
    BREAKOUT = "breakout"


class MarketPhase(str, Enum):
    """Market phase based on ICT concepts"""
    ACCUMULATION = "accumulation"
    MARKUP = "markup"
    DISTRIBUTION = "distribution"
    MARKDOWN = "markdown"


class TrendDirection(str, Enum):
    """Trend direction"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


# ============================================================================
# ORDER ENUMS
# ============================================================================

class OrderType(str, Enum):
    """Type of order"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    STOP_LIMIT = "stop_limit"
    TAKE_PROFIT = "take_profit"
    TRAILING_STOP = "trailing_stop"


class PositionSide(str, Enum):
    """Position side"""
    LONG = "long"
    SHORT = "short"


class OrderStatus(str, Enum):
    """Order status"""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


# ============================================================================
# INDICATOR ENUMS
# ============================================================================

class IndicatorType(str, Enum):
    """Type of technical indicator"""
    TREND = "trend"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    VOLUME = "volume"
    CUSTOM = "custom"


class IndicatorSignal(str, Enum):
    """Signal from indicator"""
    BUY = "buy"
    SELL = "sell"
    NEUTRAL = "neutral"
    OVERBOUGHT = "overbought"
    OVERSOLD = "oversold"


# ============================================================================
# PATTERN ENUMS
# ============================================================================

class PatternType(str, Enum):
    """Type of chart pattern"""
    # Reversal Patterns
    HEAD_SHOULDERS = "head_shoulders"
    INVERSE_HEAD_SHOULDERS = "inverse_head_shoulders"
    DOUBLE_TOP = "double_top"
    DOUBLE_BOTTOM = "double_bottom"
    TRIPLE_TOP = "triple_top"
    TRIPLE_BOTTOM = "triple_bottom"
    
    # Continuation Patterns
    TRIANGLE_ASCENDING = "triangle_ascending"
    TRIANGLE_DESCENDING = "triangle_descending"
    TRIANGLE_SYMMETRICAL = "triangle_symmetrical"
    FLAG = "flag"
    PENNANT = "pennant"
    WEDGE_RISING = "wedge_rising"
    WEDGE_FALLING = "wedge_falling"
    
    # Candlestick Patterns
    DOJI = "doji"
    HAMMER = "hammer"
    SHOOTING_STAR = "shooting_star"
    ENGULFING_BULLISH = "engulfing_bullish"
    ENGULFING_BEARISH = "engulfing_bearish"
    MORNING_STAR = "morning_star"
    EVENING_STAR = "evening_star"


class PatternConfidence(str, Enum):
    """Confidence in pattern detection"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


# ============================================================================
# ICT ENUMS
# ============================================================================

class ICTConceptType(str, Enum):
    """Type of ICT concept"""
    ORDER_BLOCK = "order_block"
    FAIR_VALUE_GAP = "fair_value_gap"
    BREAKER_BLOCK = "breaker_block"
    LIQUIDITY_ZONE = "liquidity_zone"
    OPTIMAL_TRADE_ENTRY = "optimal_trade_entry"
    MARKET_STRUCTURE_SHIFT = "market_structure_shift"


class MarketStructureEvent(str, Enum):
    """Market structure events"""
    BOS = "break_of_structure"  # Break of Structure
    CHOCH = "change_of_character"  # Change of Character
    SWING_HIGH = "swing_high"
    SWING_LOW = "swing_low"


class LiquidityType(str, Enum):
    """Type of liquidity"""
    BUY_SIDE = "buy_side"
    SELL_SIDE = "sell_side"
    EQUAL_HIGHS = "equal_highs"
    EQUAL_LOWS = "equal_lows"


# ============================================================================
# NEWS & SENTIMENT ENUMS
# ============================================================================

class NewsImpact(IntEnum):
    """Impact level of news (1-10)"""
    VERY_LOW = 1
    LOW = 3
    MEDIUM = 5
    HIGH = 7
    VERY_HIGH = 9
    EXTREME = 10


class SentimentScore(str, Enum):
    """Sentiment score"""
    VERY_BEARISH = "very_bearish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    BULLISH = "bullish"
    VERY_BULLISH = "very_bullish"


class NewsSource(str, Enum):
    """News source"""
    CRYPTOPANIC = "cryptopanic"
    NEWSAPI = "newsapi"
    TWITTER = "twitter"
    REDDIT = "reddit"
    RSS = "rss"
    TELEGRAM = "telegram"


class NewsTopic(str, Enum):
    """News topic/category"""
    REGULATION = "regulation"
    ADOPTION = "adoption"
    TECHNOLOGY = "technology"
    PARTNERSHIP = "partnership"
    SECURITY = "security"
    MARKET = "market"
    HACK = "hack"
    LISTING = "listing"


# ============================================================================
# TIMEFRAME ENUMS
# ============================================================================

class TimeFrameEnum(str, Enum):
    """Trading timeframes"""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H2 = "2h"
    H4 = "4h"
    H6 = "6h"
    H12 = "12h"
    D1 = "1d"
    D3 = "3d"
    W1 = "1w"
    M = "1M"


# ============================================================================
# PERFORMANCE ENUMS
# ============================================================================

class TradeOutcome(str, Enum):
    """Outcome of a trade"""
    WIN = "win"
    LOSS = "loss"
    BREAK_EVEN = "break_even"
    PARTIAL_WIN = "partial_win"
    PARTIAL_LOSS = "partial_loss"
    STOPPED_OUT = "stopped_out"
    TAKEN_PROFIT = "taken_profit"


class PerformancePeriod(str, Enum):
    """Period for performance metrics"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    ALL_TIME = "all_time"


# ============================================================================
# BOT ENUMS
# ============================================================================

class BotStatus(str, Enum):
    """Status of a bot"""
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class BotType(str, Enum):
    """Type of bot"""
    MARKET_DATA = "market_data"
    NEWS_COLLECTOR = "news_collector"
    TECHNICAL_ANALYSIS = "technical_analysis"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    ICT_ANALYSIS = "itc_analysis"
    PATTERN_RECOGNITION = "pattern_recognition"
    SIGNAL_AGGREGATOR = "signal_aggregator"
    ML_ENGINE = "ml_engine"
    NOTIFICATION = "notification"
    FEEDBACK_PROCESSOR = "feedback_processor"
    MONITORING = "monitoring"


# ============================================================================
# VALIDATION ENUMS
# ============================================================================

class ValidationStatus(str, Enum):
    """Status of validation"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    PENDING = "pending"


class ValidationRule(str, Enum):
    """Validation rules"""
    RISK_REWARD = "risk_reward"
    WIN_RATE = "win_rate"
    MARKET_REGIME = "market_regime"
    VOLUME = "volume"
    CORRELATION = "correlation"
    VOLATILITY = "volatility"
    CONFLUENCE = "confluence"


# ============================================================================
# NOTIFICATION ENUMS
# ============================================================================

class NotificationChannel(str, Enum):
    """Notification channel"""
    TELEGRAM = "telegram"
    DISCORD = "discord"
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    PUSH = "push"


class NotificationType(str, Enum):
    """Type of notification"""
    SIGNAL = "signal"
    NEWS = "news"
    PERFORMANCE = "performance"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class NotificationPriority(str, Enum):
    """Priority of notification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# ============================================================================
# ML MODEL ENUMS
# ============================================================================

class ModelType(str, Enum):
    """Type of ML model"""
    LSTM = "lstm"
    GRU = "gru"
    TRANSFORMER = "transformer"
    CNN = "cnn"
    ENSEMBLE = "ensemble"
    BERT = "bert"
    DQN = "dqn"
    PPO = "ppo"


class ModelStatus(str, Enum):
    """Status of ML model"""
    TRAINING = "training"
    TRAINED = "trained"
    DEPLOYED = "deployed"
    TESTING = "testing"
    FAILED = "failed"
    DEPRECATED = "deprecated"


class TrainingPhase(str, Enum):
    """Phase of model training"""
    PREPROCESSING = "preprocessing"
    TRAINING = "training"
    VALIDATION = "validation"
    TESTING = "testing"
    COMPLETED = "completed"


# ============================================================================
# EXCHANGE ENUMS
# ============================================================================

class ExchangeName(str, Enum):
    """Supported exchanges"""
    BINANCE = "binance"
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    BYBIT = "bybit"
    OKX = "okx"
    KUCOIN = "kucoin"


class DataType(str, Enum):
    """Type of market data"""
    OHLCV = "ohlcv"
    ORDERBOOK = "orderbook"
    TRADES = "trades"
    TICKER = "ticker"
    FUNDING_RATE = "funding_rate"


# ============================================================================
# RISK ENUMS
# ============================================================================

class RiskLevel(str, Enum):
    """Risk level"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class RiskType(str, Enum):
    """Type of risk"""
    MARKET_RISK = "market_risk"
    LIQUIDITY_RISK = "liquidity_risk"
    VOLATILITY_RISK = "volatility_risk"
    CORRELATION_RISK = "correlation_risk"


# ============================================================================
# LOGGING ENUMS
# ============================================================================

class LogLevel(str, Enum):
    """Logging level"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogCategory(str, Enum):
    """Log category"""
    SYSTEM = "system"
    DATABASE = "database"
    API = "api"
    SIGNAL = "signal"
    TRADING = "trading"
    ML = "ml"
    NOTIFICATION = "notification"


# ============================================================================
# ERROR ENUMS
# ============================================================================

class ErrorType(str, Enum):
    """Type of error"""
    DATABASE_ERROR = "database_error"
    API_ERROR = "api_error"
    VALIDATION_ERROR = "validation_error"
    NETWORK_ERROR = "network_error"
    AUTHENTICATION_ERROR = "authentication_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    INSUFFICIENT_DATA = "insufficient_data"
    MODEL_ERROR = "model_error"
    CONFIGURATION_ERROR = "configuration_error"


class ErrorSeverity(str, Enum):
    """Severity of error"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_enum_values(enum_class):
    """Get all values from an enum class"""
    return [e.value for e in enum_class]


def is_valid_enum(enum_class, value):
    """Check if value is valid for enum class"""
    return value in get_enum_values(enum_class)