
# ============================================
# Crypto Trading Signal System
# backed/bots/shared/messaging/rabbitmq_client.py
# Deception: Async RabbitMQ client for message publishing and consuming.
# ============================================


import asyncio
import json
from typing import Optional, Callable, Dict, Any, List
from aio_pika import (
    connect_robust,
    Message,
    DeliveryMode,
    ExchangeType,
    Connection,
    Channel,
    Exchange,
    Queue,
)
from aio_pika.abc import AbstractIncomingMessage

from ..core.config import Config
from ..core.logger import get_logger
from ..core.exceptions import BotConnectionError, BotError, retry_on_error
from .message_types import BaseMessage, MessageFactory, MessageType, MessagePriority


class RabbitMQClient:
    """
    Async RabbitMQ client for pub/sub messaging.

    Features:
    - Topic-based routing
    - Persistent messages
    - Automatic reconnection
    - Dead letter queues
    - Message acknowledgment
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize RabbitMQ client.

        Args:
            config: Configuration instance
        """
        self.config = config or Config()
        self.logger = get_logger("rabbitmq_client")

        self.connection: Optional[Connection] = None
        self.channel: Optional[Channel] = None
        self.exchanges: Dict[str, Exchange] = {}
        self.queues: Dict[str, Queue] = {}
        self._is_connected = False

        # Default exchange names
        self.signals_exchange = "crypto_signals"
        self.events_exchange = "crypto_events"
        self.dlx_exchange = "crypto_dlx"  # Dead letter exchange

    async def connect(self):
        """Establish RabbitMQ connection."""
        if self._is_connected:
            self.logger.warning("RabbitMQ client is already connected")
            return

        try:
            # Get RabbitMQ URL
            rabbitmq_url = self.config.get_rabbitmq_url()

            # Create robust connection (auto-reconnect)
            self.connection = await connect_robust(
                rabbitmq_url, heartbeat=60, connection_class=Connection
            )

            # Create channel
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)

            # Declare exchanges
            await self._declare_exchanges()

            self._is_connected = True
            self.logger.info("✓ Connected to RabbitMQ")

        except Exception as e:
            self.logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise BotConnectionError(
                f"RabbitMQ connection failed: {str(e)}", service="RabbitMQ"
            )

    async def disconnect(self):
        """Close RabbitMQ connection."""
        if not self._is_connected:
            return

        try:
            if self.connection:
                await self.connection.close()

            self._is_connected = False
            self.logger.info("✓ Disconnected from RabbitMQ")

        except Exception as e:
            self.logger.error(f"Error disconnecting from RabbitMQ: {e}")

    async def _declare_exchanges(self):
        """Declare exchanges."""
        # Signals exchange (topic)
        self.exchanges[self.signals_exchange] = await self.channel.declare_exchange(
            self.signals_exchange, ExchangeType.TOPIC, durable=True
        )

        # Events exchange (topic)
        self.exchanges[self.events_exchange] = await self.channel.declare_exchange(
            self.events_exchange, ExchangeType.TOPIC, durable=True
        )

        # Dead letter exchange (fanout)
        self.exchanges[self.dlx_exchange] = await self.channel.declare_exchange(
            self.dlx_exchange, ExchangeType.FANOUT, durable=True
        )

        self.logger.info("Exchanges declared successfully")

    @retry_on_error(max_attempts=3)
    async def publish(
        self,
        message: BaseMessage,
        exchange: str,
        routing_key: str,
        priority: Optional[MessagePriority] = None,
    ):
        """
        Publish message to exchange.

        Args:
            message: Message to publish
            exchange: Exchange name
            routing_key: Routing key
            priority: Message priority (overrides message.priority)
        """
        if not self._is_connected:
            await self.connect()

        try:
            # Get priority
            priority_value = (priority or message.priority).value

            # Create message
            message_body = message.to_json().encode()

            aio_message = Message(
                body=message_body,
                delivery_mode=DeliveryMode.PERSISTENT,
                priority=priority_value,
                content_type="application/json",
                headers={
                    "message_type": message.message_type.value,
                    "source_bot": message.source_bot,
                    "timestamp": message.timestamp.isoformat(),
                },
            )

            # Get exchange
            exch = self.exchanges.get(exchange)
            if not exch:
                raise BotError(f"Exchange not found: {exchange}")

            # Publish
            await exch.publish(aio_message, routing_key=routing_key)

            self.logger.debug(
                f"Published {message.message_type.value} to {exchange}:{routing_key}"
            )

        except Exception as e:
            self.logger.error(f"Failed to publish message: {e}")
            raise BotError(f"Message publishing failed: {str(e)}")

    async def declare_queue(
        self,
        queue_name: str,
        routing_keys: List[str],
        exchange: str,
        durable: bool = True,
        auto_delete: bool = False,
        exclusive: bool = False,
        dlx: bool = True,
    ) -> Queue:
        """
        Declare and bind queue.

        Args:
            queue_name: Queue name
            routing_keys: List of routing keys to bind
            exchange: Exchange name
            durable: Whether queue survives broker restart
            auto_delete: Delete queue when no consumers
            exclusive: Queue can only be accessed by current connection
            dlx: Enable dead letter exchange

        Returns:
            Queue instance
        """
        if not self._is_connected:
            await self.connect()

        try:
            # Queue arguments
            arguments = {}
            if dlx:
                arguments["x-dead-letter-exchange"] = self.dlx_exchange
                arguments["x-message-ttl"] = 86400000  # 24 hours

            # Declare queue
            queue = await self.channel.declare_queue(
                queue_name,
                durable=durable,
                auto_delete=auto_delete,
                exclusive=exclusive,
                arguments=arguments if arguments else None,
            )

            # Bind to exchange with routing keys
            exch = self.exchanges.get(exchange)
            if exch:
                for routing_key in routing_keys:
                    await queue.bind(exch, routing_key=routing_key)
                    self.logger.debug(f"Bound queue {queue_name} to {routing_key}")

            self.queues[queue_name] = queue
            self.logger.info(f"Queue '{queue_name}' declared and bound")

            return queue

        except Exception as e:
            self.logger.error(f"Failed to declare queue: {e}")
            raise BotError(f"Queue declaration failed: {str(e)}")

    async def consume(
        self,
        queue_name: str,
        callback: Callable[[BaseMessage], None],
        auto_ack: bool = False,
    ):
        """
        Start consuming messages from queue.

        Args:
            queue_name: Queue name
            callback: Async callback function to handle messages
            auto_ack: Automatically acknowledge messages
        """
        if not self._is_connected:
            await self.connect()

        try:
            queue = self.queues.get(queue_name)
            if not queue:
                raise BotError(f"Queue not found: {queue_name}")

            async def message_handler(message: AbstractIncomingMessage):
                """Handle incoming message."""
                async with message.process(ignore_processed=True):
                    try:
                        # Parse message
                        body = message.body.decode()
                        msg = MessageFactory.from_json(body)

                        # Call callback
                        await callback(msg)

                        # Acknowledge if not auto-ack
                        if not auto_ack:
                            await message.ack()

                        self.logger.debug(
                            f"Processed message: {msg.message_type.value}"
                        )

                    except Exception as e:
                        self.logger.error(f"Error processing message: {e}")
                        # Reject and requeue
                        await message.reject(requeue=False)

            # Start consuming
            await queue.consume(message_handler, no_ack=auto_ack)

            self.logger.info(f"Started consuming from queue: {queue_name}")

        except Exception as e:
            self.logger.error(f"Failed to start consuming: {e}")
            raise BotError(f"Consumer start failed: {str(e)}")

    async def purge_queue(self, queue_name: str):
        """
        Purge all messages from queue.

        Args:
            queue_name: Queue name
        """
        try:
            queue = self.queues.get(queue_name)
            if queue:
                await queue.purge()
                self.logger.info(f"Purged queue: {queue_name}")
        except Exception as e:
            self.logger.error(f"Failed to purge queue: {e}")
            raise BotError(f"Queue purge failed: {str(e)}")

    async def delete_queue(self, queue_name: str):
        """
        Delete queue.

        Args:
            queue_name: Queue name
        """
        try:
            queue = self.queues.get(queue_name)
            if queue:
                await queue.delete()
                del self.queues[queue_name]
                self.logger.info(f"Deleted queue: {queue_name}")
        except Exception as e:
            self.logger.error(f"Failed to delete queue: {e}")
            raise BotError(f"Queue deletion failed: {str(e)}")

    async def get_queue_info(self, queue_name: str) -> Dict[str, Any]:
        """
        Get queue information.

        Args:
            queue_name: Queue name

        Returns:
            Queue information
        """
        try:
            queue = self.queues.get(queue_name)
            if queue:
                declaration_result = await queue.declare(passive=True)
                return {
                    "name": queue_name,
                    "message_count": declaration_result.message_count,
                    "consumer_count": declaration_result.consumer_count,
                }
            return {}
        except Exception as e:
            self.logger.error(f"Failed to get queue info: {e}")
            return {}

    async def health_check(self) -> Dict[str, Any]:
        """
        Check RabbitMQ health.

        Returns:
            Health check results
        """
        try:
            if not self._is_connected or not self.connection:
                return {"healthy": False, "connected": False, "error": "Not connected"}

            # Check if connection is open
            is_open = not self.connection.is_closed

            # Get queue information
            queue_info = {}
            for queue_name in self.queues.keys():
                queue_info[queue_name] = await self.get_queue_info(queue_name)

            return {
                "healthy": is_open,
                "connected": self._is_connected,
                "connection_open": is_open,
                "exchanges": list(self.exchanges.keys()),
                "queues": queue_info,
            }
        except Exception as e:
            return {"healthy": False, "connected": False, "error": str(e)}

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
