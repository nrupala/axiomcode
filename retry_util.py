import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
):
    """Retry decorator with exponential backoff."""

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs) -> Any:
            last_exception: BaseException | None = None
            exc_types = exceptions
            for attempt in range(max_attempts):
                try:
                    return fn(*args, **kwargs)
                except BaseException as e:
                    if not isinstance(e, exc_types):
                        raise
                    last_exception = e
                    if attempt < max_attempts - 1:
                        wait_time = delay * (backoff**attempt)
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
            if last_exception is not None:
                raise last_exception
            return None

        return wrapper

    return decorator


@retry(max_attempts=3, delay=1.0)
def unstable_api_call():
    # Your flaky API call here
    pass
