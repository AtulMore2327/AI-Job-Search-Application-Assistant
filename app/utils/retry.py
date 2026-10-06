import time
import functools
from app.utils.logging import logger

def safe_retry(max_retries: int = 3, retries: int = None, backoff_factor: float = 1.0, backoff_in_seconds: float = None, exceptions=(Exception,)):
    """Decorator to retry functions on failure with exponential backoff."""
    actual_max = retries if retries is not None else max_retries
    actual_backoff = backoff_in_seconds if backoff_in_seconds is not None else backoff_factor
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cnt = 0
            delay = actual_backoff
            while cnt < actual_max:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    cnt += 1
                    if cnt >= actual_max:
                        logger.error(f"Function '{func.__name__}' failed after {actual_max} attempts: {e}")
                        raise e
                    logger.warning(f"Attempt {cnt}/{actual_max} failed for '{func.__name__}': {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2
        return wrapper
    return decorator

retry_with_backoff = safe_retry
