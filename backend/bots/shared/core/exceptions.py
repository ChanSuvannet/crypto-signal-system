
# ============================================
# Crypto Trading Signal System
# backed/bots/shared/core/exceptions.py
# Deception: Custom exception classes for bot error handling.
# ============================================
class BotError(Exception):
    """Base exception for all bot-related errors."""
    
    def __init__(self, message: str, code: str = None, details: dict = None):
        """
        Initialize bot error.
        
        Args:
            message: Error message
            code: Optional error code
            details: Optional additional details
        """
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        """String representation of error."""
        return f"[{self.code}] {self.message}" if self.code else self.message
    
    def to_dict(self) -> dict:
        """
        Convert error to dictionary.
        
        Returns:
            Dictionary representation of error
        """
        return {
            'error': self.__class__.__name__,
            'message': self.message,
            'code': self.code,
            'details': self.details
        }


class BotConfigError(BotError):
    """Error in bot configuration."""
    
    def __init__(self, message: str, config_key: str = None):
        """
        Initialize configuration error.
        
        Args:
            message: Error message
            config_key: Configuration key that caused the error
        """
        details = {'config_key': config_key} if config_key else {}
        super().__init__(message, code='CONFIG_ERROR', details=details)


class BotConnectionError(BotError):
    """Error connecting to external services."""
    
    def __init__(self, message: str, service: str = None, retry_after: int = None):
        """
        Initialize connection error.
        
        Args:
            message: Error message
            service: Name of service that failed
            retry_after: Seconds to wait before retry
        """
        details = {}
        if service:
            details['service'] = service
        if retry_after:
            details['retry_after'] = retry_after
        
        super().__init__(message, code='CONNECTION_ERROR', details=details)


class BotDatabaseError(BotError):
    """Database operation error."""
    
    def __init__(self, message: str, query: str = None, table: str = None):
        """
        Initialize database error.
        
        Args:
            message: Error message
            query: SQL query that failed
            table: Database table involved
        """
        details = {}
        if query:
            details['query'] = query
        if table:
            details['table'] = table
        
        super().__init__(message, code='DATABASE_ERROR', details=details)


