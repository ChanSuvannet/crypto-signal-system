# ============================================
# Crypto Trading Signal System
# backed/bots/shared/database/models.py
# Deception: Database models for MySQL/TimescaleDB.
# ============================================
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, Boolean,
    Enum as SQLEnum, JSON, DECIMAL, BigInteger, Index, ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Base class for all models
Base = declarative_base()


# ==================== SIGNALS & TRADING ====================

class Signal(Base):
    """Trading signals table."""
    __tablename__ = 'signals'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    signal_id = Column(String(50), unique=True, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(SQLEnum('1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w'), nullable=False)
    signal_type = Column(SQLEnum('BUY', 'SELL'), nullable=False)
    
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
    market_regime = Column(SQLEnum('BULL', 'BEAR', 'SIDEWAYS', 'VOLATILE'))
    volatility_level = Column(SQLEnum('LOW', 'MEDIUM', 'HIGH', 'EXTREME'))
    volume_profile = Column(SQLEnum('LOW', 'NORMAL', 'HIGH'))
    
    # Factors
    technical_factors = Column(JSON)
    sentiment_factors = Column(JSON)
    itc_factors = Column(JSON)
    pattern_factors = Column(JSON)
    
    # Reasoning
    reasoning = Column(Text)
    key_levels = Column(JSON)
    
    # Status
    status = Column(SQLEnum('PENDING', 'ACTIVE', 'COMPLETED', 'CANCELLED', 'EXPIRED'), default='PENDING')
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime)
    
    # Human feedback
    human_executed = Column(Boolean, default=False)
    execution_note = Column(Text)
    
    # Indexes
    __table_args__ = (
        Index('idx_symbol_status', 'symbol', 'status'),
        Index('idx_confidence', 'final_confidence'),
        Index('idx_rr_ratio', 'risk_reward_ratio'),
    )


class SignalOutcome(Base):
    """Signal outcomes for learning."""
    __tablename__ = 'signal_outcomes'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    signal_id = Column(String(50), ForeignKey('signals.signal_id'), nullable=False)
    
    # Execution
    executed = Column(Boolean, default=False)
    entry_filled_price = Column(DECIMAL(20, 8))
    entry_filled_at = Column(DateTime)
    
    # Exit
    exit_price = Column(DECIMAL(20, 8))
    exit_type = Column(SQLEnum('TP1', 'TP2', 'TP3', 'STOP_LOSS', 'MANUAL', 'TRAILING_STOP'))
    exit_at = Column(DateTime)
    
    # Performance
    profit_loss_amount = Column(DECIMAL(20, 8))
    profit_loss_percentage = Column(DECIMAL(10, 4))
    actual_rr_achieved = Column(DECIMAL(10, 2))
    holding_duration_minutes = Column(Integer)
    
    # Outcome
    outcome = Column(SQLEnum('BIG_WIN', 'SMALL_WIN', 'BREAKEVEN', 'SMALL_LOSS', 'BIG_LOSS'))
    met_target = Column(Boolean)
    
    # Learning
    what_went_right = Column(Text)
    what_went_wrong = Column(Text)
    lessons_learned = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_outcome', 'outcome'),
        Index('idx_executed', 'executed'),
    )


# ==================== NEWS & SENTIMENT ====================

class NewsSource(Base):
    """News sources with credibility tracking."""
    __tablename__ = 'news_sources'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)