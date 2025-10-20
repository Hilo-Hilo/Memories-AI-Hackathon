"""
Enhanced error handling and resilience utilities for Focus Guardian.

Provides centralized error handling, circuit breaker pattern, and graceful degradation
strategies to make the application more robust against various failure modes.
"""

import time
import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional, Callable, Any
from collections import defaultdict, deque
import functools

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for classification."""
    LOW = "low"           # Non-critical, can continue operation
    MEDIUM = "medium"     # Degraded functionality, should alert user
    HIGH = "high"         # Critical failure, may need to pause session
    CRITICAL = "critical" # System-wide failure, should terminate gracefully


class ErrorCategory(Enum):
    """Error categories for targeted handling."""
    NETWORK = "network"
    API = "api"
    HARDWARE = "hardware"
    FILESYSTEM = "filesystem"
    CONFIGURATION = "configuration"
    RESOURCE = "resource"
    THREADING = "threading"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information for error handling."""
    component: str
    operation: str
    timestamp: float = field(default_factory=time.time)
    retry_count: int = 0
    last_retry: Optional[float] = None
    severity: ErrorSeverity = ErrorSeverity.LOW
    category: ErrorCategory = ErrorCategory.UNKNOWN
    user_visible: bool = False
    can_retry: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics."""
    failures: int = 0
    successes: int = 0
    last_failure: Optional[float] = None
    last_success: Optional[float] = None
    state_changes: int = 0


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, requests rejected
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker pattern implementation for API resilience."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Circuit breaker identifier
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before attempting recovery
            expected_exception: Exception type that triggers failure count
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self._state = CircuitBreakerState.CLOSED
        self._stats = CircuitBreakerStats()
        self._lock = threading.Lock()

        logger.info(f"Circuit breaker '{name}' initialized (threshold: {failure_threshold})")

    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap functions with circuit breaker logic."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper

    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        with self._lock:
            if self._state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self._state = CircuitBreakerState.HALF_OPEN
                    logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN")
                else:
                    raise RuntimeError(f"Circuit breaker '{self.name}' is OPEN")

        try:
            result = func(*args, **kwargs)

            with self._lock:
                if self._state == CircuitBreakerState.HALF_OPEN:
                    self._state = CircuitBreakerState.CLOSED
                    self._stats.successes += 1
                    self._stats.last_success = time.time()
                    self._stats.state_changes += 1
                    logger.info(f"Circuit breaker '{self.name}' recovered (CLOSED)")

            return result

        except self.expected_exception as e:
            with self._lock:
                self._stats.failures += 1
                self._stats.last_failure = time.time()

                if self._state == CircuitBreakerState.HALF_OPEN:
                    # Failed during recovery attempt, go back to open
                    self._state = CircuitBreakerState.OPEN
                    self._stats.state_changes += 1
                    logger.warning(f"Circuit breaker '{self.name}' failed during recovery (OPEN)")
                elif self._stats.failures >= self.failure_threshold:
                    self._state = CircuitBreakerState.OPEN
                    self._stats.state_changes += 1
                    logger.warning(f"Circuit breaker '{self.name}' opened after {self._stats.failures} failures")

            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self._stats.last_failure is None:
            return True
        return (time.time() - self._stats.last_failure) >= self.recovery_timeout

    def get_stats(self) -> CircuitBreakerStats:
        """Get current circuit breaker statistics."""
        with self._lock:
            return CircuitBreakerStats(
                failures=self._stats.failures,
                successes=self._stats.successes,
                last_failure=self._stats.last_failure,
                last_success=self._stats.last_success,
                state_changes=self._stats.state_changes
            )

    def reset(self) -> None:
        """Manually reset circuit breaker to closed state."""
        with self._lock:
            self._state = CircuitBreakerState.CLOSED
            self._stats = CircuitBreakerStats()
            logger.info(f"Circuit breaker '{self.name}' manually reset")


class ErrorHandler:
    """Centralized error handling and resilience management."""

    def __init__(self):
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._error_history: deque = deque(maxlen=1000)
        self._error_counts: defaultdict = defaultdict(int)
        self._lock = threading.Lock()

        # Initialize default circuit breakers
        self._setup_default_circuit_breakers()

    def _setup_default_circuit_breakers(self):
        """Setup default circuit breakers for critical services."""
        self._circuit_breakers = {
            'openai_vision': CircuitBreaker('openai_vision', failure_threshold=3, recovery_timeout=30.0),
            'hume_ai': CircuitBreaker('hume_ai', failure_threshold=2, recovery_timeout=60.0),
            'memories_ai': CircuitBreaker('memories_ai', failure_threshold=2, recovery_timeout=60.0),
            'database': CircuitBreaker('database', failure_threshold=5, recovery_timeout=10.0),
        }

    def handle_error(
        self,
        error: Exception,
        context: ErrorContext,
        retry_func: Optional[Callable] = None
    ) -> bool:
        """
        Handle an error with appropriate resilience strategy.

        Args:
            error: The exception that occurred
            context: Error context information
            retry_func: Optional function to retry operation

        Returns:
            True if operation should be retried, False otherwise
        """
        # Record error
        error_record = {
            'timestamp': context.timestamp,
            'component': context.component,
            'operation': context.operation,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'severity': context.severity.value,
            'category': context.category.value,
            'retry_count': context.retry_count,
        }

        with self._lock:
            self._error_history.append(error_record)
            self._error_counts[context.category.value] += 1

        # Log error with appropriate level
        log_message = (
            f"Error in {context.component}.{context.operation}: "
            f"{type(error).__name__}: {error}"
        )

        if context.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, exc_info=True)
        elif context.severity == ErrorSeverity.HIGH:
            logger.error(log_message, exc_info=True)
        elif context.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)

        # Handle by category
        if context.category == ErrorCategory.API:
            return self._handle_api_error(error, context, retry_func)
        elif context.category == ErrorCategory.NETWORK:
            return self._handle_network_error(error, context, retry_func)
        elif context.category == ErrorCategory.RESOURCE:
            return self._handle_resource_error(error, context, retry_func)
        elif context.category == ErrorCategory.THREADING:
            return self._handle_threading_error(error, context, retry_func)
        else:
            return self._handle_generic_error(error, context, retry_func)

    def _handle_api_error(self, error: Exception, context: ErrorContext, retry_func: Optional[Callable]) -> bool:
        """Handle API-related errors."""
        circuit_breaker = self._circuit_breakers.get(context.component)

        if circuit_breaker and isinstance(error, (ConnectionError, TimeoutError)):
            try:
                if retry_func:
                    circuit_breaker.call(retry_func)
                    return False  # Success, no retry needed
            except RuntimeError:
                # Circuit breaker is open
                if context.user_visible:
                    logger.warning(f"Service {context.component} temporarily unavailable")
                return False  # Don't retry, service unavailable

        # For other API errors, allow retry if appropriate
        return context.can_retry and context.retry_count < 3

    def _handle_network_error(self, error: Exception, context: ErrorContext, retry_func: Optional[Callable]) -> bool:
        """Handle network-related errors."""
        # Network errors are often transient, allow retries
        if isinstance(error, (ConnectionError, TimeoutError)):
            return context.can_retry and context.retry_count < 5

        return False

    def _handle_resource_error(self, error: Exception, context: ErrorContext, retry_func: Optional[Callable]) -> bool:
        """Handle resource-related errors (memory, disk, CPU)."""
        # Resource errors usually shouldn't be retried immediately
        if context.user_visible:
            logger.warning(f"Resource constraint in {context.component}: {error}")

        return False

    def _handle_threading_error(self, error: Exception, context: ErrorContext, retry_func: Optional[Callable]) -> bool:
        """Handle threading-related errors."""
        logger.error(f"Threading error in {context.component}: {error}")
        # Threading errors are usually not retryable
        return False

    def _handle_generic_error(self, error: Exception, context: ErrorContext, retry_func: Optional[Callable]) -> bool:
        """Handle generic errors."""
        return context.can_retry and context.retry_count < 2

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics summary."""
        with self._lock:
            recent_errors = list(self._error_history)[-10:] if self._error_history else []

            return {
                'total_errors': len(self._error_history),
                'error_counts_by_category': dict(self._error_counts),
                'recent_errors': recent_errors,
                'circuit_breaker_states': {
                    name: {
                        'state': cb._state.value,
                        'stats': cb.get_stats().__dict__
                    }
                    for name, cb in self._circuit_breakers.items()
                }
            }

    def reset_circuit_breaker(self, name: str) -> bool:
        """Reset a specific circuit breaker."""
        if name in self._circuit_breakers:
            self._circuit_breakers[name].reset()
            return True
        return False


