# ============================================
# Crypto Trading Signal System
# backed/bots/shared/core/config.py
# Deception: Centralized configuration management for all bots.
# ============================================

import os
from typing import Any, Optional, Dict
from pathlib import Path
from dotenv import load_dotenv
import yaml


class Config:
    """
    Configuration manager for bot settings.

    Loads configuration from:
    1. Environment variables (.env file)
    2. YAML configuration files
    3. Default values
    """

    # Default configuration values
    DEFAULTS = {
        # General
        "NODE_ENV": "development",
        "LOG_LEVEL": "INFO",
        "DEBUG": False,
        # Database
        "MYSQL_HOST": "localhost",
        "MYSQL_PORT": 3306,
        "MYSQL_DATABASE": "crypto_trading_bot",
        "MYSQL_USER": "crypto_user",
        "MYSQL_PASSWORD": "",
        "TIMESCALE_HOST": "localhost",
        "TIMESCALE_PORT": 5432,
        "TIMESCALE_DATABASE": "crypto_timeseries",
        "TIMESCALE_USER": "timescale_user",
        "TIMESCALE_PASSWORD": "",
        "MONGO_HOST": "localhost",
        "MONGO_PORT": 27017,
        "MONGO_DATABASE": "crypto_ml_models",
        "MONGO_USER": "mongo_user",
        "MONGO_PASSWORD": "",
        # Redis
        "REDIS_HOST": "localhost",
        "REDIS_PORT": 6379,
        "REDIS_PASSWORD": "",
        "REDIS_DB": 0,
        # RabbitMQ
        "RABBITMQ_HOST": "localhost",
        "RABBITMQ_PORT": 5672,
        "RABBITMQ_USER": "rabbitmq_user",
        "RABBITMQ_PASSWORD": "",
        "RABBITMQ_VHOST": "/",
        # Bot Settings
        "MAX_CONSECUTIVE_ERRORS": 5,
        "HEARTBEAT_INTERVAL": 60,
        "RECONNECT_DELAY": 5,
        "RECONNECT_MAX_ATTEMPTS": 10,
        # API Keys
        "BINANCE_API_KEY": "",
        "BINANCE_API_SECRET": "",
        "BINANCE_TESTNET": False,
        "NEWSAPI_KEY": "",
        "CRYPTOPANIC_API_KEY": "",
        # Signal Settings
        "MIN_RR_RATIO": 4.0,
        "MIN_CONFIDENCE": 60,
        "MIN_WIN_RATE": 60,
        "DEFAULT_RISK_PERCENTAGE": 1.0,
        # Performance
        "DB_POOL_MIN": 2,
        "DB_POOL_MAX": 10,
        "CACHE_TTL": 300,
        "WORKER_THREADS": 4,
    }

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            config_file: Optional path to YAML config file
        """
        self._config: Dict[str, Any] = {}
        self._load_environment()

        if config_file:
            self._load_yaml_config(config_file)

    def _load_environment(self):
        """Load environment variables from .env file."""
        # Find .env file
        env_path = self._find_env_file()

        if env_path:
            load_dotenv(env_path)

        # Load all environment variables
        for key, default_value in self.DEFAULTS.items():
            env_value = os.getenv(key)

            if env_value is not None:
                # Convert to appropriate type
                self._config[key] = self._convert_type(env_value, type(default_value))
            else:
                self._config[key] = default_value

    def _find_env_file(self) -> Optional[Path]:
        """
        Find .env file by searching up directory tree.

        Returns:
            Path to .env file or None
        """
        current_dir = Path.cwd()

        # Search up to 5 levels
        for _ in range(5):
            env_file = current_dir / ".env"
            if env_file.exists():
                return env_file

            parent = current_dir.parent
            if parent == current_dir:
                break
            current_dir = parent

        return None

    def _load_yaml_config(self, config_file: str):
        """
        Load configuration from YAML file.

        Args:
            config_file: Path to YAML config file
        """
        try:
            with open(config_file, "r") as f:
                yaml_config = yaml.safe_load(f)
                self._config.update(yaml_config)
        except FileNotFoundError:
            print(f"Warning: Config file not found: {config_file}")
        except yaml.YAMLError as e:
            print(f"Error parsing YAML config: {e}")

    def _convert_type(self, value: str, target_type: type) -> Any:
        """
        Convert string value to target type.

        Args:
            value: String value to convert
            target_type: Target Python type

        Returns:
            Converted value
        """
        if target_type == bool:
            return value.lower() in ("true", "1", "yes", "on")
        elif target_type == int:
            return int(value)
        elif target_type == float:
            return float(value)
        else:
            return value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        """
        Set configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config[key] = value

    def get_database_url(self, db_type: str = "mysql") -> str:
        """
        Get database connection URL.

        Args:
            db_type: Database type ('mysql', 'postgresql', 'mongodb')

        Returns:
            Database connection URL
        """
        if db_type == "mysql":
            return (
                f"mysql+aiomysql://{self.get('MYSQL_USER')}:{self.get('MYSQL_PASSWORD')}"
                f"@{self.get('MYSQL_HOST')}:{self.get('MYSQL_PORT')}"
                f"/{self.get('MYSQL_DATABASE')}"
            )
        elif db_type == "postgresql" or db_type == "timescale":
            return (
                f"postgresql+asyncpg://{self.get('TIMESCALE_USER')}:{self.get('TIMESCALE_PASSWORD')}"
                f"@{self.get('TIMESCALE_HOST')}:{self.get('TIMESCALE_PORT')}"
                f"/{self.get('TIMESCALE_DATABASE')}"
            )
        elif db_type == "mongodb":
            return (
                f"mongodb://{self.get('MONGO_USER')}:{self.get('MONGO_PASSWORD')}"
                f"@{self.get('MONGO_HOST')}:{self.get('MONGO_PORT')}"
                f"/{self.get('MONGO_DATABASE')}"
            )
        else:
            raise ValueError(f"Unknown database type: {db_type}")

    def get_redis_url(self) -> str:
        """
        Get Redis connection URL.

        Returns:
            Redis connection URL
        """
        password = self.get("REDIS_PASSWORD")
        auth = f":{password}@" if password else ""

        return (
            f"redis://{auth}{self.get('REDIS_HOST')}:"
            f"{self.get('REDIS_PORT')}/{self.get('REDIS_DB')}"
        )

    def get_rabbitmq_url(self) -> str:
        """
        Get RabbitMQ connection URL.

        Returns:
            RabbitMQ connection URL
        """
        return (
            f"amqp://{self.get('RABBITMQ_USER')}:{self.get('RABBITMQ_PASSWORD')}"
            f"@{self.get('RABBITMQ_HOST')}:{self.get('RABBITMQ_PORT')}"
            f"/{self.get('RABBITMQ_VHOST')}"
        )

    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.get("NODE_ENV") == "development"

    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.get("NODE_ENV") == "production"

    def is_debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self.get("DEBUG", False)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Configuration dictionary (with sensitive data masked)
        """
        config_copy = self._config.copy()

        # Mask sensitive keys
        sensitive_keys = [
            "MYSQL_PASSWORD",
            "TIMESCALE_PASSWORD",
            "MONGO_PASSWORD",
            "REDIS_PASSWORD",
            "RABBITMQ_PASSWORD",
            "BINANCE_API_SECRET",
            "NEWSAPI_KEY",
            "CRYPTOPANIC_API_KEY",
        ]

        for key in sensitive_keys:
            if key in config_copy and config_copy[key]:
                config_copy[key] = "***MASKED***"

        return config_copy

    def __repr__(self) -> str:
        """String representation."""
        return f"<Config(env={self.get('NODE_ENV')}, debug={self.is_debug()})>"
