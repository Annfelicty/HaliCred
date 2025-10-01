"""
Structured Logging Implementation for HaliCred
Provides consistent, searchable, and analyzable logging across the application.
"""

import logging
import json
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, Optional, Union
from contextvars import ContextVar
from enum import Enum
import os

# Context variable for correlation ID
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class LogLevel(Enum):
    """Log levels enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "correlation_id": correlation_id_var.get(),
            "environment": os.getenv("ENVIRONMENT", "development"),
            "service": "halicred-backend",
        }

        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Add performance metrics if present
        if hasattr(record, 'duration_ms'):
            log_data["performance"] = {
                "duration_ms": record.duration_ms
            }

        # Add user context if present
        if hasattr(record, 'user_id'):
            log_data["user"] = {
                "id": record.user_id,
                "email": getattr(record, 'user_email', None)
            }

        # Add request context if present
        if hasattr(record, 'request_method'):
            log_data["request"] = {
                "method": record.request_method,
                "path": getattr(record, 'request_path', None),
                "ip": getattr(record, 'request_ip', None),
                "user_agent": getattr(record, 'user_agent', None)
            }

        return json.dumps(log_data)


class StructuredLogger:
    """Enhanced logger with structured logging capabilities"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.name = name

    def _log(
        self,
        level: str,
        message: str,
        extra_fields: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Internal method to log with structured data"""
        # Extract exc_info from kwargs as it's a reserved logging parameter
        exc_info = kwargs.pop("exc_info", None)

        extra = {"extra_fields": extra_fields or {}}
        extra.update(kwargs)

        # Add correlation ID if available
        correlation_id = correlation_id_var.get()
        if correlation_id:
            extra["correlation_id"] = correlation_id

        method = getattr(self.logger, level.lower())
        # Pass exc_info as a separate parameter, not in extra
        if exc_info is not None:
            method(message, exc_info=exc_info, extra=extra)
        else:
            method(message, extra=extra)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log(LogLevel.DEBUG.value, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log(LogLevel.INFO.value, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log(LogLevel.WARNING.value, message, **kwargs)

    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error message with optional exception"""
        if exception:
            kwargs["exc_info"] = sys.exc_info()
        self._log(LogLevel.ERROR.value, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self._log(LogLevel.CRITICAL.value, message, **kwargs)

    def log_api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Log API request with metrics"""
        message = f"API Request: {method} {path} - Status: {status_code}"
        extra_fields = {
            "api": {
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "success": 200 <= status_code < 400
            }
        }

        if user_id:
            extra_fields["user_id"] = user_id

        if error:
            extra_fields["error"] = error
            self.error(message, extra_fields=extra_fields)
        else:
            self.info(message, extra_fields=extra_fields)

    def log_database_query(
        self,
        query_type: str,
        table: str,
        duration_ms: float,
        rows_affected: int = 0,
        error: Optional[str] = None
    ):
        """Log database query with metrics"""
        message = f"Database Query: {query_type} on {table}"
        extra_fields = {
            "database": {
                "query_type": query_type,
                "table": table,
                "duration_ms": duration_ms,
                "rows_affected": rows_affected,
                "success": error is None
            }
        }

        if error:
            extra_fields["error"] = error
            self.error(message, extra_fields=extra_fields)
        else:
            self.debug(message, extra_fields=extra_fields)

    def log_external_api_call(
        self,
        service: str,
        endpoint: str,
        method: str,
        status_code: Optional[int] = None,
        duration_ms: Optional[float] = None,
        error: Optional[str] = None
    ):
        """Log external API call with metrics"""
        message = f"External API Call: {service} - {method} {endpoint}"
        extra_fields = {
            "external_api": {
                "service": service,
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "success": error is None
            }
        }

        if error:
            extra_fields["error"] = error
            self.error(message, extra_fields=extra_fields)
        else:
            self.info(message, extra_fields=extra_fields)

    def log_business_event(
        self,
        event_type: str,
        entity_type: str,
        entity_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log business event for analytics"""
        message = f"Business Event: {event_type} for {entity_type} {entity_id}"
        extra_fields = {
            "business_event": {
                "type": event_type,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "metadata": metadata or {}
            }
        }

        if user_id:
            extra_fields["user_id"] = user_id

        self.info(message, extra_fields=extra_fields)

    def log_security_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "WARNING"
    ):
        """Log security event for audit trail"""
        message = f"Security Event: {event_type}"
        extra_fields = {
            "security": {
                "event_type": event_type,
                "severity": severity,
                "details": details or {}
            }
        }

        if user_id:
            extra_fields["user_id"] = user_id

        if ip_address:
            extra_fields["ip_address"] = ip_address

        if severity == "CRITICAL":
            self.critical(message, extra_fields=extra_fields)
        elif severity == "HIGH":
            self.error(message, extra_fields=extra_fields)
        else:
            self.warning(message, extra_fields=extra_fields)

    def log_performance_metric(
        self,
        operation: str,
        duration_ms: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log performance metric"""
        message = f"Performance Metric: {operation} took {duration_ms}ms"
        extra_fields = {
            "performance": {
                "operation": operation,
                "duration_ms": duration_ms,
                "metadata": metadata or {}
            }
        }

        if duration_ms > 1000:  # Log as warning if > 1 second
            self.warning(message, extra_fields=extra_fields)
        else:
            self.debug(message, extra_fields=extra_fields)


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "structured",
    log_file: Optional[str] = None
):
    """
    Setup logging configuration for the application

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type ('structured' for JSON, 'simple' for plain text)
        log_file: Optional log file path
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)

    if log_format == "structured":
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )

    root_logger.addHandler(console_handler)

    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        if log_format == "structured":
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            )
        root_logger.addHandler(file_handler)


# Cache for logger instances
_logger_cache: Dict[str, StructuredLogger] = {}


def get_logger(name: str) -> StructuredLogger:
    """
    Get or create a structured logger instance

    Args:
        name: Logger name (usually __name__)

    Returns:
        StructuredLogger instance
    """
    if name not in _logger_cache:
        _logger_cache[name] = StructuredLogger(name)
    return _logger_cache[name]


# Set correlation ID for the current context
def set_correlation_id(correlation_id: str):
    """Set correlation ID for the current context"""
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> Optional[str]:
    """Get correlation ID from the current context"""
    return correlation_id_var.get()