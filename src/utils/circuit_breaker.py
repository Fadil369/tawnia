"""
Circuit Breaker pattern implementation for fault tolerance
"""

import time
import asyncio
from enum import Enum
from typing import Callable, Any, Optional
from functools import wraps
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerError(Exception):
    """Circuit breaker exception"""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation for preventing cascading failures
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        expected_exception: type[Exception] = Exception,
        name: Optional[str] = None
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.name = name or "CircuitBreaker"

        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap functions with circuit breaker"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.call_async(func, *args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return self.call_sync(func, *args, **kwargs)

        # Return async wrapper if function is async
        if asyncio.iscoroutinefunction(func):
            return wrapper
        else:
            return sync_wrapper

    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Call function with circuit breaker protection (async)"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker {self.name} entering half-open state")
            else:
                raise CircuitBreakerError(f"Circuit breaker {self.name} is open")

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            self._on_success()
            return result

        except self.expected_exception as e:
            self._on_failure()
            raise e

    def call_sync(self, func: Callable, *args, **kwargs) -> Any:
        """Call function with circuit breaker protection (sync)"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker {self.name} entering half-open state")
            else:
                raise CircuitBreakerError(f"Circuit breaker {self.name} is open")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt to reset"""
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.timeout
        )

    def _on_success(self):
        """Handle successful call"""
        if self.state == CircuitState.HALF_OPEN:
            logger.info(f"Circuit breaker {self.name} reset to closed state")

        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker {self.name} opened after {self.failure_count} failures"
            )

    @property
    def is_open(self) -> bool:
        """Check if circuit breaker is open"""
        return self.state == CircuitState.OPEN

    @property
    def is_closed(self) -> bool:
        """Check if circuit breaker is closed"""
        return self.state == CircuitState.CLOSED

    def reset(self):
        """Manually reset circuit breaker"""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        logger.info(f"Circuit breaker {self.name} manually reset")


# Pre-configured circuit breakers for common operations
excel_processing_breaker = CircuitBreaker(
    failure_threshold=3,
    timeout=30.0,
    name="ExcelProcessing"
)

ai_api_breaker = CircuitBreaker(
    failure_threshold=5,
    timeout=60.0,
    name="AIAPICall"
)

database_breaker = CircuitBreaker(
    failure_threshold=3,
    timeout=15.0,
    name="DatabaseOperation"
)

external_api_breaker = CircuitBreaker(
    failure_threshold=5,
    timeout=120.0,
    name="ExternalAPI"
)
