
# ============================================
# Crypto Trading Signal System
# backed/bots/shared/utils/helpers.py
# Deception: Helper Functions = Miscellaneous utility functions.
# ============================================


import hashlib
import uuid
import time
from typing import Any, List, Dict, Optional, Callable
from datetime import datetime, timedelta
from functools import wraps
import asyncio

from datetime import timezone
from ..core.logger import get_logger

logger = get_logger('helpers')


# ==================== ID GENERATION ====================

def generate_signal_id(symbol: str, timestamp: Optional[datetime] = None) -> str:
    """
    Generate unique signal ID.
    
    Args:
        symbol: Trading symbol
        timestamp: Optional timestamp (uses current if None)
        
    Returns:
        Unique signal ID
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    timestamp_str = timestamp.strftime("%Y%m%d%H%M%S")
    random_suffix = uuid.uuid4().hex[:6]

    return f"SIG_{symbol}_{timestamp_str}_{random_suffix}"


def generate_unique_id(prefix: str = "") -> str:
    """
    Generate unique ID.
    
    Args:
        prefix: Optional prefix
        
    Returns:
        Unique ID
    """
    unique_id = uuid.uuid4().hex[:12]

    return f"{prefix}_{unique_id}" if prefix else unique_id


def generate_checksum(data: str) -> str:
    """
    Generate checksum for data.
    
    Args:
        data: Data string
        
    Returns:
        SHA256 checksum
    """
    return hashlib.sha256(data.encode()).hexdigest()


# ==================== TIME HELPERS ====================

def get_timestamp() -> int:
    """
    Get current Unix timestamp in milliseconds.
    
    Returns:
        Timestamp in milliseconds
    """
    return int(time.time() * 1000)


def timestamp_to_datetime(timestamp: int) -> datetime:
    """
    Convert Unix timestamp to datetime.
    
    Args:
        timestamp: Unix timestamp (milliseconds)
        
    Returns:
        Datetime object
    """
    return datetime.utcfromtimestamp(timestamp / 1000)


def datetime_to_timestamp(dt: datetime) -> int:
    """
    Convert datetime to Unix timestamp.
    
    Args:
        dt: Datetime object
        
    Returns:
        Unix timestamp in milliseconds
    """
    return int(dt.timestamp() * 1000)


def get_timeframe_seconds(timeframe: str) -> int:
    """
    Convert timeframe to seconds.
    
    Args:
        timeframe: Timeframe string (1m, 5m, 1h, etc.)
        
    Returns:
        Seconds
    """
    timeframe_map = {
        '1m': 60,
        '3m': 180,
        '5m': 300,
        '15m': 900,
        '30m': 1800,
        '1h': 3600,
        '2h': 7200,
        '4h': 14400,
        '6h': 21600,
        '8h': 28800,
        '12h': 43200,
        '1d': 86400,
        '3d': 259200,
        '1w': 604800,
    }
    
    return timeframe_map.get(timeframe, 3600)


def align_to_timeframe(timestamp: datetime, timeframe: str) -> datetime:
    """
    Align timestamp to timeframe boundary.
    
    Args:
        timestamp: Timestamp to align
        timeframe: Timeframe
        
    Returns:
        Aligned timestamp
    """
    seconds = get_timeframe_seconds(timeframe)
    unix_timestamp = int(timestamp.timestamp())
    aligned_timestamp = (unix_timestamp // seconds) * seconds
    
    return datetime.utcfromtimestamp(aligned_timestamp)


# ==================== DATA HELPERS ====================

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers.
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if division fails
        
    Returns:
        Result or default
    """
    try:
        return default if denominator == 0 else numerator / denominator
    except (ZeroDivisionError, TypeError):
        return default


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """
    Calculate percentage change.
    
    Args:
        old_value: Old value
        new_value: New value
        
    Returns:
        Percentage change
    """
    return 0.0 if old_value == 0 else ((new_value - old_value) / old_value) * 100


def round_to_precision(value: float, precision: int) -> float:
    """
    Round value to specific precision.
    
    Args:
        value: Value to round
        precision: Number of decimal places
        
    Returns:
        Rounded value
    """
    return round(value, precision)


def clamp(value: float, min_value: float, max_value: float) -> float:
    """
    Clamp value between min and max.
    
    Args:
        value: Value to clamp
        min_value: Minimum value
        max_value: Maximum value
        
    Returns:
        Clamped value
    """
    return max(min_value, min(value, max_value))


