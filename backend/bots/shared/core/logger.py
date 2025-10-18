"""
Logging Setup
=============
Centralized logging configuration for all bots.
"""

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Optional


# ANSI color codes for console output
class LogColors:
    """ANSI color codes for terminal output."""

    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright colors
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""

    # Color mapping for log levels
    COLORS = {
        "DEBUG": LogColors.CYAN,
        "INFO": LogColors.GREEN,
        "WARNING": LogColors.YELLOW,
        "ERROR": LogColors.RED,
        "CRITICAL": LogColors.BRIGHT_RED + LogColors.BOLD,
    }

    def __init__(self, fmt: str, use_colors: bool = True):
        """
        Initialize colored formatter.

        Args:
            fmt: Log format string
            use_colors: Whether to use colors
        """
        super().__init__(fmt)
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with colors.

        Args:
            record: Log record to format

        Returns:
            Formatted log string
        """
        if self.use_colors and record.levelname in self.COLORS:
            # Color the level name
            record.levelname = (
                f"{self.COLORS[record.levelname]}"
                f"{record.levelname}{LogColors.RESET}"
            )

        return super().format(record)


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: str = "INFO",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    console: bool = True,
    use_colors: bool = True,
) -> logging.Logger:
    """
    Setup and configure a logger.

    Args:
        name: Logger name
        log_file: Optional path to log file
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        console: Whether to log to console
        use_colors: Whether to use colors in console output

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)

        console_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        console_formatter = ColoredFormatter(
            console_format, use_colors=use_colors and sys.stdout.isatty()
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # File handler
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Rotating file handler
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)

        file_format = (
            "%(asctime)s | %(levelname)-8s | %(name)s | "
            "%(filename)s:%(lineno)d | %(funcName)s() | %(message)s"
        )
        file_formatter = logging.Formatter(file_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def setup_daily_logger(
    name: str,
    log_dir: str = "logs",
    level: str = "INFO",
    backup_count: int = 30,
    console: bool = True,
) -> logging.Logger:
    """
    Setup logger with daily rotation.

    Args:
        name: Logger name
        log_dir: Directory for log files
        level: Logging level
        backup_count: Number of days to keep logs
        console: Whether to log to console

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    logger.handlers.clear()

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)

        console_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        console_formatter = ColoredFormatter(console_format)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # Daily rotating file handler
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    log_file = log_path / f"{name}.log"

    file_handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.suffix = "%Y-%m-%d"

    file_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s | "
        "%(filename)s:%(lineno)d | %(message)s"
    )
    file_formatter = logging.Formatter(file_format)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get existing logger or create basic one.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        # Setup basic logger if not configured
        logger = setup_logger(name)

    return logger


# Example usage functions
def log_trade_signal(logger: logging.Logger, signal: dict):
    """
    Log a trading signal with formatted output.

    Args:
        logger: Logger instance
        signal: Signal dictionary
    """
    logger.info(
        f"""
╔════════════════════════════════════════════╗
║           TRADING SIGNAL                   ║
╚════════════════════════════════════════════╝
  Symbol:          {signal.get('symbol')}
  Type:            {signal.get('signal_type')}
  Entry:           ${signal.get('entry_price')}
  Stop Loss:       ${signal.get('stop_loss')}
  Take Profit:     ${signal.get('take_profit')}
  Risk/Reward:     1:{signal.get('risk_reward_ratio')}
  Confidence:      {signal.get('confidence')}%
  Reasoning:       {signal.get('reasoning', 'N/A')}
════════════════════════════════════════════
"""
    )