# Global error handler instance
error_handler = ErrorHandler()


def handle_error(
    component: str,
    operation: str,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    user_visible: bool = False,
    can_retry: bool = True
):
    """
    Decorator for centralized error handling.

    Args:
        component: Component name (e.g., 'openai_vision_client')
        operation: Operation name (e.g., 'classify_image')
        severity: Error severity level
        category: Error category
        user_visible: Whether error should be shown to user
        can_retry: Whether operation can be retried
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = ErrorContext(
                    component=component,
                    operation=operation,
                    severity=severity,
                    category=category,
                    user_visible=user_visible,
                    can_retry=can_retry
                )

                retry_func = lambda: func(*args, **kwargs)
                should_retry = error_handler.handle_error(e, context, retry_func)

                if should_retry and context.retry_count < 3:  # Max 3 retries
                    # Implement exponential backoff retry
                    wait_time = min(2 ** context.retry_count, 30)  # Max 30 seconds
                    time.sleep(wait_time)
                    context.retry_count += 1
                    context.last_retry = time.time()
                    logger.info(f"Retrying {context.component}.{context.operation} (attempt {context.retry_count}/3)")
                    return wrapper(*args, **kwargs)  # Recursive retry
                else:
                    # Max retries exceeded or retry not recommended
                    if context.retry_count >= 3:
                        logger.error(f"Max retries exceeded for {context.component}.{context.operation}")
                    raise

        return wrapper
    return decorator


def with_circuit_breaker(name: str, **kwargs):
    """
    Decorator to apply circuit breaker pattern to a function.

    Args:
        name: Circuit breaker name
        **kwargs: Additional circuit breaker parameters
    """
    def decorator(func: Callable) -> Callable:
        if name not in error_handler._circuit_breakers:
            error_handler._circuit_breakers[name] = CircuitBreaker(name, **kwargs)

        cb = error_handler._circuit_breakers[name]

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return cb.call(func, *args, **kwargs)

        return wrapper
    return decorator
