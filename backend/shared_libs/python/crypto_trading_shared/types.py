"""
Shared Type Definitions
All system-wide type definitions and data classes
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from .enums import (BotStatus, MarketRegime, NewsImpact, NotificationChannel,
                    PatternType, SentimentScore, SignalSource, SignalStatus,
                    SignalStrength, SignalType, TimeFrameEnum, TradeOutcome,
                    ValidationStatus)

# ============================================================================
# PRICE DATA TYPES
# ============================================================================


class PriceData(BaseModel):
    """Basic price data"""

    symbol: str
    price: Decimal
    timestamp: datetime
    volume: Optional[Decimal] = None
    exchange: Optional[str] = None

    class Config:
        json_encoders = {Decimal: lambda v: float(v), datetime: lambda v: v.isoformat()}


class OHLCVData(BaseModel):
    """OHLCV candlestick data"""

    symbol: str
    timeframe: TimeFrameEnum
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    exchange: Optional[str] = None

    @validator("high")
    def high_must_be_highest(cls, v, values):
        if "low" in values and v < values["low"]:
            raise ValueError("High must be >= Low")
        return v

    class Config:
        json_encoders = {Decimal: lambda v: float(v), datetime: lambda v: v.isoformat()}


class OrderBookData(BaseModel):
    """Order book snapshot"""

    symbol: str
    timestamp: datetime
    bids: List[tuple[Decimal, Decimal]]  # [(price, size), ...]
    asks: List[tuple[Decimal, Decimal]]  # [(price, size), ...]
    exchange: Optional[str] = None


# ============================================================================
# INDICATOR TYPES
# ============================================================================


class IndicatorData(BaseModel):
    """Technical indicator data"""

    symbol: str
    timeframe: TimeFrameEnum
    timestamp: datetime
    indicator_name: str
    value: Union[Decimal, Dict[str, Decimal]]
    signal: Optional[str] = None

    class Config:
        json_encoders = {Decimal: lambda v: float(v), datetime: lambda v: v.isoformat()}


class MultiTimeframeIndicators(BaseModel):
    """Indicators across multiple timeframes"""

    symbol: str
    timestamp: datetime
    indicators: Dict[TimeFrameEnum, Dict[str, Any]]


# ============================================================================
# SIGNAL TYPES
# ============================================================================


class TradeLevels(BaseModel):
    """Trade entry, stop loss, and take profit levels"""

    entry_price: Decimal
    stop_loss: Decimal
    take_profit: Decimal
    risk_amount: Optional[Decimal] = None
    reward_amount: Optional[Decimal] = None

    @property
    def risk_reward_ratio(self) -> float:
        """Calculate risk/reward ratio"""
        risk = abs(self.entry_price - self.stop_loss)
        reward = abs(self.take_profit - self.entry_price)
        return float(reward / risk) if risk > 0 else 0

    class Config:
        json_encoders = {Decimal: lambda v: float(v)}


class RiskRewardRatio(BaseModel):
    """Risk/Reward ratio calculation"""

    risk: Decimal
    reward: Decimal
    ratio: float
    is_valid: bool = True

    @validator("is_valid", always=True)
    def validate_ratio(cls, v, values):
        """Ensure minimum 1:4 RR ratio"""
        if "ratio" in values:
            return values["ratio"] >= 4.0
        return False


class SignalData(BaseModel):
    """Trading signal data"""

    signal_id: str
    symbol: str
    signal_type: SignalType
    signal_source: SignalSource
    strength: SignalStrength
    confidence: float = Field(ge=0, le=100)
    timeframe: TimeFrameEnum
    timestamp: datetime

    # Trade levels
    entry_price: Decimal
    stop_loss: Decimal
    take_profit: Decimal

    # Risk/Reward
    risk_reward_ratio: float
    position_size: Optional[Decimal] = None
    risk_percent: Optional[float] = None

    # Context
    market_regime: Optional[MarketRegime] = None
    indicators: Optional[Dict[str, Any]] = None
    patterns: Optional[List[str]] = None

    # Validation
    validation_status: ValidationStatus
    validation_reasons: Optional[List[str]] = None

    # Historical performance
    historical_win_rate: Optional[float] = None
    historical_trades: Optional[int] = None

    # Status
    status: SignalStatus = SignalStatus.PENDING
    created_at: datetime
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    # Notes
    description: Optional[str] = None
    tags: Optional[List[str]] = None

    @validator("confidence")
    def confidence_range(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("Confidence must be between 0 and 100")
        return v

    @validator("risk_reward_ratio")
    def validate_rr(cls, v):
        if v < 4.0:
            raise ValueError("Risk/Reward ratio must be at least 1:4")
        return v

    class Config:
        json_encoders = {Decimal: lambda v: float(v), datetime: lambda v: v.isoformat()}


# ============================================================================
# NEWS & SENTIMENT TYPES
# ============================================================================


class NewsData(BaseModel):
    """News article data"""

    news_id: str
    title: str
    content: Optional[str] = None
    source: str
    url: Optional[str] = None
    published_at: datetime
    collected_at: datetime

    # Impact & Sentiment
    impact: NewsImpact
    sentiment: SentimentScore
    sentiment_score: float = Field(ge=-1, le=1)

    # Related
    symbols: List[str] = []
    topics: List[str] = []
    keywords: List[str] = []

    # Metadata
    author: Optional[str] = None
    language: Optional[str] = "en"

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class SentimentData(BaseModel):
    """Sentiment analysis result"""

    symbol: str
    timestamp: datetime
    sentiment: SentimentScore
    sentiment_score: float = Field(ge=-1, le=1)
    confidence: float = Field(ge=0, le=1)

    # Aggregated from multiple sources
    source_count: int
    positive_ratio: float
    negative_ratio: float
    neutral_ratio: float

    # Time-weighted
    recent_sentiment: Optional[float] = None
    trending: Optional[str] = None  # "improving", "declining", "stable"


# ============================================================================
# PERFORMANCE TYPES
# ============================================================================


class TradeResult(BaseModel):
    """Result of a completed trade"""

    trade_id: str
    signal_id: str
    symbol: str
    signal_type: SignalType

    # Entry & Exit
    entry_price: Decimal
    exit_price: Decimal
    entry_time: datetime
    exit_time: datetime

    # Outcome
    outcome: TradeOutcome
    profit_loss: Decimal
    profit_loss_percent: float

    # Levels
    stop_loss: Decimal
    take_profit: Decimal
    actual_risk_reward: float

    # Metadata
    position_size: Decimal
    duration_minutes: int
    notes: Optional[str] = None

    class Config:
        json_encoders = {Decimal: lambda v: float(v), datetime: lambda v: v.isoformat()}


class PerformanceMetrics(BaseModel):
    """Performance metrics"""

    total_trades: int
    winning_trades: int
    losing_trades: int
    break_even_trades: int

    # Win Rate
    win_rate: float
    loss_rate: float

    # Profit/Loss
    total_profit: Decimal
    total_loss: Decimal
    net_profit: Decimal

    # Ratios
    profit_factor: float  # Total profit / Total loss
    avg_win: Decimal
    avg_loss: Decimal
    avg_rr_ratio: float

    # Risk metrics
    max_drawdown: float
    max_drawdown_percent: float
    sharpe_ratio: Optional[float] = None

    # Consecutive
    max_consecutive_wins: int
    max_consecutive_losses: int
    current_streak: int

    # Period
    period_start: datetime
    period_end: datetime

    class Config:
        json_encoders = {Decimal: lambda v: float(v), datetime: lambda v: v.isoformat()}


# ============================================================================
# BOT HEALTH TYPES
# ============================================================================


class BotHealthMetrics(BaseModel):
    """Bot health metrics"""

    bot_name: str
    bot_type: str
    status: BotStatus

    # Uptime
    started_at: datetime
    last_heartbeat: datetime
    uptime_seconds: int

    # Performance
    messages_processed: int
    messages_failed: int
    success_rate: float
    avg_processing_time_ms: float

    # Resources
    cpu_percent: Optional[float] = None
    memory_mb: Optional[float] = None
    disk_usage_percent: Optional[float] = None

    # Errors
    recent_errors: Optional[List[str]] = None
    error_count: int = 0

    # Health score (0-100)
    health_score: int = Field(ge=0, le=100)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# ============================================================================
# ML MODEL TYPES
# ============================================================================


class MLModelMetrics(BaseModel):
    """ML model performance metrics"""

    model_id: str
    model_type: str
    version: str

    # Training metrics
    training_accuracy: float
    validation_accuracy: float
    test_accuracy: float

    # Loss
    training_loss: float
    validation_loss: float
    test_loss: float

    # Additional metrics
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None

    # Model info
    trained_at: datetime
    training_samples: int
    training_duration_seconds: int

    # Deployment
    deployed_at: Optional[datetime] = None
    predictions_made: int = 0
    prediction_accuracy: Optional[float] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# ============================================================================
# FEEDBACK TYPES
# ============================================================================


class FeedbackData(BaseModel):
    """User feedback on signal"""

    feedback_id: str
    signal_id: str
    user_id: Optional[str] = None

    # Trade result
    trade_result: TradeResult

    # Feedback
    rating: int = Field(ge=1, le=5)
    was_accurate: bool
    comments: Optional[str] = None

    # Learning
    what_went_right: Optional[List[str]] = None
    what_went_wrong: Optional[List[str]] = None
    improvement_suggestions: Optional[List[str]] = None

    submitted_at: datetime


# ============================================================================
# VALIDATION TYPES
# ============================================================================


class ValidationResult(BaseModel):
    """Result of signal validation"""

    is_valid: bool
    validation_status: ValidationStatus
    passed_rules: List[str]
    failed_rules: List[str]
    warnings: Optional[List[str]] = None

    # Details
    risk_reward_check: bool
    win_rate_check: bool
    market_regime_check: bool
    volume_check: bool
    confluence_score: Optional[float] = None

    # Scores
    overall_score: float = Field(ge=0, le=100)
    confidence_adjustment: float = 0.0

    validated_at: datetime


# ============================================================================
# MESSAGE TYPES
# ============================================================================


class MessagePayload(BaseModel):
    """Generic message payload for RabbitMQ"""

    message_id: str
    message_type: str
    timestamp: datetime
    data: Dict[str, Any]
    source: str
    priority: Optional[int] = 5

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class NotificationMessage(BaseModel):
    """Notification message"""

    notification_id: str
    channel: NotificationChannel
    recipient: str
    subject: str
    message: str
    priority: str = "medium"

    # Attachments
    attachments: Optional[List[Dict[str, Any]]] = None

    # Metadata
    signal_id: Optional[str] = None
    created_at: datetime
    send_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# ============================================================================
# SYSTEM TYPES
# ============================================================================


class SystemHealth(BaseModel):
    """Overall system health"""

    timestamp: datetime
    is_healthy: bool
    health_score: int = Field(ge=0, le=100)

    # Components
    bots_health: Dict[str, BotHealthMetrics]
    database_health: bool
    api_health: bool
    queue_health: bool

    # Issues
    critical_issues: List[str] = []
    warnings: List[str] = []

    # Performance
    total_signals_today: int
    total_trades_today: int
    system_uptime_hours: float


class APIResponse(BaseModel):
    """Standard API response"""

    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