def normalize_symbol(symbol: str) -> str:
    """
    Normalize trading symbol format.
    
    Args:
        symbol: Trading symbol
        
    Returns:
        Normalized symbol (e.g., BTCUSDT)
    """
    # Remove separators
    symbol = symbol.replace('/', '').replace('-', '').replace('_', '')
    
    # Convert to uppercase
    symbol = symbol.upper()
    
    return symbol


def chunk_list(lst: list, chunk_size: int) -> List[list]:
    """
    Split list into chunks.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def merge_dicts(*dicts: dict) -> dict:
    """
    Merge multiple dictionaries.
    
    Args:
        *dicts: Dictionaries to merge
        
    Returns:
        Merged dictionary
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result


def flatten_dict(d: dict, parent_key: str = '', sep: str = '_') -> dict:
    """
    Flatten nested dictionary.
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key prefix
        sep: Separator
        
    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


# ==================== DECORATORS ====================

def timing_decorator(func: Callable) -> Callable:
    """
    Decorator to measure function execution time.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        elapsed = time.time() - start_time
        logger.debug(f"{func.__name__} took {elapsed:.2f}s")
        return result
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        logger.debug(f"{func.__name__} took {elapsed:.2f}s")
        return result
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def cache_result(ttl_seconds: int = 300):
    """
    Decorator to cache function results.
    
    Args:
        ttl_seconds: Cache TTL in seconds
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        cache_time = {}
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_key = str(args) + str(kwargs)
            current_time = time.time()
            
            # Check if cached and not expired
            if cache_key in cache:
                if current_time - cache_time[cache_key] < ttl_seconds:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cache[cache_key]
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            cache[cache_key] = result
            cache_time[cache_key] = current_time
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_key = str(args) + str(kwargs)
            current_time = time.time()
            
            # Check if cached and not expired
            if cache_key in cache:
                if current_time - cache_time[cache_key] < ttl_seconds:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cache[cache_key]
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache[cache_key] = result
            cache_time[cache_key] = current_time
            
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# ==================== ASYNC HELPERS ====================

async def run_with_timeout(coro, timeout: float):
    """
    Run coroutine with timeout.
    
    Args:
        coro: Coroutine to run
        timeout: Timeout in seconds
        
    Returns:
        Result or raises TimeoutError
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.error(f"Operation timed out after {timeout}s")
        raise


async def run_parallel(*coros, max_concurrency: int = 10):
    """
    Run coroutines in parallel with concurrency limit.
    
    Args:
        *coros: Coroutines to run
        max_concurrency: Maximum concurrent tasks
        
    Returns:
        List of results
    """
    semaphore = asyncio.Semaphore(max_concurrency)
    
    async def run_with_semaphore(coro):
        async with semaphore:
            return await coro
    
    tasks = [run_with_semaphore(coro) for coro in coros]
    return await asyncio.gather(*tasks)


# ==================== RATE LIMITING ====================

class RateLimiter:
    """Simple rate limiter."""
    
    def __init__(self, max_calls: int, period_seconds: float):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum calls allowed
            period_seconds: Time period in seconds
        """
        self.max_calls = max_calls
        self.period_seconds = period_seconds
        self.calls = []
    
    async def acquire(self):
        """Wait if rate limit exceeded."""
        now = time.time()
        
        # Remove old calls
        self.calls = [call_time for call_time in self.calls 
                     if now - call_time < self.period_seconds]
        
        # Wait if limit exceeded
        if len(self.calls) >= self.max_calls:
            sleep_time = self.period_seconds - (now - self.calls[0])
            if sleep_time > 0:
                logger.debug(f"Rate limit reached, sleeping for {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
                self.calls = []
        
        # Record this call
        self.calls.append(time.time())


# ==================== COMPARISON HELPERS ====================

def is_price_near(price1: float, price2: float, tolerance_pct: float = 0.1) -> bool:
    """
    Check if two prices are near each other.
    
    Args:
        price1: First price
        price2: Second price
        tolerance_pct: Tolerance percentage
        
    Returns:
        True if prices are within tolerance
    """
    diff_pct = abs((price1 - price2) / price1) * 100
    return diff_pct <= tolerance_pct


def get_price_direction(old_price: float, new_price: float) -> str:
    """
    Get price direction.
    
    Args:
        old_price: Old price
        new_price: New price
        
    Returns:
        'UP', 'DOWN', or 'NEUTRAL'
    """
    change_pct = calculate_percentage_change(old_price, new_price)
    
    if change_pct > 0.01:
        return 'UP'
    elif change_pct < -0.01:
        return 'DOWN'
    else:
        return 'NEUTRAL'

