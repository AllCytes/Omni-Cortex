"""Logging configuration for Omni-Cortex Dashboard.

Following IndyDevDan's logging philosophy:
- Agent visibility through structured stdout
- [SUCCESS] and [ERROR] prefixes for machine parsing
- Key metrics in success logs
- Full tracebacks in error logs
"""

import logging
import sys
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured agent-readable logs."""

    def format(self, record):
        # Format: [YYYY-MM-DD HH:MM:SS] [LEVEL] message
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname
        message = record.getMessage()

        # Add exception info if present
        if record.exc_info:
            import traceback
            exc_text = ''.join(traceback.format_exception(*record.exc_info))
            message = f"{message}\n[ERROR] Traceback:\n{exc_text}"

        return f"[{timestamp}] [{level}] {message}"


def setup_logging():
    """Configure logging for dashboard backend."""
    # Get or create logger
    logger = logging.getLogger("omni_cortex_dashboard")

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Console handler with structured formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(StructuredFormatter())

    logger.addHandler(console_handler)

    return logger


# Create global logger instance
logger = setup_logging()


def log_success(endpoint: str, **metrics):
    """Log a successful operation with key metrics.

    Args:
        endpoint: API endpoint (e.g., "/api/memories")
        **metrics: Key-value pairs of metrics to log

    Example:
        log_success("/api/memories", count=150, time_ms=45)
        # Output: [SUCCESS] /api/memories - count=150, time_ms=45
    """
    metric_str = ", ".join(f"{k}={v}" for k, v in metrics.items())
    logger.info(f"[SUCCESS] {endpoint} - {metric_str}")


def log_error(endpoint: str, exception: Exception, **context):
    """Log an error with exception details and context.

    Args:
        endpoint: API endpoint (e.g., "/api/memories")
        exception: The exception that occurred
        **context: Additional context key-value pairs

    Example:
        log_error("/api/memories", exc, project="path/to/db")
        # Output includes exception type, message, and full traceback
    """
    context_str = ", ".join(f"{k}={v}" for k, v in context.items()) if context else ""
    error_msg = f"[ERROR] {endpoint} - Exception: {type(exception).__name__}"
    if context_str:
        error_msg += f" - {context_str}"
    error_msg += f"\n[ERROR] Details: {str(exception)}"

    # Log with exception info to include traceback
    logger.error(error_msg, exc_info=True)
