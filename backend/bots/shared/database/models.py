# ============================================
# Crypto Trading Signal System
# backed/bots/shared/database/models.py
# Deception: Database models for MySQL/TimescaleDB.
# ============================================
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    Boolean,
    Enum as SQLEnum,
    JSON,
    DECIMAL,
    BigInteger,
    Index,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Base class for all models
Base = declarative_base()


# ==================== SIGNALS & TRADING ====================
class Signal(Base):
    """Trading signals table."""

    __tablename__ = "signals"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    signal_id = Column(String(50), unique=True, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(
        SQLEnum("1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"), nullable=False
    )
    signal_type = Column(SQLEnum("BUY", "SELL"), nullable=False)

    # Entry, Stop Loss, Take Profit
    entry_price = Column(DECIMAL(20, 8), nullable=False)
    stop_loss = Column(DECIMAL(20, 8), nullable=False)
    take_profit_1 = Column(DECIMAL(20, 8), nullable=False)
    take_profit_2 = Column(DECIMAL(20, 8))
    take_profit_3 = Column(DECIMAL(20, 8))

    # Risk-Reward
    risk_reward_ratio = Column(DECIMAL(10, 2), nullable=False)
    risk_percentage = Column(DECIMAL(5, 2), default=1.00)
    position_size_recommended = Column(DECIMAL(20, 8))

    # Confidence scores
    technical_confidence = Column(DECIMAL(5, 2))
    sentiment_confidence = Column(DECIMAL(5, 2))
    itc_confidence = Column(DECIMAL(5, 2))
    pattern_confidence = Column(DECIMAL(5, 2))
    ml_confidence = Column(DECIMAL(5, 2))
    final_confidence = Column(DECIMAL(5, 2), nullable=False)
    quality_score = Column(DECIMAL(5, 2))

    # Market context
    market_regime = Column(SQLEnum("BULL", "BEAR", "SIDEWAYS", "VOLATILE"))
    volatility_level = Column(SQLEnum("LOW", "MEDIUM", "HIGH", "EXTREME"))
    volume_profile = Column(SQLEnum("LOW", "NORMAL", "HIGH"))

    # Factors
    technical_factors = Column(JSON)
    sentiment_factors = Column(JSON)
    itc_factors = Column(JSON)
    pattern_factors = Column(JSON)

    # Reasoning
    reasoning = Column(Text)
    key_levels = Column(JSON)

    # Status
    status = Column(
        SQLEnum("PENDING", "ACTIVE", "COMPLETED", "CANCELLED", "EXPIRED"),
        default="PENDING",
    )
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime)

    # Human feedback
    human_executed = Column(Boolean, default=False)
    execution_note = Column(Text)

    # Indexes
    __table_args__ = (
        Index("idx_symbol_status", "symbol", "status"),
        Index("idx_confidence", "final_confidence"),
        Index("idx_rr_ratio", "risk_reward_ratio"),
    )

class SignalOutcome(Base):
    """Signal outcomes for learning."""

    __tablename__ = "signal_outcomes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    signal_id = Column(String(50), ForeignKey("signals.signal_id"), nullable=False)

    # Execution
    executed = Column(Boolean, default=False)
    entry_filled_price = Column(DECIMAL(20, 8))
    entry_filled_at = Column(DateTime)

    # Exit
    exit_price = Column(DECIMAL(20, 8))
    exit_type = Column(
        SQLEnum("TP1", "TP2", "TP3", "STOP_LOSS", "MANUAL", "TRAILING_STOP")
    )
    exit_at = Column(DateTime)

    # Performance
    profit_loss_amount = Column(DECIMAL(20, 8))
    profit_loss_percentage = Column(DECIMAL(10, 4))
    actual_rr_achieved = Column(DECIMAL(10, 2))
    holding_duration_minutes = Column(Integer)

    # Outcome
    outcome = Column(
        SQLEnum("BIG_WIN", "SMALL_WIN", "BREAKEVEN", "SMALL_LOSS", "BIG_LOSS")
    )
    met_target = Column(Boolean)

    # Learning
    what_went_right = Column(Text)
    what_went_wrong = Column(Text)
    lessons_learned = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_outcome", "outcome"),
        Index("idx_executed", "executed"),
    )

# ==================== NEWS & SENTIMENT ====================
class NewsSource(Base):
    """News sources with credibility tracking."""

    __tablename__ = "news_sources"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    source_name = Column(String(100), unique=True, nullable=False)
    source_type = Column(SQLEnum("NEWS_SITE", "TWITTER", "REDDIT", "TELEGRAM", "RSS"))
    
    # Credibility
    credibility_score = Column(DECIMAL(5, 2), default=50.00)
    accuracy_rate = Column(DECIMAL(5, 2))
    false_positive_rate = Column(DECIMAL(5, 2))

    # Performance
    total_articles = Column(Integer, default=0)
    correct_predictions = Column(Integer, default=0)

    # Status
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (Index("idx_credibility", "credibility_score"),)

