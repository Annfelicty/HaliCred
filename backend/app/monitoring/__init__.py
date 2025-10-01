"""
Monitoring and Observability Module for HaliCred
Provides comprehensive logging, metrics, and monitoring capabilities.
"""

from .error_handling import error_handler, ErrorHandler
from .logger import get_logger, StructuredLogger, setup_logging
from .metrics import MetricsCollector, metrics_collector
from .health import HealthChecker, health_checker
from .tracing import RequestTracer, CorrelationIdMiddleware, correlation_id_middleware, MetricsMiddleware
from .security import (
    SecurityHeadersMiddleware, RateLimitingMiddleware, InputValidationMiddleware,
    rate_limiter, security_config
)
from .error_handling import (
    validation_exception_handler, http_exception_handler, generic_exception_handler
)


__all__ = [
    'get_logger',
    'StructuredLogger',
    'setup_logging',
    'MetricsCollector',
    'metrics_collector',
    'HealthChecker',
    'health_checker',
    'RequestTracer',
    'CorrelationIdMiddleware',
    'correlation_id_middleware',
    'MetricsMiddleware',
    'SecurityHeadersMiddleware',
    'RateLimitingMiddleware',
    'InputValidationMiddleware',
    'rate_limiter',
    'security_config',
    'validation_exception_handler',
    'http_exception_handler',
    'generic_exception_handler',
    'error_handler',
    'ErrorHandler'
]
