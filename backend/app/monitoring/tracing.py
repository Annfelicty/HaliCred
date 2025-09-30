"""
Request Tracing and Correlation for HaliCred
Provides request correlation IDs and distributed tracing capabilities.
"""

import uuid
import time
from typing import Optional, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import contextvars

from .logger import get_logger, set_correlation_id, get_correlation_id
from .metrics import metrics_collector

logger = get_logger(__name__)

# Context variable for request context
request_context: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar('request_context', default={})


class RequestTracer:
    """Request tracing and correlation utility"""

    @staticmethod
    def generate_correlation_id() -> str:
        """Generate a new correlation ID"""
        return str(uuid.uuid4())

    @staticmethod
    def extract_correlation_id(request: Request) -> str:
        """Extract or generate correlation ID from request"""
        # Try to get from header first
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = request.headers.get("X-Request-ID")
        if not correlation_id:
            # Generate new one
            correlation_id = RequestTracer.generate_correlation_id()
        return correlation_id

    @staticmethod
    def set_request_context(
        request: Request,
        correlation_id: str,
        start_time: float
    ):
        """Set request context for the current request"""
        context = {
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "user_agent": request.headers.get("User-Agent", ""),
            "remote_addr": request.client.host if request.client else "",
            "start_time": start_time
        }
        request_context.set(context)
        set_correlation_id(correlation_id)

    @staticmethod
    def get_request_context() -> Dict[str, Any]:
        """Get current request context"""
        return request_context.get({})

    @staticmethod
    def log_request_start(request: Request, correlation_id: str):
        """Log request start"""
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra_fields={
                "request": {
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": str(request.query_params),
                    "headers": dict(request.headers),
                    "remote_addr": request.client.host if request.client else ""
                },
                "correlation_id": correlation_id
            }
        )

    @staticmethod
    def log_request_end(
        request: Request,
        response: Response,
        correlation_id: str,
        duration_ms: float,
        user_id: Optional[str] = None
    ):
        """Log request completion"""
        status_code = response.status_code
        log_level = "error" if status_code >= 500 else "warning" if status_code >= 400 else "info"

        log_data = {
            "request": {
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
                "status_code": status_code,
                "success": status_code < 400
            },
            "correlation_id": correlation_id
        }

        if user_id:
            log_data["user_id"] = user_id

        message = f"Request completed: {request.method} {request.url.path} - {status_code} ({duration_ms:.2f}ms)"

        if log_level == "error":
            logger.error(message, extra_fields=log_data)
        elif log_level == "warning":
            logger.warning(message, extra_fields=log_data)
        else:
            logger.info(message, extra_fields=log_data)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation IDs to all requests"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # Extract or generate correlation ID
        correlation_id = RequestTracer.extract_correlation_id(request)
        start_time = time.time()

        # Set request context
        RequestTracer.set_request_context(request, correlation_id, start_time)

        # Log request start
        RequestTracer.log_request_start(request, correlation_id)

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log exception
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                exception=e,
                extra_fields={
                    "request": {
                        "method": request.method,
                        "path": request.url.path,
                        "duration_ms": duration_ms
                    },
                    "correlation_id": correlation_id
                }
            )
            raise

        # Calculate duration and log completion
        duration_ms = (time.time() - start_time) * 1000

        # Record metrics
        metrics_collector.record_api_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms
        )

        # Extract user ID if available (from token or session)
        user_id = getattr(request.state, 'user_id', None)

        # Log request completion
        RequestTracer.log_request_end(request, response, correlation_id, duration_ms, user_id)

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect request metrics"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Increment active requests
        metrics_collector.active_requests += 1

        try:
            response = await call_next(request)
            return response
        finally:
            # Decrement active requests
            metrics_collector.active_requests -= 1

            # Record request metrics
            duration_ms = (time.time() - start_time) * 1000
            metrics_collector.request_count += 1
            metrics_collector.total_request_duration += duration_ms

            # Record error if status >= 400
            if hasattr(response, 'status_code') and response.status_code >= 400:
                metrics_collector.error_count += 1


def correlation_id_middleware(app: ASGIApp) -> ASGIApp:
    """Add correlation ID middleware to the application"""
    return CorrelationIdMiddleware(app)


def metrics_middleware(app: ASGIApp) -> ASGIApp:
    """Add metrics middleware to the application"""
    return MetricsMiddleware(app)