class NewsArticle(Base):
    """News articles with sentiment analysis."""
    __tablename__ = 'news_articles'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    article_id = Column(String(100), unique=True, nullable=False)

    # Content
    title = Column(Text, nullable=False)
    content = Column(Text)
    summary = Column(Text)
    url = Column(String(500))

    # Source
    source_id = Column(Integer, ForeignKey('news_sources.id'), nullable=False)
    author = Column(String(200))

    # Crypto mentions
    mentioned_cryptos = Column(JSON)
    primary_symbol = Column(String(20), index=True)

    # Sentiment
    sentiment_score = Column(DECIMAL(5, 4))  # -1 to 1
    sentiment_label = Column(SQLEnum('VERY_BEARISH', 'BEARISH', 'NEUTRAL', 'BULLISH', 'VERY_BULLISH'))
    sentiment_confidence = Column(DECIMAL(5, 2))

    # Impact
    impact_score = Column(DECIMAL(5, 2))  # 0-100
    impact_level = Column(SQLEnum('NEGLIGIBLE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'))
    urgency = Column(SQLEnum('LOW', 'NORMAL', 'HIGH', 'IMMEDIATE'))

    # Classification
    category = Column(SQLEnum('REGULATION', 'ADOPTION', 'TECHNOLOGY', 'MARKET', 'SECURITY', 'OTHER'))
    keywords = Column(JSON)
    entities = Column(JSON)

    # Timestamps
    published_at = Column(DateTime, index=True)
    collected_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_symbol_impact', 'primary_symbol', 'impact_score'),
        Index('idx_sentiment', 'sentiment_label'),
    )
    
# ==================== BOT PERFORMANCE ====================
class BotPerformance(Base):
    """Bot performance metrics."""
    __tablename__ = 'bot_performance'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bot_name = Column(String(50), nullable=False)
    date = Column(DateTime, nullable=False)

    # Signal metrics
    signals_generated = Column(Integer, default=0)
    signals_executed = Column(Integer, default=0)

    # Accuracy
    correct_signals = Column(Integer, default=0)
    incorrect_signals = Column(Integer, default=0)
    accuracy_rate = Column(DECIMAL(5, 2))

    # Confidence
    avg_confidence = Column(DECIMAL(5, 2))
    confidence_calibration = Column(DECIMAL(5, 2))

    # Financial
    total_profit_loss = Column(DECIMAL(20, 8))
    profit_factor = Column(DECIMAL(10, 4))
    win_rate = Column(DECIMAL(5, 2))
    avg_win = Column(DECIMAL(20, 8))
    avg_loss = Column(DECIMAL(20, 8))

    # Risk
    max_drawdown = Column(DECIMAL(5, 2))
    sharpe_ratio = Column(DECIMAL(10, 4))
    sortino_ratio = Column(DECIMAL(10, 4))

    # Execution
    avg_signal_generation_time_ms = Column(Integer)
    avg_response_time_ms = Column(Integer)
    uptime_percentage = Column(DECIMAL(5, 2))
    errors_count = Column(Integer, default=0)

    __table_args__ = (
        Index('idx_bot_date', 'bot_name', 'date'),
    )
    
class BotHealth(Base):
    """Bot health monitoring."""
    __tablename__ = 'bot_health'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bot_name = Column(String(50), nullable=False, index=True)

    # Status
    status = Column(SQLEnum('RUNNING', 'STOPPED', 'ERROR', 'DEGRADED', 'STARTING', 'STOPPING'))
    is_healthy = Column(Boolean, default=True)

    # Metrics
    cpu_usage = Column(DECIMAL(5, 2))
    memory_usage_mb = Column(Integer)
    disk_usage_mb = Column(Integer)

    # Performance
    requests_per_minute = Column(Integer)
    avg_response_time_ms = Column(Integer)
    error_rate = Column(DECIMAL(5, 2))

    # Activity
    last_heartbeat = Column(DateTime)
    last_successful_operation = Column(DateTime)
    last_error_at = Column(DateTime)
    last_error_message = Column(Text)

    # Uptime
    uptime_seconds = Column(BigInteger)
    restart_count = Column(Integer, default=0)

    checked_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_bot_status', 'bot_name', 'status'),
    )
    
