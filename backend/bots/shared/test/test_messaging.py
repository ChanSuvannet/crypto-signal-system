"""
Test Messaging System
=====================
Test RabbitMQ messaging between bots.
"""

import asyncio
import contextlib
from datetime import datetime, timezone
from shared.core import Config, setup_logger
from shared.messaging import (
    RabbitMQClient,
    EventPublisher,
    SignalMessage,
    MessageType,
    RoutingKey,
)


async def test_publisher():
    """Test event publisher."""
    logger = setup_logger("test_publisher")
    logger.info("Testing event publisher...")

    async with EventPublisher(bot_name="test-publisher") as publisher:

        # Publish price update
        await publisher.publish_price_update(
            symbol="BTCUSDT",
            timeframe="1h",
            open=45000.0,
            high=45500.0,
            low=44800.0,
            close=45200.0,
            volume=1234.56,
        )
        logger.info("✓ Published price update")

        # Publish signal
        await publisher.publish_signal(
            signal_id="SIG_001",
            symbol="BTCUSDT",
            signal_type="BUY",
            timeframe="4h",
            entry_price=45000.0,
            stop_loss=44000.0,
            take_profit_1=49000.0,
            risk_reward_ratio=4.0,
            final_confidence=85.5,
            reasoning="Strong bullish momentum with RSI oversold",
        )
        logger.info("✓ Published trading signal")

        # Publish notification
        await publisher.publish_notification(
            title="Test Notification",
            message_text="System is working correctly!",
            notification_type="INFO",
        )
        logger.info("✓ Published notification")

        # Publish heartbeat
        await publisher.publish_heartbeat(
            status="RUNNING", uptime_seconds=3600, success_count=100, error_count=2
        )
        logger.info("✓ Published heartbeat")


async def test_consumer():
    """Test message consumer."""
    logger = setup_logger("test_consumer")
    logger.info("Testing message consumer...")

    async with RabbitMQClient() as client:

        # Define message handler
        async def handle_signal(message):
            logger.info(
                f"""
╔════════════════════════════════════════════╗
║           SIGNAL RECEIVED                  ║
╚════════════════════════════════════════════╝
  Signal ID:       {message.signal_id}
  Symbol:          {message.symbol}
  Type:            {message.signal_type}
  Entry:           ${message.entry_price}
  Stop Loss:       ${message.stop_loss}
  Take Profit:     ${message.take_profit_1}
  Risk/Reward:     1:{message.risk_reward_ratio}
  Confidence:      {message.final_confidence}%
════════════════════════════════════════════
            """
            )

        # Declare and bind queue
        await client.declare_queue(
            queue_name="test_signal_queue",
            routing_keys=[RoutingKey.signal("BTCUSDT", "*")],
            exchange="crypto_signals",
        )

        # Start consuming
        await client.consume(queue_name="test_signal_queue", callback=handle_signal)

        logger.info("Started consuming signals. Waiting for messages...")

        # Keep running
        await asyncio.sleep(30)


async def test_pub_sub():
    """Test full pub/sub flow."""
    logger = setup_logger("test_pubsub")
    logger.info("Testing pub/sub flow...")

    # Start consumer in background
    consumer_task = asyncio.create_task(test_consumer())

    # Wait a bit for consumer to setup
    await asyncio.sleep(2)

    # Publish messages
    await test_publisher()

    # Wait for consumer to process
    await asyncio.sleep(3)

    # Cancel consumer
    consumer_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await consumer_task
    logger.info("✅ Pub/sub test complete!")


async def main():
    """Run all tests."""
    logger = setup_logger("test_main")

    try:
        logger.info("🚀 Starting messaging system tests...")

        # Test individual components
        await test_publisher()

        # Test pub/sub
        # await test_pub_sub()  # Uncomment to test full flow

        logger.info("✅ All messaging tests passed!")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