class BotValidationError(BotError):
    """Data validation error."""
    
    def __init__(self, message: str, field: str = None, value: any = None):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field: Field name that failed validation
            value: Invalid value
        """
        details = {}
        if field:
            details['field'] = field
        if value is not None:
            details['value'] = str(value)
        
        super().__init__(message, code='VALIDATION_ERROR', details=details)


class BotAPIError(BotError):
    """External API error."""
    
    def __init__(
        self,
        message: str,
        api: str = None,
        status_code: int = None,
        response: str = None
    ):
        """
        Initialize API error.
        
        Args:
            message: Error message
            api: API name
            status_code: HTTP status code
            response: API response
        """
        details = {}
        if api:
            details['api'] = api
        if status_code:
            details['status_code'] = status_code
        if response:
            details['response'] = response
        
        super().__init__(message, code='API_ERROR', details=details)


class BotRateLimitError(BotAPIError):
    """API rate limit exceeded."""
    
    def __init__(self, message: str, api: str = None, retry_after: int = None):
        """
        Initialize rate limit error.
        
        Args:
            message: Error message
            api: API name
            retry_after: Seconds to wait before retry
        """
        super().__init__(message, api=api, status_code=429)
        self.code = 'RATE_LIMIT_ERROR'
        if retry_after:
            self.details['retry_after'] = retry_after


class BotDataError(BotError):
    """Data processing error."""
    
    def __init__(self, message: str, data_type: str = None, reason: str = None):
        """
        Initialize data error.
        
        Args:
            message: Error message
            data_type: Type of data that caused error
            reason: Reason for the error
        """
        details = {}
        if data_type:
            details['data_type'] = data_type
        if reason:
            details['reason'] = reason
        
        super().__init__(message, code='DATA_ERROR', details=details)


class BotTimeoutError(BotError):
    """Operation timeout error."""
    
    def __init__(self, message: str, operation: str = None, timeout: float = None):
        """
        Initialize timeout error.
        
        Args:
            message: Error message
            operation: Operation that timed out
            timeout: Timeout duration in seconds
        """
        details = {}
        if operation:
            details['operation'] = operation
        if timeout:
            details['timeout'] = timeout
        
        super().__init__(message, code='TIMEOUT_ERROR', details=details)


class BotAuthenticationError(BotError):
    """Authentication/authorization error."""
    
    def __init__(self, message: str, service: str = None, credential: str = None):
        """
        Initialize authentication error.
        
        Args:
            message: Error message
            service: Service that failed authentication
            credential: Type of credential used
        """
        details = {}
        if service:
            details['service'] = service
        if credential:
            details['credential'] = credential
        
        super().__init__(message, code='AUTH_ERROR', details=details)


class BotSignalError(BotError):
    """Trading signal generation error."""
    
    def __init__(
        self,
        message: str,
        symbol: str = None,
        reason: str = None,
        signal_data: dict = None
    ):
        """
        Initialize signal error.
        
        Args:
            message: Error message
            symbol: Trading symbol
            reason: Reason for signal failure
            signal_data: Signal data that caused error
        """
        details = {}
        if symbol:
            details['symbol'] = symbol
        if reason:
            details['reason'] = reason
        if signal_data:
            details['signal_data'] = signal_data
        
        super().__init__(message, code='SIGNAL_ERROR', details=details)


class BotIndicatorError(BotError):
    """Technical indicator calculation error."""
    
    def __init__(
        self,
        message: str,
        indicator: str = None,
        symbol: str = None,
        reason: str = None
    ):
        """
        Initialize indicator error.
        
        Args:
            message: Error message
            indicator: Indicator name
            symbol: Trading symbol
            reason: Reason for calculation failure
        """
        details = {}
        if indicator:
            details['indicator'] = indicator
        if symbol:
            details['symbol'] = symbol
        if reason:
            details['reason'] = reason
        
        super().__init__(message, code='INDICATOR_ERROR', details=details)


class BotModelError(BotError):
    """Machine learning model error."""
    
    def __init__(
        self,
        message: str,
        model_name: str = None,
        model_type: str = None,
        reason: str = None
    ):
        """
        Initialize model error.
        
        Args:
            message: Error message
            model_name: Name of the model
            model_type: Type of model (LSTM, etc.)
            reason: Reason for model failure
        """
        details = {}
        if model_name:
            details['model_name'] = model_name
        if model_type:
            details['model_type'] = model_type
        if reason:
            details['reason'] = reason
        
        super().__init__(message, code='MODEL_ERROR', details=details)


class BotShutdownError(BotError):
    """Error during bot shutdown."""
    
    def __init__(self, message: str, component: str = None):
        """
        Initialize shutdown error.
        
        Args:
            message: Error message
            component: Component that failed to shutdown
        """
        details = {}
        if component:
            details['component'] = component
        
        super().__init__(message, code='SHUTDOWN_ERROR', details=details)


# Exception handler decorator
def handle_bot_errors(logger=None):
    """
    Decorator to handle bot errors gracefully.
    
    Args:
        logger: Logger instance for error logging
        
    Usage:
        @handle_bot_errors(logger)
        async def my_function():
            ...
    """
    def decorator(func):
        import functools
        import asyncio

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except BotError as e:
                if logger:
                    logger.error(f"Bot error in {func.__name__}: {e}")
                    if e.details:
                        logger.error(f"Details: {e.details}")
                raise
            except Exception as e:
                if logger:
                    logger.error(f"Unexpected error in {func.__name__}: {e}")
                raise BotError(f"Unexpected error: {str(e)}")

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except BotError as e:
                if logger:
                    logger.error(f"Bot error in {func.__name__}: {e}")
                    if e.details:
                        logger.error(f"Details: {e.details}")
                raise
            except Exception as e:
                if logger:
                    logger.error(f"Unexpected error in {func.__name__}: {e}")
                raise BotError(f"Unexpected error: {str(e)}")

        # Return appropriate wrapper based on function type
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


# Retry decorator with exponential backoff
def retry_on_error(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (BotConnectionError, BotTimeoutError, BotAPIError),
    logger=None
):
    """
    Decorator to retry function on specific errors.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay on each retry
        exceptions: Tuple of exceptions to catch
        logger: Logger instance
        
    Usage:
        @retry_on_error(max_attempts=3, logger=logger)
        async def fetch_data():
            ...
    """
    def decorator(func):
        import functools
        import asyncio

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        if logger:
                            logger.error(
                                f"Failed after {max_attempts} attempts: {e}"
                            )
                        raise

                    if logger:
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed: {e}. "
                            f"Retrying in {current_delay}s..."
                        )

                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        if logger:
                            logger.error(
                                f"Failed after {max_attempts} attempts: {e}"
                            )
                        raise

                    if logger:
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed: {e}. "
                            f"Retrying in {current_delay}s..."
                        )

                    time.sleep(current_delay)
                    current_delay *= backoff

        # Return appropriate wrapper
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator
