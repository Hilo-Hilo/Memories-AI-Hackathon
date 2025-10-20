"""
Enhanced logging configuration for Focus Guardian.

Provides structured logging with observability features:
- Structured JSON logging for better parsing
- Performance metrics collection
- Request/response tracing
- Error context enrichment
- Log aggregation and alerting
"""

import logging
import sys
import json
import time
import threading
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from collections import defaultdict, deque
import traceback


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""

    def format(self, record: logging.LogRecord) -> str:
        # Add structured context to log record
        if not hasattr(record, 'structured_data'):
            record.structured_data = {}

        # Add timing information
        if not hasattr(record, 'start_time'):
            record.start_time = time.time()

        # Create structured log entry
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": getattr(record, 'threadName', 'unknown'),
        }

        # Add structured data if present
        if hasattr(record, 'structured_data') and record.structured_data:
            log_entry["data"] = record.structured_data

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add performance metrics if available
        if hasattr(record, 'duration_ms'):
            log_entry["duration_ms"] = record.duration_ms

        return json.dumps(log_entry)


class MetricsCollector:
    """Collects application metrics for observability."""

    def __init__(self):
        self._metrics = defaultdict(lambda: deque(maxlen=1000))
        self._counters = defaultdict(int)
        self._gauges = defaultdict(float)
        self._timers = defaultdict(lambda: deque(maxlen=1000))
        self._lock = threading.Lock()

    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        with self._lock:
            key = f"{name}{f'_{tags}' if tags else ''}"
            self._counters[key] += value

    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric."""
        with self._lock:
            key = f"{name}{f'_{tags}' if tags else ''}"
            self._gauges[key] = value

    def record_timer(self, name: str, duration_seconds: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a timer metric."""
        with self._lock:
            key = f"{name}{f'_{tags}' if tags else ''}"
            self._timers[key].append(duration_seconds)

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "timers": {
                    name: {
                        "count": len(values),
                        "avg": sum(values) / len(values) if values else 0,
                        "min": min(values) if values else 0,
                        "max": max(values) if values else 0,
                    }
                    for name, values in self._timers.items()
                }
            }


# Global metrics collector
metrics_collector = MetricsCollector()


def setup_logger(
    name: str = "focus_guardian",
    log_dir: Optional[Path] = None,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    enable_structured: bool = True,
    enable_metrics: bool = True
) -> logging.Logger:
    """
    Setup enhanced logger with observability features.

    Args:
        name: Logger name
        log_dir: Directory for log files (if None, only console logging)
        console_level: Logging level for console output
        file_level: Logging level for file output
        enable_structured: Enable structured JSON logging
        enable_metrics: Enable metrics collection

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Capture everything, handlers filter

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)

    if enable_structured:
        console_formatter = StructuredFormatter()
    else:
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%H:%M:%S'
        )

    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (if log_dir provided)
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"focus_guardian_{datetime.now().strftime('%Y%m%d')}.log"

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(file_level)

        if enable_structured:
            file_formatter = StructuredFormatter()
        else:
            file_formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Add metrics collection filter if enabled
    if enable_metrics:
        # Add a filter to collect metrics
        class MetricsFilter(logging.Filter):
            def filter(self, record):
                # Collect error metrics
                if record.levelno >= logging.ERROR:
                    metrics_collector.increment_counter("errors", tags={"level": record.levelname})
                return True

        logger.addFilter(MetricsFilter())

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_with_context(logger: logging.Logger, level: int, message: str, **kwargs) -> None:
    """
    Log a message with structured context data.

    Args:
        logger: Logger instance
        level: Logging level
        message: Log message
        **kwargs: Additional structured data to include
    """
    # Create a log record manually to add structured data
    record = logger.makeRecord(
        name=logger.name,
        level=level,
        fn="",
        lno=0,
        msg=message,
        args=(),
        exc_info=None
    )
    record.structured_data = kwargs
    logger.handle(record)


def log_performance(logger: logging.Logger, operation: str, duration_ms: float, **kwargs) -> None:
    """
    Log performance metrics for an operation.

    Args:
        logger: Logger instance
        operation: Operation name
        duration_ms: Duration in milliseconds
        **kwargs: Additional context
    """
    log_with_context(
        logger, logging.INFO,
        f"Performance: {operation}",
        operation=operation,
        duration_ms=duration_ms,
        **kwargs
    )

    # Also record in metrics collector
    metrics_collector.record_timer(f"{operation}_duration", duration_ms / 1000.0)


def log_api_call(logger: logging.Logger, api_name: str, duration_ms: float, success: bool, **kwargs) -> None:
    """
    Log API call metrics.

    Args:
        logger: Logger instance
        api_name: API name (e.g., 'openai_vision')
        duration_ms: Call duration in milliseconds
        success: Whether the call was successful
        **kwargs: Additional context
    """
    level = logging.INFO if success else logging.WARNING

    log_with_context(
        logger, level,
        f"API call: {api_name}",
        api=api_name,
        duration_ms=duration_ms,
        success=success,
        **kwargs
    )

    # Record metrics
    metrics_collector.record_timer(f"{api_name}_latency", duration_ms / 1000.0)
    metrics_collector.increment_counter(
        "api_calls",
        tags={"api": api_name, "success": "true" if success else "false"}
    )


class LogContext:
    """Context manager for adding structured data to log messages."""

    def __init__(self, logger: logging.Logger, **context_data):
        self.logger = logger
        self.context_data = context_data
        self._old_factory = None

    def __enter__(self):
        # Store original record factory
        self._old_factory = logging.getLogRecordFactory()

        # Create new factory that adds our context data
        def record_factory(*args, **kwargs):
            record = self._old_factory(*args, **kwargs)
            if not hasattr(record, 'structured_data'):
                record.structured_data = {}
            record.structured_data.update(self.context_data)
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original factory
        if self._old_factory:
            logging.setLogRecordFactory(self._old_factory)


class TimerContext:
    """Context manager for timing operations."""

    def __init__(self, logger: logging.Logger, operation: str, **context):
        self.logger = logger
        self.operation = operation
        self.context = context
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            log_performance(self.logger, self.operation, duration_ms, **self.context)

            # Record error if exception occurred
            if exc_type:
                metrics_collector.increment_counter("errors", tags={"operation": self.operation})


def get_metrics() -> Dict[str, Any]:
    """Get current application metrics."""
    return metrics_collector.get_metrics()


def log_error_with_context(logger: logging.Logger, error: Exception, operation: str, **context) -> None:
    """
    Log an error with enhanced context.

    Args:
        logger: Logger instance
        error: Exception that occurred
        operation: Operation that failed
        **context: Additional context data
    """
    # Create enhanced error context
    error_context = {
        "operation": operation,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
        **context
    }

    log_with_context(
        logger, logging.ERROR,
        f"Error in {operation}: {error}",
        **error_context
    )

    # Record error metrics
    metrics_collector.increment_counter("errors", tags={"operation": operation, "type": type(error).__name__})


def setup_observability(log_dir: Optional[Path] = None) -> None:
    """
    Setup comprehensive observability for the application.

    Args:
        log_dir: Directory for log files
    """
    # Setup structured logging
    setup_logger(
        "focus_guardian",
        log_dir=log_dir,
        enable_structured=True,
        enable_metrics=True
    )

    # Log startup metrics
    import psutil
    process = psutil.Process()

    logger = get_logger("focus_guardian")
    logger.info("Application observability initialized", structured_data={
        "pid": process.pid,
        "start_time": datetime.now().isoformat(),
        "python_version": sys.version,
        "platform": sys.platform
    })


# Initialize observability when module is imported
if __name__ != "__main__":
    # This will be called when the module is imported during app startup
    pass

