"""
Security Hardening and Rate Limiting for HaliCred
Provides rate limiting, DDoS protection, and security enhancements.
"""

import time
import hashlib
from typing import Dict, Any, Optional, List
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
import redis
import re

from .logger import get_logger
from .error_handling import error_handler

logger = get_logger(__name__)


@dataclass
class RateLimit:
    """Rate limit configuration"""
    requests: int  # Number of requests
    window: int    # Time window in seconds
    burst: int     # Burst allowance


@dataclass
class SecurityConfig:
    """Security configuration"""
    enable_rate_limiting: bool = True
    enable_cors_protection: bool = True
    enable_xss_protection: bool = True
    enable_csrf_protection: bool = True
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: List[str] = None

    def __post_init__(self):
        if self.allowed_file_types is None:
            self.allowed_file_types = ['.jpg', '.jpeg', '.png', '.pdf', '.tiff', '.tif']


class RateLimiter:
    """In-memory rate limiter with Redis fallback"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.local_cache: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.rate_limits = {
            "default": RateLimit(requests=100, window=60, burst=10),
            "auth": RateLimit(requests=10, window=60, burst=3),
            "upload": RateLimit(requests=20, window=300, burst=5),
            "api": RateLimit(requests=1000, window=3600, burst=50)
        }

    def _get_client_key(self, request: Request, endpoint_type: str = "default") -> str:
        """Generate unique key for client identification"""
        # Use IP address as primary identifier
        client_ip = request.client.host if request.client else "unknown"

        # Add user agent hash for additional uniqueness
        user_agent = request.headers.get("User-Agent", "")
        ua_hash = hashlib.md5(user_agent.encode()).hexdigest()[:8]

        return f"rate_limit:{endpoint_type}:{client_ip}:{ua_hash}"

    def _get_endpoint_type(self, request: Request) -> str:
        """Determine endpoint type for rate limiting"""
        path = request.url.path.lower()

        if "/auth/" in path:
            return "auth"
        elif "/evidence/" in path or "/ai/evidence/" in path:
            return "upload"
        elif path.startswith("/api/"):
            return "api"
        else:
            return "default"

    async def is_allowed(self, request: Request) -> bool:
        """Check if request is allowed under rate limits"""
        endpoint_type = self._get_endpoint_type(request)
        rate_limit = self.rate_limits[endpoint_type]
        client_key = self._get_client_key(request, endpoint_type)

        current_time = time.time()
        window_start = current_time - rate_limit.window

        try:
            # Try Redis first if available
            if self.redis_client:
                return await self._check_redis_rate_limit(
                    client_key, rate_limit, current_time, window_start
                )
            else:
                return self._check_local_rate_limit(
                    client_key, rate_limit, current_time, window_start
                )
        except Exception as e:
            logger.error(f"Rate limiting check failed: {e}")
            # Allow request if rate limiting fails to avoid blocking legitimate users
            return True

    async def _check_redis_rate_limit(
        self,
        client_key: str,
        rate_limit: RateLimit,
        current_time: float,
        window_start: float
    ) -> bool:
        """Check rate limit using Redis"""
        pipe = self.redis_client.pipeline()

        # Remove old entries
        pipe.zremrangebyscore(client_key, 0, window_start)
        # Count current requests
        pipe.zcard(client_key)
        # Add current request
        pipe.zadd(client_key, {str(current_time): current_time})
        # Set expiry
        pipe.expire(client_key, rate_limit.window + 60)

        results = pipe.execute()
        request_count = results[1]

        return request_count < rate_limit.requests

    def _check_local_rate_limit(
        self,
        client_key: str,
        rate_limit: RateLimit,
        current_time: float,
        window_start: float
    ) -> bool:
        """Check rate limit using local memory"""
        requests = self.local_cache[client_key]

        # Remove old requests
        while requests and requests[0] < window_start:
            requests.popleft()

        # Check if under limit
        if len(requests) < rate_limit.requests:
            requests.append(current_time)
            return True

        return False

    def get_rate_limit_info(self, request: Request) -> Dict[str, Any]:
        """Get rate limit information for client"""
        endpoint_type = self._get_endpoint_type(request)
        rate_limit = self.rate_limits[endpoint_type]
        client_key = self._get_client_key(request, endpoint_type)

        current_time = time.time()
        window_start = current_time - rate_limit.window

        if self.redis_client:
            try:
                # Count current requests in Redis
                count = self.redis_client.zcount(client_key, window_start, current_time)
            except:
                count = 0
        else:
            # Count from local cache
            requests = self.local_cache[client_key]
            count = sum(1 for req_time in requests if req_time >= window_start)

        return {
            "limit": rate_limit.requests,
            "remaining": max(0, rate_limit.requests - count),
            "reset_time": int(current_time + rate_limit.window),
            "window_seconds": rate_limit.window
        }


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers"""

    def __init__(self, app, config: SecurityConfig = None):
        super().__init__(app)
        self.config = config or SecurityConfig()

    async def dispatch(self, request, call_next):
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # Add HSTS header for HTTPS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Add CSP header
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none'"
        )
        response.headers["Content-Security-Policy"] = csp_policy

        return response


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting"""

    def __init__(self, app, rate_limiter: RateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter

    async def dispatch(self, request, call_next):
        # Check rate limit
        if not await self.rate_limiter.is_allowed(request):
            # Log rate limit violation
            logger.warning(
                f"Rate limit exceeded for {request.client.host if request.client else 'unknown'}",
                extra_fields={
                    "security": {
                        "event_type": "rate_limit_exceeded",
                        "ip": request.client.host if request.client else "unknown",
                        "path": request.url.path,
                        "user_agent": request.headers.get("User-Agent", "")
                    }
                }
            )

            # Return rate limit error
            error = error_handler.create_error_response("RATE_001")
            return HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=error_handler.format_error_response(error)
            )

        # Add rate limit headers to response
        response = await call_next(request)
        rate_info = self.rate_limiter.get_rate_limit_info(request)

        response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_info["reset_time"])

        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for input validation and sanitization"""

    def __init__(self, app, config: SecurityConfig = None):
        super().__init__(app)
        self.config = config or SecurityConfig()

        # Compile regex patterns for validation
        self.xss_patterns = [
            re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
            re.compile(r'javascript:', re.IGNORECASE),
            re.compile(r'vbscript:', re.IGNORECASE),
            re.compile(r'onload=', re.IGNORECASE),
            re.compile(r'onerror=', re.IGNORECASE),
            re.compile(r'onclick=', re.IGNORECASE),
        ]

        self.sql_patterns = [
            re.compile(r'(union|select|insert|update|delete|drop|create|alter|exec|execute)', re.IGNORECASE),
            re.compile(r'(--|\/\*|\*\/)', re.IGNORECASE),
            re.compile(r"(;|'|\"|`)", re.IGNORECASE),
        ]

    async def dispatch(self, request, call_next):
        # Check request size
        if hasattr(request, 'headers'):
            content_length = request.headers.get('content-length')
            if content_length and int(content_length) > self.config.max_request_size:
                logger.warning(
                    f"Request size limit exceeded: {content_length} bytes",
                    extra_fields={
                        "security": {
                            "event_type": "request_size_exceeded",
                            "size": content_length,
                            "limit": self.config.max_request_size
                        }
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Request too large"
                )

        # Validate query parameters and headers for XSS
        if self.config.enable_xss_protection:
            self._validate_xss(request)

        response = await call_next(request)
        return response

    def _validate_xss(self, request: Request):
        """Validate request for XSS patterns"""
        # Check query parameters
        for param, value in request.query_params.items():
            if self._contains_malicious_content(value):
                logger.warning(
                    f"Potential XSS attack detected in query parameter: {param}",
                    extra_fields={
                        "security": {
                            "event_type": "xss_attempt",
                            "parameter": param,
                            "value": value[:100],  # Log only first 100 chars
                            "ip": request.client.host if request.client else "unknown"
                        }
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input detected"
                )

        # Check headers
        suspicious_headers = ['user-agent', 'referer', 'x-forwarded-for']
        for header in suspicious_headers:
            value = request.headers.get(header, '')
            if self._contains_malicious_content(value):
                logger.warning(
                    f"Potential XSS attack detected in header: {header}",
                    extra_fields={
                        "security": {
                            "event_type": "xss_attempt",
                            "header": header,
                            "value": value[:100],
                            "ip": request.client.host if request.client else "unknown"
                        }
                    }
                )

    def _contains_malicious_content(self, content: str) -> bool:
        """Check if content contains malicious patterns"""
        if not content:
            return False

        # Check for XSS patterns
        for pattern in self.xss_patterns:
            if pattern.search(content):
                return True

        # Check for SQL injection patterns (basic check)
        for pattern in self.sql_patterns:
            if pattern.search(content):
                return True

        return False


class SecurityMonitor:
    """Security event monitoring and alerting"""

    def __init__(self):
        self.suspicious_activity = defaultdict(list)
        self.blocked_ips = set()
        self.alert_thresholds = {
            "failed_auth_attempts": 5,
            "rate_limit_violations": 10,
            "xss_attempts": 3,
            "time_window": 300  # 5 minutes
        }

    def record_security_event(
        self,
        event_type: str,
        ip: str,
        details: Dict[str, Any] = None
    ):
        """Record a security event"""
        current_time = time.time()
        event = {
            "timestamp": current_time,
            "type": event_type,
            "details": details or {}
        }

        self.suspicious_activity[ip].append(event)

        # Clean old events
        cutoff_time = current_time - self.alert_thresholds["time_window"]
        self.suspicious_activity[ip] = [
            e for e in self.suspicious_activity[ip]
            if e["timestamp"] > cutoff_time
        ]

        # Check if IP should be blocked
        self._check_blocking_criteria(ip)

    def _check_blocking_criteria(self, ip: str):
        """Check if IP should be blocked based on suspicious activity"""
        events = self.suspicious_activity[ip]
        event_counts = defaultdict(int)

        for event in events:
            event_counts[event["type"]] += 1

        # Check thresholds
        should_block = False
        if event_counts["failed_auth"] >= self.alert_thresholds["failed_auth_attempts"]:
            should_block = True
        elif event_counts["rate_limit_violation"] >= self.alert_thresholds["rate_limit_violations"]:
            should_block = True
        elif event_counts["xss_attempt"] >= self.alert_thresholds["xss_attempts"]:
            should_block = True

        if should_block and ip not in self.blocked_ips:
            self.blocked_ips.add(ip)
            logger.critical(
                f"IP {ip} blocked due to suspicious activity",
                extra_fields={
                    "security": {
                        "event_type": "ip_blocked",
                        "ip": ip,
                        "reason": "threshold_exceeded",
                        "event_counts": dict(event_counts)
                    }
                }
            )

    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked"""
        return ip in self.blocked_ips

    def unblock_ip(self, ip: str):
        """Unblock an IP address"""
        self.blocked_ips.discard(ip)
        if ip in self.suspicious_activity:
            del self.suspicious_activity[ip]


# Global instances
security_config = SecurityConfig()
rate_limiter = RateLimiter()
security_monitor = SecurityMonitor()