# ==================== ML MODELS ====================
class MLModel(Base):
    """Machine learning models registry."""
    __tablename__ = 'ml_models'
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(100), nullable=False)
    version = Column(String(20), nullable=False)
    model_type = Column(SQLEnum('LSTM', 'TRANSFORMER', 'CNN', 'RF', 'XGBoost', 'RL', 'ENSEMBLE'))

    # Purpose
    purpose = Column(SQLEnum('PRICE_PREDICTION', 'PATTERN_RECOGNITION', 'SENTIMENT', 'SIGNAL_OPTIMIZATION'))

    # Performance metrics
    accuracy = Column(DECIMAL(5, 2))
    precision_score = Column(DECIMAL(5, 2))
    recall = Column(DECIMAL(5, 2))
    f1_score = Column(DECIMAL(5, 2))

    # Trading performance
    win_rate = Column(DECIMAL(5, 2))
    profit_factor = Column(DECIMAL(10, 4))
    sharpe_ratio = Column(DECIMAL(10, 4))
    max_drawdown = Column(DECIMAL(5, 2))

    # Deployment
    is_active = Column(Boolean, default=False)
    traffic_percentage = Column(Integer, default=0)
    deployment_stage = Column(SQLEnum('DEVELOPMENT', 'TESTING', 'STAGING', 'PRODUCTION'))

    # Training
    training_dataset_size = Column(Integer)
    training_duration_minutes = Column(Integer)
    hyperparameters = Column(JSON)
    feature_importance = Column(JSON)

    # Timestamps
    trained_at = Column(DateTime)
    deployed_at = Column(DateTime)
    last_prediction_at = Column(DateTime)

    # Storage
    model_path = Column(String(500))
    model_checksum = Column(String(64))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_model_version', 'model_name', 'version', unique=True),
        Index('idx_active', 'is_active'),
    )
    
# ==================== USER FEEDBACK ====================
class UserTradeResult(Base):
    """User trade results for learning."""
    tablename = 'user_trade_results'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    signal_id = Column(String(50), ForeignKey('signals.signal_id'), nullable=False)
    user_id = Column(Integer)

    # Trade details
    entry_price = Column(DECIMAL(20, 8), nullable=False)
    exit_price = Column(DECIMAL(20, 8), nullable=False)
    position_size = Column(DECIMAL(20, 8))

    # Outcome
    profit_loss = Column(DECIMAL(20, 8))
    profit_loss_percentage = Column(DECIMAL(10, 4))
    trade_result = Column(SQLEnum('WIN', 'LOSS', 'BREAKEVEN'))

    # User notes
    user_notes = Column(Text)
    trade_rating = Column(Integer)  # 1-5 stars
    would_take_again = Column(Boolean)

    # Deviations
    deviated_from_signal = Column(Boolean, default=False)
    deviation_notes = Column(Text)

    submitted_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_signal', 'signal_id'),
        Index('idx_result', 'trade_result'),
    )
# ==================== MARKET CONTEXT ====================
class MarketRegime(Base):
    """Market regime detection."""
    __tablename__ = 'market_regimes'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(SQLEnum('1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w'))

    # Regime
    regime = Column(SQLEnum('BULL', 'BEAR', 'SIDEWAYS', 'VOLATILE', 'ACCUMULATION', 'DISTRIBUTION'))
    confidence = Column(DECIMAL(5, 2))

    # Indicators
    trend_direction = Column(SQLEnum('UP', 'DOWN', 'NEUTRAL'))
    trend_strength = Column(DECIMAL(5, 2))
    volatility = Column(DECIMAL(10, 4))
    volume_trend = Column(SQLEnum('INCREASING', 'DECREASING', 'STABLE'))

    # Price structure
    higher_highs = Column(Boolean)
    higher_lows = Column(Boolean)
    lower_highs = Column(Boolean)
    lower_lows = Column(Boolean)

    # Context
    indicators = Column(JSON)

    # Validity
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime)
    is_current = Column(Boolean, default=True)

    __table_args__ = (
        Index('idx_symbol_current', 'symbol', 'is_current'),
        Index('idx_regime', 'regime'),
    )

# ==================== HELPER FUNCTIONS ====================
def create_all_tables(engine):
    """
    Create all tables in database.
    Args:
        engine: SQLAlchemy engine
    """
    Base.metadata.create_all(engine)

def drop_all_tables(engine):
    """
    Drop all tables from database.
    Args:
        engine: SQLAlchemy engine
    """
    Base.metadata.drop_all(engine)
    
def get_table_names():
    """
    Get list of all table names.
    Returns:
        List of table names
    """
    return [table.name for table in Base.metadata.sorted_tables]
