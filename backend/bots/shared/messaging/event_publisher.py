# ============================================
# Crypto Trading Signal System
# backed/bots/shared/messaging/event_publisher.py
# Deception: High-level interface for publishing events.
# ============================================


# ============================================ Standard Library
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from decimal import Decimal

# ============================================ Custom Library
from ..core.logger import get_logger
from ..core.config import Config
from .rabbitmq_client import RabbitMQClient
from .message_types import (
    MessageType,
    MessagePriority,
    PriceUpdateMessage,
    NewsArticleMessage,
    SignalMessage,
    TechnicalAnalysisMessage,
    PatternDetectedMessage,
    PredictionMessage,
    NotificationMessage,
    BotHeartbeatMessage,
    CommandMessage,
    ResponseMessage,
    RoutingKey,
)


class EventPublisher:
    """
    High-level event publisher for bots.

    Simplifies publishing common events with appropriate routing.
    """

    def __init__(
        self,
        bot_name: str,
        config: Optional[Config] = None,
        rabbitmq_client: Optional[RabbitMQClient] = None,
    ):
        """
        Initialize event publisher.

        Args:
            bot_name: Name of the bot publishing events
            config: Configuration instance
            rabbitmq_client: RabbitMQ client (creates new if None)
        """
        self.bot_name = bot_name
        self.config = config or Config()
        self.logger = get_logger(f"event_publisher_{bot_name}")

        self.rabbitmq = rabbitmq_client or RabbitMQClient(config)
        self._own_client = rabbitmq_client is None

    async def connect(self):
        """Connect to RabbitMQ."""
        if self._own_client:
            await self.rabbitmq.connect()

    async def disconnect(self):
        """Disconnect from RabbitMQ."""
        if self._own_client:
            await self.rabbitmq.disconnect()

    def _generate_message_id(self) -> str:
        """Generate unique message ID."""
        return f"{self.bot_name}_{uuid.uuid4().hex[:12]}"

    async def publish_price_update(
        self,
        symbol: str,
        timeframe: str,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: float,
        **kwargs,
    ):
        """
        Publish price update event.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            open: Open price
            high: High price
            low: Low price
            close: Close price
            volume: Volume
            **kwargs: Additional fields
        """
        message = PriceUpdateMessage(
            message_id=self._generate_message_id(),
            timestamp=datetime.utcnow(),
            source_bot=self.bot_name,
            symbol=symbol,
            timeframe=timeframe,
            open=open,
            high=high,
            low=low,
            close=close,
            volume=volume,
            **kwargs,
        )

        routing_key = RoutingKey.price_update(symbol, timeframe)

        await self.rabbitmq.publish(
            message, exchange="crypto_events", routing_key=routing_key
        )

        self.logger.debug(f"Published price update: {symbol} {timeframe}")

    async def publish_news_article(
        self,
        article_id: str,
        title: str,
        url: str,
        source: str,
        published_at: datetime,
        symbol: str,
        sentiment_score: float,
        sentiment_label: str,
        impact_score: float,
        impact_level: str,
        **kwargs,
    ):
        """
        Publish news article event.

        Args:
            article_id: Unique article ID
            title: Article title
            url: Article URL
            source: News source
            published_at: Publication timestamp
            symbol: Related crypto symbol
            sentiment_score: Sentiment score (-1 to 1)
            sentiment_label: Sentiment label
            impact_score: Impact score (0-100)
            impact_level: Impact level
            **kwargs: Additional fields
        """
        category = kwargs.pop("category", "GENERAL")
        message = NewsArticleMessage(
            message_id=self._generate_message_id(),
            timestamp=datetime.now(timezone.utc),
            source_bot=self.bot_name,
            article_id=article_id,
            title=title,
            url=url,
            source=source,
            published_at=published_at,
            symbol=symbol,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            impact_score=impact_score,
            impact_level=impact_level,
            category=category,
            **kwargs,
        )

        routing_key = RoutingKey.news(symbol, category)

        # High priority for high impact news
        priority = (
            MessagePriority.HIGH
            if impact_level in {"HIGH", "CRITICAL"}
            else MessagePriority.NORMAL
        )

        await self.rabbitmq.publish(
            message,
            exchange="crypto_events",
            routing_key=routing_key,
            priority=priority,
        )

        self.logger.debug(f"Published news article: {title[:50]}")

    async def publish_signal(
        self,
        signal_id: str,
        symbol: str,
        signal_type: str,
        timeframe: str,
        entry_price: float,
        stop_loss: float,
        take_profit_1: float,
        risk_reward_ratio: float,
        final_confidence: float,
        **kwargs,
    ):
        """
        Publish trading signal.

        Args:
            signal_id: Unique signal ID
            symbol: Trading symbol
            signal_type: BUY or SELL
            timeframe: Timeframe
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit_1: First take profit
            risk_reward_ratio: Risk/reward ratio
            final_confidence: Final confidence score
            **kwargs: Additional fields
        """
        message = SignalMessage(
            message_id=self._generate_message_id(),
            timestamp=datetime.utcnow(),
            source_bot=self.bot_name,
            signal_id=signal_id,
            symbol=symbol,
            signal_type=signal_type,
            timeframe=timeframe,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit_1=take_profit_1,
            risk_reward_ratio=risk_reward_ratio,
            final_confidence=final_confidence,
            **kwargs,
        )

        # Validate signal
        if not message.validate():
            self.logger.error(f"Invalid signal data: {signal_id}")
            return

        routing_key = RoutingKey.signal(symbol, signal_type)

        # High priority for high confidence signals
        priority = (
            MessagePriority.HIGH if final_confidence >= 80 else MessagePriority.NORMAL
        )

        await self.rabbitmq.publish(
            message,
            exchange="crypto_signals",
            routing_key=routing_key,
            priority=priority,
        )

        self.logger.info(f"Published signal: {signal_type} {symbol} @ {entry_price}")

    async def publish_technical_analysis(
        self, symbol: str, timeframe: str, indicators: Dict[str, float], **kwargs
    ):
        """
        Publish technical analysis results.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            indicators: Dictionary of indicator values
            **kwargs: Additional fields (buy_signals, sell_signals, etc.)
        """
        message = TechnicalAnalysisMessage(
            message_id=self._generate_message_id(),
            timestamp=datetime.utcnow(),
            source_bot=self.bot_name,
            symbol=symbol,
            timeframe=timeframe,
            indicators=indicators,
            **kwargs,
        )

        routing_key = RoutingKey.technical(symbol, timeframe)

        await self.rabbitmq.publish(
            message, exchange="crypto_events", routing_key=routing_key
        )

        self.logger.debug(f"Published technical analysis: {symbol} {timeframe}")

    async def publish_pattern_detected(
        self,
        symbol: str,
        timeframe: str,
        pattern_type: str,
        pattern_category: str,
        direction: str,
        confidence: float,
        pattern_start_price: float,
        pattern_end_price: float,
        **kwargs,
    ):
        """
        Publish pattern detection event.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            pattern_type: Type of pattern
            pattern_category: Category (REVERSAL, CONTINUATION, etc.)
            direction: BULLISH or BEARISH
            confidence: Confidence score
            pattern_start_price: Pattern start price
            pattern_end_price: Pattern end price
            **kwargs: Additional fields
        """
        message = PatternDetectedMessage(
            message_id=self._generate_message_id(),
            timestamp=datetime.utcnow(),
            source_bot=self.bot_name,
            symbol=symbol,
            timeframe=timeframe,
            pattern_type=pattern_type,
            pattern_category=pattern_category,
            direction=direction,
            confidence=confidence,
            pattern_start_price=pattern_start_price,
            pattern_end_price=pattern_end_price,
            **kwargs,
        )

        routing_key = f"pattern.{symbol}.{direction.lower()}"

        priority = MessagePriority.HIGH if confidence >= 80 else MessagePriority.NORMAL

        await self.rabbitmq.publish(
            message,
            exchange="crypto_events",
            routing_key=routing_key,
            priority=priority,
        )

        self.logger.info(f"Published pattern: {pattern_type} {direction} on {symbol}")

    async def publish_prediction(
        self,
        symbol: str,
        model_name: str,
        model_version: str,
        prediction_type: str,
        confidence: float,
        prediction_horizon: str,
        **kwargs,
    ):
        """
        Publish ML prediction.

        Args:
            symbol: Trading symbol
            model_name: Name of the model
            model_version: Model version
            prediction_type: Type of prediction
            confidence: Confidence score
            prediction_horizon: Prediction timeframe
            **kwargs: Additional fields (predicted_value, predicted_direction, etc.)
        """
        message = PredictionMessage(
            message_id=self._generate_message_id(),
            timestamp=datetime.utcnow(),
            source_bot=self.bot_name,
            symbol=symbol,
            model_name=model_name,
            model_version=model_version,
            prediction_type=prediction_type,
            confidence=confidence,
            prediction_horizon=prediction_horizon,
            **kwargs,
        )

        routing_key = f"prediction.{symbol}.{prediction_type.lower()}"

        await self.rabbitmq.publish(
            message, exchange="crypto_events", routing_key=routing_key
        )

        self.logger.debug(f"Published prediction: {model_name} for {symbol}")

    async def publish_notification(
        self,
        title: str,
        message_text: str,
        notification_type: str = "INFO",
        channels: List[str] = None,
        **kwargs,
    ):
        """
        Publish notification.

        Args:
            title: Notification title
            message_text: Notification message
            notification_type: Type (INFO, WARNING, ERROR, ALERT)
            channels: List of channels (telegram, discord, email)
            **kwargs: Additional fields
        """
        message = NotificationMessage(
            message_id=self._generate_message_id(),
            timestamp=datetime.utcnow(),
            source_bot=self.bot_name,
            title=title,
            message=message_text,
            notification_type=notification_type,
            channels=channels or ["telegram"],
            **kwargs,
        )

        routing_key = RoutingKey.notification(notification_type.lower())

        priority = {
            "INFO": MessagePriority.LOW,
            "WARNING": MessagePriority.NORMAL,
            "ERROR": MessagePriority.HIGH,
            "ALERT": MessagePriority.CRITICAL,
        }.get(notification_type, MessagePriority.NORMAL)

        await self.rabbitmq.publish(
            message,
            exchange="crypto_events",
            routing_key=routing_key,
            priority=priority,
        )

        self.logger.info(f"Published notification: {title}")

    async def publish_heartbeat(
        self,
        status: str,
        uptime_seconds: int,
        success_count: int = 0,
        error_count: int = 0,
        **kwargs,
    ):
        """
        Publish bot heartbeat.

        Args:
            status: Bot status (RUNNING, STOPPED, etc.)
            uptime_seconds: Uptime in seconds
            success_count: Number of successful operations
            error_count: Number of errors
            **kwargs: Additional fields
        """
        message = BotHeartbeatMessage(
            message_id=self._generate_message_id(),
            timestamp=datetime.utcnow(),
            source_bot=self.bot_name,
            bot_name=self.bot_name,
            status=status,
            uptime_seconds=uptime_seconds,
            success_count=success_count,
            error_count=error_count,
            **kwargs,
        )

        routing_key = RoutingKey.bot_event(self.bot_name, "heartbeat")

        await self.rabbitmq.publish(
            message,
            exchange="crypto_events",
            routing_key=routing_key,
            priority=MessagePriority.LOW,
        )

        self.logger.debug(f"Published heartbeat: {status}")

    async def send_command(
        self, target_bot: str, command: str, parameters: Dict[str, Any] = None
    ):
        """
        Send command to another bot.

        Args:
            target_bot: Target bot name
            command: Command (START, STOP, RESTART, etc.)
            parameters: Command parameters
        """
        message = CommandMessage(
            message_id=self._generate_message_id(),
            timestamp=datetime.utcnow(),
            source_bot=self.bot_name,
            target_bot=target_bot,
            command=command,
            parameters=parameters or {},
        )

        routing_key = RoutingKey.bot_event(target_bot, "command")

        await self.rabbitmq.publish(
            message,
            exchange="crypto_events",
            routing_key=routing_key,
            priority=MessagePriority.HIGH,
        )

        self.logger.info(f"Sent command {command} to {target_bot}")

    async def send_response(
        self, command_id: str, status: str, result: Any = None, error: str = None
    ):
        """
        Send response to command.

        Args:
            command_id: Original command ID
            status: Response status (SUCCESS, FAILED, PENDING)
            result: Result data
            error: Error message if failed
        """
        message = ResponseMessage(
            message_id=self._generate_message_id(),
            timestamp=datetime.utcnow(),
            source_bot=self.bot_name,
            command_id=command_id,
            status=status,
            result=result,
            error=error,
        )

        routing_key = RoutingKey.bot_event(self.bot_name, "response")

        await self.rabbitmq.publish(
            message, exchange="crypto_events", routing_key=routing_key
        )

        self.logger.debug(f"Sent response: {status}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
