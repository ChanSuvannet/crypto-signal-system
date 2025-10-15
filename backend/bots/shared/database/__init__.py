
# ============================================
# Crypto Trading Signal System
# backed/bots/shared/database/__init__.py
# Deception: Database clients and models for all bots.
# ============================================
from .mysql_client import MySQLClient
from .timescale_client import TimescaleClient
from .redis_client import RedisClient
from .mongodb_client import MongoDBClient
from .models import (
    Base,
    Signal,
    SignalOutcome,
    NewsSource,
    NewsArticle,
    BotPerformance,
    BotHealth,
    SystemEvent,
    MLModel,
    UserTradeResult,
    MarketRegime,
    create_all_tables,
    drop_all_tables,
    get_table_names,
)

__all__ = [
    # Clients
    'MySQLClient',
    'TimescaleClient',
    'RedisClient',
    'MongoDBClient',
    
    # Models
    'Base',
    'Signal',
    'SignalOutcome',
    'NewsSource',
    'NewsArticle',
    'BotPerformance',
    'BotHealth',
    'SystemEvent',
    'MLModel',
    'UserTradeResult',
    'MarketRegime',
    
    # Helper functions
    'create_all_tables',
    'drop_all_tables',
    'get_table_names',
]
