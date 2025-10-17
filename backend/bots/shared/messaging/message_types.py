# ============================================
# Crypto Trading Signal System
# backed/bots/shared/messaging/message_types.py
# Deception: Message schemas and types for inter-bot communication.
# ============================================


from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field, asdict
from decimal import Decimal
import json


class MessageType(str, Enum):
    """Types of messages that can be sent between bots."""

    # Market Data
    PRICE_UPDATE = "price_update"
    ORDERBOOK_UPDATE = "orderbook_update"
    TRADE_UPDATE = "trade_update"

    # News & Sentiment
    NEWS_ARTICLE = "news_article"
    SENTIMENT_UPDATE = "sentiment_update"
    NEWS_ALERT = "news_alert"

    # Signals
    SIGNAL_GENERATED = "signal_generated"
    SIGNAL_VALIDATED = "signal_validated"
    SIGNAL_INVALIDATED = "signal_invalidated"
    SIGNAL_EXECUTED = "signal_executed"
    SIGNAL_CLOSED = "signal_closed"

    # Analysis
    TECHNICAL_ANALYSIS = "technical_analysis"
    ITC_ANALYSIS = "itc_analysis"
    PATTERN_DETECTED = "pattern_detected"

    # ML & Predictions
    PREDICTION_UPDATE = "prediction_update"
    MODEL_TRAINED = "model_trained"
    MODEL_DEPLOYED = "model_deployed"

    # System Events
    BOT_STARTED = "bot_started"
    BOT_STOPPED = "bot_stopped"
    BOT_ERROR = "bot_error"
    BOT_HEARTBEAT = "bot_heartbeat"

    # Notifications
    NOTIFICATION = "notification"
    ALERT = "alert"

    # Commands
    COMMAND = "command"
    RESPONSE = "response"


class MessagePriority(int, Enum):
    """Message priority levels."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class BaseMessage:
    """Base message class for all messages."""

    message_type: MessageType
    message_id: str
    timestamp: datetime
    source_bot: str
    priority: MessagePriority = MessagePriority.NORMAL
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        data = asdict(self)

        # Convert enums to values
        data["message_type"] = self.message_type.value
        data["priority"] = self.priority.value

        # Convert datetime to ISO format
        data["timestamp"] = self.timestamp.isoformat()

        # Convert Decimal to float
        data = self._convert_decimals(data)

        return data

    @staticmethod
    def _convert_decimals(obj):
        """Recursively convert Decimal to float."""
        if isinstance(obj, dict):
            return {k: BaseMessage._convert_decimals(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [BaseMessage._convert_decimals(item) for item in obj]
        elif isinstance(obj, Decimal):
            return float(obj)
        return obj

    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create message from dictionary."""
        # Convert string enums back
        if "message_type" in data:
            data["message_type"] = MessageType(data["message_type"])
        if "priority" in data:
            data["priority"] = MessagePriority(data["priority"])

        # Convert ISO string to datetime
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])

        return cls(**data)


@dataclass
class PriceUpdateMessage(BaseMessage):
    """Price update message."""

    symbol: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: Optional[float] = None
    trades_count: Optional[int] = None

    def __post_init__(self):
        self.message_type = MessageType.PRICE_UPDATE

    @dataclass
    class NewsArticleMessage(BaseMessage):
        """News article message."""

        article_id: str
        title: str
        url: str
        source: str
        published_at: datetime
        symbol: str
        sentiment_score: float
        sentiment_label: str
        impact_score: float
        impact_level: str
        summary: Optional[str] = None
        category: Optional[str] = None
        keywords: List[str] = field(default_factory=list)

        def __post_init__(self):
            self.message_type = MessageType.NEWS_ARTICLE

    @dataclass
    class SignalMessage(BaseMessage):
        """Trading signal message."""

        signal_id: str
        symbol: str
        signal_type: str  # BUY or SELL
        timeframe: str

        # Prices
        entry_price: float
        stop_loss: float
        take_profit_1: float
        take_profit_2: Optional[float] = None
        take_profit_3: Optional[float] = None

        # Risk/Reward
        risk_reward_ratio: float
        position_size_recommended: Optional[float] = None

        # Confidence
        final_confidence: float
        technical_confidence: Optional[float] = None
        sentiment_confidence: Optional[float] = None
        itc_confidence: Optional[float] = None
        ml_confidence: Optional[float] = None

        # Context
        market_regime: Optional[str] = None
        volatility_level: Optional[str] = None

        # Reasoning
        reasoning: Optional[str] = None
        key_levels: Optional[Dict[str, float]] = None

    def __post_init__(self):
        self.message_type = MessageType.SIGNAL_GENERATED

    def validate(self) -> bool:
        """Validate signal data."""
        # Check required fields
        if not all(
            [
                self.signal_id,
                self.symbol,
                self.signal_type in ["BUY", "SELL"],
                self.entry_price > 0,
                self.stop_loss > 0,
                self.take_profit_1 > 0,
                self.risk_reward_ratio >= 4.0,
                0 <= self.final_confidence <= 100,
            ]
        ):
            return False

        # Validate price logic for BUY
        if self.signal_type == "BUY" and not (
            self.stop_loss < self.entry_price < self.take_profit_1
        ):
            return False
        elif self.signal_type == "SELL":
            if not (self.take_profit_1 < self.entry_price < self.stop_loss):
                return False

    @dataclass
    class TechnicalAnalysisMessage(BaseMessage):
        """Technical analysis results message."""

        symbol: str
        timeframe: str

        # Indicators
        indicators: Dict[str, float]

        # Signals
        buy_signals: List[str] = field(default_factory=list)
        sell_signals: List[str] = field(default_factory=list)

        # Trend
        trend_direction: Optional[str] = None
        trend_strength: Optional[float] = None

        # Support/Resistance
        support_levels: List[float] = field(default_factory=list)
        resistance_levels: List[float] = field(default_factory=list)

        def __post_init__(self):
            self.message_type = MessageType.TECHNICAL_ANALYSIS

    @dataclass
    class PatternDetectedMessage(BaseMessage):
        """Pattern detection message."""

        symbol: str
        timeframe: str
        pattern_type: str
        pattern_category: str  # REVERSAL, CONTINUATION, BILATERAL
        direction: str  # BULLISH or BEARISH
        confidence: float

        # Price levels
        pattern_start_price: float
        pattern_end_price: float
        target_price: Optional[float] = None
        stop_loss_price: Optional[float] = None

        # Coordinates for charting
        coordinates: Optional[List[Dict[str, Any]]] = None

        def __post_init__(self):
            self.message_type = MessageType.PATTERN_DETECTED

    @dataclass
    class PredictionMessage(BaseMessage):
        """ML prediction message."""

        symbol: str
        model_name: str
        model_version: str

        # Prediction
        prediction_type: str  # PRICE, DIRECTION, PATTERN, etc.
        predicted_value: Optional[float] = None
        predicted_direction: Optional[str] = None
        confidence: float
        prediction_horizon: str  # e.g., "1h", "4h", "1d"

        # Input features used
        features: Optional[Dict[str, Any]] = None

        def __post_init__(self):
            self.message_type = MessageType.PREDICTION_UPDATE

    @dataclass
    class NotificationMessage(BaseMessage):
        """Notification message."""

        title: str
        message: str
        notification_type: str  # INFO, WARNING, ERROR, ALERT

        # Channels
        channels: List[str] = field(default_factory=lambda: ["telegram"])

        # Attachments
        image_url: Optional[str] = None
        chart_data: Optional[Dict[str, Any]] = None

        # Actions
        action_url: Optional[str] = None
        action_buttons: Optional[List[Dict[str, str]]] = None

        def __post_init__(self):
            self.message_type = MessageType.NOTIFICATION

    @dataclass
    class BotHeartbeatMessage(BaseMessage):
        """Bot heartbeat message."""

        bot_name: str
        status: str  # RUNNING, STOPPED, ERROR, DEGRADED
        uptime_seconds: int

        # Performance metrics
        cpu_usage: Optional[float] = None
        memory_usage_mb: Optional[int] = None

        # Counters
        success_count: int = 0
        error_count: int = 0

        # Last operations
        last_successful_operation: Optional[datetime] = None
        last_error: Optional[str] = None

        def __post_init__(self):
            self.message_type = MessageType.BOT_HEARTBEAT

    @dataclass
    class CommandMessage(BaseMessage):
        """Command message for bot control."""

        target_bot: str
        command: str  # START, STOP, RESTART, PAUSE, RESUME, STATUS
        parameters: Dict[str, Any] = field(default_factory=dict)

        def __post_init__(self):
            self.message_type = MessageType.COMMAND

    @dataclass
    class ResponseMessage(BaseMessage):
        """Response to command message."""

        command_id: str
        status: str  # SUCCESS, FAILED, PENDING
        result: Optional[Any] = None
        error: Optional[str] = None

        def __post_init__(self):
            self.message_type = MessageType.RESPONSE

    # Message factory
    class MessageFactory:
        """Factory for creating messages from dictionaries."""

        MESSAGE_CLASSES = {
            MessageType.PRICE_UPDATE: PriceUpdateMessage,
            MessageType.NEWS_ARTICLE: NewsArticleMessage,
            MessageType.SIGNAL_GENERATED: SignalMessage,
            MessageType.TECHNICAL_ANALYSIS: TechnicalAnalysisMessage,
            MessageType.PATTERN_DETECTED: PatternDetectedMessage,
            MessageType.PREDICTION_UPDATE: PredictionMessage,
            MessageType.NOTIFICATION: NotificationMessage,
            MessageType.BOT_HEARTBEAT: BotHeartbeatMessage,
            MessageType.COMMAND: CommandMessage,
            MessageType.RESPONSE: ResponseMessage,
        }

    @classmethod
    def create_message(cls, data: Dict[str, Any]) -> BaseMessage:
        """
        Create appropriate message type from dictionary.

        Args:
            data: Message data dictionary

        Returns:
            Message instance
        """
        message_type = MessageType(data.get("message_type"))
        message_class = cls.MESSAGE_CLASSES.get(message_type, BaseMessage)

        return message_class.from_dict(data)

    @classmethod
    def from_json(cls, json_str: str) -> BaseMessage:
        """
        Create message from JSON string.

        Args:
            json_str: JSON string

        Returns:
            Message instance
        """
        data = json.loads(json_str)
        return cls.create_message(data)


    # Routing keys helper
    class RoutingKey:
        """Helper class for generating routing keys."""

        @staticmethod
        def price_update(symbol: str, timeframe: str = "*") -> str:
            """Generate routing key for price updates."""
            return f"price.{symbol}.{timeframe}"

        @staticmethod
        def news(symbol: str = "*", category: str = "*") -> str:
            """Generate routing key for news."""
            return f"news.{symbol}.{category}"

        @staticmethod
        def signal(symbol: str = "*", signal_type: str = "*") -> str:
            """Generate routing key for signals."""
            return f"signal.{symbol}.{signal_type}"

        @staticmethod
        def technical(symbol: str = "*", timeframe: str = "*") -> str:
            """Generate routing key for technical analysis."""
            return f"technical.{symbol}.{timeframe}"

        @staticmethod
        def bot_event(bot_name: str, event_type: str = "*") -> str:
            """Generate routing key for bot events."""
            return f"bot.{bot_name}.{event_type}"

        @staticmethod
        def notification(level: str = "*") -> str:
            """Generate routing key for notifications."""
            return f"notification.{level}"
