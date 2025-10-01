
# Health Check System for HaliCred
# Provides comprehensive health monitoring for all dependencies and services.


import asyncio
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import redis
import psycopg2
from sqlalchemy import text
from sqlalchemy.orm import Session
import aiohttp

from app.db import get_db  
from app.config import settings
from .logger import get_logger  

logger = get_logger(__name__)


class HealthStatus(Enum):
    """Health check status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a single health check"""
    service: str
    status: HealthStatus
    response_time_ms: float
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class HealthChecker:
    """Comprehensive health checking for all system dependencies"""

    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.cache: Dict[str, HealthCheckResult] = {}
        self.cache_duration = timedelta(seconds=30)  # Cache results for 30 seconds

    def register_check(self, name: str, check_func: Callable):
        """Register a health check function"""
        self.checks[name] = check_func

    async def check_database(self) -> HealthCheckResult:
        """Check database connectivity and performance"""
        start_time = time.time()
        try:
            # Get database session
            db_gen = get_db()
            db: Session = next(db_gen)

            # Test basic connectivity
            result = db.execute(text("SELECT 1")).fetchone()

            # Test basic table access
            user_count = db.execute(text("SELECT COUNT(*) FROM users")).fetchone()[0]

            response_time = (time.time() - start_time) * 1000

            return HealthCheckResult(
                service="database",
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                details={
                    "connection": "ok",
                    "user_count": user_count,
                    "query_result": result[0] if result else None
                }
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Database health check failed: {e}")
            return HealthCheckResult(
                service="database",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                error=str(e)
            )

    async def check_redis(self) -> HealthCheckResult:
        """Check Redis connectivity and performance"""
        start_time = time.time()
        try:
            # Connect to Redis
            redis_client = redis.Redis(
                host=settings.CELERY_BROKER_URL.split('://')[1].split(':')[0] if hasattr(settings, 'CELERY_BROKER_URL') else 'localhost',
                port=6379,
                decode_responses=True
            )

            # Test basic operations
            test_key = "health_check_test"
            redis_client.set(test_key, "test_value", ex=10)
            result = redis_client.get(test_key)
            redis_client.delete(test_key)

            # Get Redis info
            info = redis_client.info()

            response_time = (time.time() - start_time) * 1000

            return HealthCheckResult(
                service="redis",
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                details={
                    "connection": "ok",
                    "test_operation": "success" if result == "test_value" else "failed",
                    "memory_usage": info.get("used_memory_human", "unknown"),
                    "connected_clients": info.get("connected_clients", 0)
                }
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Redis health check failed: {e}")
            return HealthCheckResult(
                service="redis",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                error=str(e)
            )

    async def check_minio(self) -> HealthCheckResult:
        """Check MinIO/S3 connectivity"""
        start_time = time.time()
        try:
            from minio import Minio
            from minio.error import S3Error

            # Initialize MinIO client
            client = Minio(
                settings.MINIO_ENDPOINT if hasattr(settings, 'MINIO_ENDPOINT') else 'localhost:9000',
                access_key=settings.MINIO_ACCESS_KEY if hasattr(settings, 'MINIO_ACCESS_KEY') else 'minioaccess',
                secret_key=settings.MINIO_SECRET_KEY if hasattr(settings, 'MINIO_SECRET_KEY') else 'miniosecret',
                secure=False
            )

            # Test bucket access
            bucket_name = settings.MINIO_BUCKET if hasattr(settings, 'MINIO_BUCKET') else 'halicred'
            bucket_exists = client.bucket_exists(bucket_name)

            response_time = (time.time() - start_time) * 1000

            return HealthCheckResult(
                service="minio",
                status=HealthStatus.HEALTHY if bucket_exists else HealthStatus.DEGRADED,
                response_time_ms=response_time,
                details={
                    "connection": "ok",
                    "bucket_exists": bucket_exists,
                    "bucket_name": bucket_name
                }
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"MinIO health check failed: {e}")
            return HealthCheckResult(
                service="minio",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                error=str(e)
            )

    async def check_external_api(self, service_name: str, url: str, timeout: int = 5) -> HealthCheckResult:
        """Check external API connectivity"""
        start_time = time.time()
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(url) as response:
                    response_time = (time.time() - start_time) * 1000

                    # Consider 2xx and 4xx as healthy (service is responding)
                    if response.status < 500:
                        status = HealthStatus.HEALTHY
                    else:
                        status = HealthStatus.DEGRADED

                    return HealthCheckResult(
                        service=service_name,
                        status=status,
                        response_time_ms=response_time,
                        details={
                            "status_code": response.status,
                            "url": url
                        }
                    )

        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service=service_name,
                status=HealthStatus.DEGRADED,
                response_time_ms=response_time,
                error="Timeout",
                details={"url": url}
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"{service_name} health check failed: {e}")
            return HealthCheckResult(
                service=service_name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                error=str(e),
                details={"url": url}
            )

    async def check_gemini_api(self) -> HealthCheckResult:
        """Check Google Gemini API connectivity"""
        # Test with a simple endpoint that doesn't require complex setup
        return await self.check_external_api(
            "gemini_api",
            "https://generativelanguage.googleapis.com/v1/models",
            timeout=10
        )

    async def check_vision_api(self) -> HealthCheckResult:
        """Check Google Vision API connectivity"""
        # Test with Vision API discovery endpoint
        return await self.check_external_api(
            "vision_api",
            "https://vision.googleapis.com/$discovery/rest?version=v1",
            timeout=10
        )

    async def check_climatiq_api(self) -> HealthCheckResult:
        """Check Climatiq API connectivity"""
        return await self.check_external_api(
            "climatiq_api",
            "https://beta3.api.climatiq.io/data/v1/categories",
            timeout=10
        )

    async def check_application_health(self) -> HealthCheckResult:
        """Check application-level health"""
        start_time = time.time()
        try:
            from app.monitoring.metrics import metrics_collector

            # Get application metrics
            app_metrics = metrics_collector.get_health_metrics()
            response_time = (time.time() - start_time) * 1000

            # Determine status based on metrics
            if app_metrics["healthy"]:
                status = HealthStatus.HEALTHY
            elif app_metrics["error_rate_percent"] < 10:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY

            return HealthCheckResult(
                service="application",
                status=status,
                response_time_ms=response_time,
                details=app_metrics
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service="application",
                status=HealthStatus.UNKNOWN,
                response_time_ms=response_time,
                error=str(e)
            )

    async def check_otp_delivery_services(self) -> HealthCheckResult:
        """Check OTP delivery service configuration and health"""
        start_time = time.time()
        try:
            from app.config import settings
            from app.services.otp_service import otp_delivery_service

            issues = []
            status = HealthStatus.HEALTHY
            details = {
                "otp_mode": settings.OTP_MODE,
                "environment_mode": settings.ENVIRONMENT_MODE
            }

            # Check if OTP_MODE is on (delivery enabled)
            if settings.OTP_MODE.lower() == "on":
                # Check Africa's Talking SMS
                if otp_delivery_service.africas_talking_sms:
                    details["africas_talking_status"] = "initialized"
                    details["africas_talking_username"] = otp_delivery_service.africas_talking_username
                    details["africas_talking_env"] = settings.ENVIRONMENT_MODE
                else:
                    issues.append("Africa's Talking SMS not initialized")
                    status = HealthStatus.DEGRADED

                # Check SMTP Email
                if settings.SMTP_HOST and settings.SMTP_PASSWORD != "not_configured_yet":
                    details["smtp_status"] = "configured"
                    details["smtp_host"] = settings.SMTP_HOST
                else:
                    issues.append("SMTP email not configured")
                    status = HealthStatus.DEGRADED
            else:
                details["delivery_mode"] = "terminal_only"
                details["note"] = "OTP delivery disabled (OTP_MODE=off)"

            response_time = (time.time() - start_time) * 1000

            if issues:
                details["issues"] = issues

            return HealthCheckResult(
                service="otp_delivery",
                status=status,
                response_time_ms=response_time,
                details=details
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service="otp_delivery",
                status=HealthStatus.UNKNOWN,
                response_time_ms=response_time,
                error=str(e)
            )

    async def run_all_checks(self, use_cache: bool = True) -> Dict[str, HealthCheckResult]:
        """Run all health checks"""
        results = {}
        checks_to_run = [
            ("database", self.check_database),
            ("redis", self.check_redis),
            ("minio", self.check_minio),
            ("gemini_api", self.check_gemini_api),
            ("vision_api", self.check_vision_api),
            ("climatiq_api", self.check_climatiq_api),
            ("otp_delivery", self.check_otp_delivery_services),
            ("application", self.check_application_health)
        ]

        # Check cache first
        if use_cache:
            cached_results = self._get_cached_results()
            if cached_results:
                return cached_results

        # Run checks concurrently
        tasks = []
        for name, check_func in checks_to_run:
            tasks.append(self._run_check_with_timeout(name, check_func))

        check_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for i, result in enumerate(check_results):
            name = checks_to_run[i][0]
            if isinstance(result, Exception):
                results[name] = HealthCheckResult(
                    service=name,
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=0,
                    error=str(result)
                )
            else:
                results[name] = result

        # Cache results
        self._cache_results(results)

        return results

    async def _run_check_with_timeout(self, name: str, check_func: Callable, timeout: int = 30) -> HealthCheckResult:
        """Run a health check with timeout"""
        try:
            return await asyncio.wait_for(check_func(), timeout=timeout)
        except asyncio.TimeoutError:
            return HealthCheckResult(
                service=name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=timeout * 1000,
                error="Health check timeout"
            )

    def _get_cached_results(self) -> Optional[Dict[str, HealthCheckResult]]:
        """Get cached health check results if still valid"""
        if not self.cache:
            return None

        # Check if cache is still valid
        now = datetime.utcnow()
        for result in self.cache.values():
            if now - result.timestamp > self.cache_duration:
                return None

        return self.cache.copy()

    def _cache_results(self, results: Dict[str, HealthCheckResult]):
        """Cache health check results"""
        self.cache = results.copy()

    def get_overall_status(self, results: Dict[str, HealthCheckResult]) -> HealthStatus:
        """Determine overall system health status"""
        if not results:
            return HealthStatus.UNKNOWN

        # Count status types
        status_counts = {status: 0 for status in HealthStatus}
        for result in results.values():
            status_counts[result.status] += 1

        # Determine overall status
        if status_counts[HealthStatus.UNHEALTHY] > 0:
            # If any critical service is unhealthy
            critical_services = ["database", "application"]
            for service_name in critical_services:
                if service_name in results and results[service_name].status == HealthStatus.UNHEALTHY:
                    return HealthStatus.UNHEALTHY

            # If non-critical services are unhealthy, system is degraded
            return HealthStatus.DEGRADED

        elif status_counts[HealthStatus.DEGRADED] > 0:
            return HealthStatus.DEGRADED

        elif status_counts[HealthStatus.HEALTHY] == len(results):
            return HealthStatus.HEALTHY

        else:
            return HealthStatus.UNKNOWN

    def format_health_response(self, results: Dict[str, HealthCheckResult]) -> Dict[str, Any]:
        """Format health check results for API response"""
        overall_status = self.get_overall_status(results)

        response = {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "services": {}
        }

        for service_name, result in results.items():
            response["services"][service_name] = {
                "status": result.status.value,
                "response_time_ms": result.response_time_ms,
                "timestamp": result.timestamp.isoformat(),
            }

            if result.error:
                response["services"][service_name]["error"] = result.error

            if result.details:
                response["services"][service_name]["details"] = result.details

        return response


# Global health checker instance
health_checker = HealthChecker()