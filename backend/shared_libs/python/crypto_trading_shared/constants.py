"""
Shared Constants
All system-wide constants used across bots
"""

from typing import Dict, List, Any


# ============================================================================
# TIMEFRAMES
# ============================================================================
class TimeFrame:
    """Standard timeframe constants"""

    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"


DEFAULT_TIMEFRAMES = [
    TimeFrame.M15,
    TimeFrame.M30,
    TimeFrame.H1,
    TimeFrame.H4,
    TimeFrame.D1,
]

# ============================================================================
# EXCHANGES
# ============================================================================
SUPPORTED_EXCHANGES = [
    "binance",
    "coinbase",
    "kraken",
    "bybit",
    "okx",
]

DEFAULT_EXCHANGE = "binance"

# ============================================================================
# TRADING PAIRS
# ============================================================================
SUPPORTED_SYMBOLS = [
    "BTC/USDT",
    "ETH/USDT",
    "BNB/USDT",
    "SOL/USDT",
    "XRP/USDT",
    "ADA/USDT",
    "DOGE/USDT",
    "MATIC/USDT",
    "DOT/USDT",
    "AVAX/USDT",
    "LINK/USDT",
    "UNI/USDT",
    "ATOM/USDT",
    "LTC/USDT",
    "BCH/USDT",
]

MAJOR_PAIRS = [
    "BTC/USDT",
    "ETH/USDT",
]

# ============================================================================
# API ENDPOINTS
# ============================================================================
API_ENDPOINTS = {
    "gateway": "http://api-gateway:3000",
    "signals": "/api/v1/signals",
    "news": "/api/v1/news",
    "performance": "/api/v1/performance",
    "feedback": "/api/v1/feedback",
    "health": "/api/v1/health",
}

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
DATABASE_NAMES = {
    "mysql": "crypto_trading",
    "timescale": "crypto_timeseries",
    "redis_db": 0,
    "mongodb": "crypto_ml",
}

# MySQL Tables
MYSQL_TABLES = {
    "signals": "signals",
    "news": "news_articles",
    "performance": "signal_performance",
    "feedback": "trade_feedback",
    "bot_health": "bot_health_status",
    "users": "users",
    "ml_models": "ml_model_registry",
}

# TimescaleDB Hypertables
TIMESCALE_TABLES = {
    "ohlcv": "ohlcv_data",
    "indicators": "technical_indicators",
    "orderbook": "orderbook_snapshots",
    "trades": "recent_trades",
}

# ============================================================================
# RABBITMQ CONFIGURATION
# ============================================================================
RABBITMQ_EXCHANGES = {
    "signals": "signals_exchange",
    "market_data": "market_data_exchange",
    "news": "news_exchange",
    "system": "system_exchange",
}

RABBITMQ_QUEUES = {
    # Market Data
    "market_data": "market_data_queue",
    "ohlcv": "ohlcv_queue",
    # News
    "news_raw": "news_raw_queue",
    "news_processed": "news_processed_queue",
    # Analysis
    "technical_analysis": "technical_analysis_queue",
    "sentiment_analysis": "sentiment_analysis_queue",
    "itc_analysis": "itc_analysis_queue",
    "pattern_recognition": "pattern_recognition_queue",
    # Signals
    "raw_signals": "raw_signals_queue",
    "validated_signals": "validated_signals_queue",
    "final_signals": "final_signals_queue",
    # Feedback
    "feedback": "feedback_queue",
    "ml_retraining": "ml_retraining_queue",
    # Notifications
    "notifications": "notifications_queue",
    # System
    "health_checks": "health_checks_queue",
    "errors": "errors_queue",
}

RABBITMQ_ROUTING_KEYS = {
    "signal.new": "signal.new",
    "signal.updated": "signal.updated",
    "signal.closed": "signal.closed",
    "market.price": "market.price",
    "market.volume": "market.volume",
    "news.published": "news.published",
    "news.high_impact": "news.high_impact",
    "system.error": "system.error",
    "system.health": "system.health",
}

# ============================================================================
# REDIS KEY PATTERNS
# ============================================================================
REDIS_KEYS = {
    # Cache
    "price_cache": "price:{symbol}:{timeframe}",
    "indicator_cache": "indicator:{symbol}:{indicator}:{timeframe}",
    "signal_cache": "signal:{signal_id}",
    "news_cache": "news:{news_id}",
    # Real-time Data
    "live_price": "live:price:{symbol}",
    "live_orderbook": "live:orderbook:{symbol}",
    # Session
    "user_session": "session:{user_id}",
    "bot_status": "bot:status:{bot_name}",
    # Rate Limiting
    "rate_limit": "rate_limit:{ip}:{endpoint}",
    # Locks
    "lock": "lock:{resource}",
}

REDIS_TTL = {
    "price_cache": 60,  # 1 minute
    "indicator_cache": 300,  # 5 minutes
    "signal_cache": 3600,  # 1 hour
    "news_cache": 86400,  # 24 hours
    "session": 86400,  # 24 hours
}

# ============================================================================
# RISK MANAGEMENT
# ============================================================================
RISK_LIMITS = {
    "min_risk_reward": 4.0,  # Minimum 1:4 RR ratio
    "max_risk_per_trade": 2.0,  # Max 2% risk per trade
    "max_daily_risk": 6.0,  # Max 6% daily risk
    "max_drawdown": 20.0,  # Max 20% drawdown
    "min_win_rate": 60.0,  # Minimum 60% win rate required
}

POSITION_SIZING = {
    "default_risk_percent": 1.0,  # 1% risk per trade
    "min_position_size": 10.0,  # Minimum $10 position
    "max_position_size": 10000.0,  # Maximum $10,000 position
}

# ============================================================================
# SIGNAL THRESHOLDS
# ============================================================================
SIGNAL_THRESHOLDS = {
    # Confidence thresholds
    "min_confidence": 70.0,  # Minimum 70% confidence
    "high_confidence": 85.0,  # High confidence threshold
    "very_high_confidence": 95.0,  # Very high confidence
    # Strength thresholds
    "weak_strength": 50.0,
    "medium_strength": 70.0,
    "strong_strength": 85.0,
    # Win rate thresholds
    "min_historical_win_rate": 60.0,
    "good_win_rate": 70.0,
    "excellent_win_rate": 80.0,
    # Volume thresholds
    "min_volume_ratio": 1.5,  # 1.5x average volume
    "high_volume_ratio": 3.0,  # 3x average volume
}

# ============================================================================
# TECHNICAL INDICATORS
# ============================================================================
INDICATOR_SETTINGS = {
    # Moving Averages
    "sma": [20, 50, 100, 200],
    "ema": [9, 12, 21, 26, 50, 200],
    # Momentum
    "rsi": {"period": 14, "overbought": 70, "oversold": 30},
    "macd": {"fast": 12, "slow": 26, "signal": 9},
    "stochastic": {"k": 14, "d": 3, "smooth": 3},
    # Volatility
    "bollinger": {"period": 20, "std_dev": 2},
    "atr": {"period": 14},
    "keltner": {"period": 20, "atr_mult": 2},
    # Volume
    "obv": {},
    "vwap": {},
    "volume_ma": {"period": 20},
}

# ============================================================================
# ICT CONCEPTS
# ============================================================================
ICT_SETTINGS = {
    "order_block": {
        "min_candles": 3,
        "max_candles": 10,
        "body_percent": 60,  # Minimum body size
    },
    "fair_value_gap": {
        "min_gap_percent": 0.5,  # Minimum 0.5% gap
        "max_age_candles": 50,  # Max 50 candles old
    },
    "liquidity_zone": {
        "lookback": 100,  # Look back 100 candles
        "min_touches": 2,  # Minimum 2 touches
    },
    "market_structure": {
        "swing_lookback": 10,  # Swing detection
        "bos_confirmation": 2,  # Candles for BOS
    },
}

# ============================================================================
# ML MODEL CONFIGURATION
# ============================================================================
ML_MODEL_PATHS = {
    "price_prediction": "models/price_prediction",
    "pattern_recognition": "models/pattern_recognition",
    "sentiment": "models/sentiment",
    "signal_optimizer": "models/signal_optimizer",
}

ML_MODEL_SETTINGS = {
    "retraining_interval": 7,  # Days
    "min_training_samples": 1000,
    "validation_split": 0.2,
    "test_split": 0.1,
    "early_stopping_patience": 10,
}

# ============================================================================
# NEWS SOURCES
# ============================================================================
NEWS_SOURCES = {
    "cryptopanic": {
        "api_url": "https://cryptopanic.com/api/v1",
        "rate_limit": 60,  # requests per minute
    },
    "newsapi": {
        "api_url": "https://newsapi.org/v2",
        "rate_limit": 100,
    },
    "twitter": {
        "api_url": "https://api.twitter.com/2",
        "rate_limit": 300,
    },
}

NEWS_KEYWORDS = [
    "bitcoin",
    "ethereum",
    "crypto",
    "blockchain",
    "regulation",
    "sec",
    "etf",
    "adoption",
    "hack",
    "security",
    "defi",
    "nft",
]

# ============================================================================
# NOTIFICATION SETTINGS
# ============================================================================
NOTIFICATION_SETTINGS = {
    "signal": {
        "enabled": True,
        "channels": ["telegram", "discord", "email"],
        "min_confidence": 80.0,
    },
    "high_impact_news": {
        "enabled": True,
        "channels": ["telegram", "discord"],
        "min_impact": 8.0,
    },
    "performance": {
        "enabled": True,
        "channels": ["email"],
        "frequency": "daily",
    },
    "errors": {
        "enabled": True,
        "channels": ["telegram", "email"],
        "severity": "high",
    },
}

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
LOG_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ============================================================================
# SYSTEM SETTINGS
# ============================================================================
SYSTEM_SETTINGS = {
    "bot_health_check_interval": 60,  # seconds
    "signal_expiry": 3600,  # 1 hour
    "max_concurrent_signals": 10,
    "api_timeout": 30,  # seconds
    "websocket_reconnect_delay": 5,  # seconds
    "max_retries": 3,
}

# ============================================================================
# VALIDATION RULES
# ============================================================================
VALIDATION_RULES = {
    "price": {
        "min_value": 0.000001,
        "max_value": 1000000.0,
    },
    "volume": {
        "min_value": 0.0,
        "max_value": float("inf"),
    },
    "percentage": {
        "min_value": -100.0,
        "max_value": 100.0,
    },
    "confidence": {
        "min_value": 0.0,
        "max_value": 100.0,
    },
}

# ============================================================================
# ERROR MESSAGES
# ============================================================================
ERROR_MESSAGES = {
    "database_error": "Database operation failed",
    "api_error": "API request failed",
    "validation_error": "Data validation failed",
    "signal_generation_error": "Signal generation failed",
    "ml_model_error": "ML model prediction failed",
    "insufficient_data": "Insufficient data for analysis",
}

# ============================================================================
# SUCCESS MESSAGES
# ============================================================================
SUCCESS_MESSAGES = {
    "signal_generated": "Signal generated successfully",
    "feedback_recorded": "Feedback recorded successfully",
    "model_trained": "Model trained successfully",
    "data_collected": "Data collected successfully",
}
