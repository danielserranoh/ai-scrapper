"""
Centralized error handling utilities
"""

import logging
from typing import Callable, Any, Optional
from functools import wraps
import requests
from pipeline.base import ErrorAction


def handle_network_error(error: Exception, retry_count: int = 0, max_retries: int = 3) -> ErrorAction:
    """Standard network error handling logic"""
    if isinstance(error, requests.exceptions.Timeout):
        if retry_count < max_retries:
            return ErrorAction.RETRY
        return ErrorAction.SKIP
    
    elif isinstance(error, requests.exceptions.ConnectionError):
        if retry_count < max_retries:
            return ErrorAction.RETRY
        return ErrorAction.SKIP
    
    elif isinstance(error, requests.exceptions.HTTPError):
        status_code = error.response.status_code if hasattr(error, 'response') else None
        if status_code and status_code >= 500 and retry_count < max_retries:
            return ErrorAction.RETRY
        return ErrorAction.SKIP
    
    else:
        # Unknown network error - skip
        return ErrorAction.SKIP


def handle_parsing_error(error: Exception, retry_count: int = 0) -> ErrorAction:
    """Standard parsing error handling logic"""
    if isinstance(error, (AttributeError, TypeError, ValueError)):
        # Parsing issues - don't retry
        return ErrorAction.SKIP
    elif isinstance(error, MemoryError):
        # Content too large - skip
        return ErrorAction.SKIP
    else:
        # Other parsing errors - skip
        return ErrorAction.SKIP


def log_error_context(logger: logging.Logger, error: Exception, context: dict):
    """Log error with standardized context information"""
    context_str = ", ".join(f"{k}={v}" for k, v in context.items())
    logger.error(f"{type(error).__name__}: {error} | Context: {context_str}")


def retry_on_exception(
    exceptions: tuple = (Exception,),
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    logger: Optional[logging.Logger] = None
):
    """Decorator for retrying functions on specific exceptions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        if logger:
                            logger.debug(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying...")
                        if backoff_factor > 0:
                            import time
                            time.sleep(backoff_factor * (2 ** attempt))
                    else:
                        if logger:
                            logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}: {e}")
                        raise
            
            # This shouldn't be reached, but just in case
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


class CrawlerError(Exception):
    """Base exception for crawler-related errors"""
    pass


class ConfigurationError(CrawlerError):
    """Configuration-related errors"""
    pass


class PipelineError(CrawlerError):
    """Pipeline processing errors"""
    pass


class StorageError(CrawlerError):
    """Data storage errors"""
    pass


class RateLimitError(CrawlerError):
    """Rate limiting errors"""
    pass