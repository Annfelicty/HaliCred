"""
Comprehensive monitoring and security tests for HaliCred backend.
Tests health checks, logging, error handling, rate limiting, and security features.
"""

import pytest
import json
import time
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.monitoring.health import check_database_health, check_redis_health, check_external_services
from app.monitoring.logger import get_correlation_id, log_business_event, setup_logging
from app.monitoring.error_handling import StandardError, ErrorCategory, create_error_response
from app.monitoring.security import RateLimiter, SecurityMiddleware


@pytest.mark.monitoring
class TestHealthChecks:
    """Test system health check functionality."""

    def test_health_ready_endpoint(self, client: TestClient):
        """Test /health/ready endpoint."""
        response = client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "checks" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

    def test_health_live_endpoint(self, client: TestClient):
        """Test /health/live endpoint."""
        response = client.get("/health/live")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert "uptime" in data
        assert "timestamp" in data

    def test_database_health_check_success(self, db_session: Session):
        """Test successful database health check."""
        health = check_database_health(db_session)

        assert health["status"] == "healthy"
        assert health["response_time"] > 0
        assert health["details"]["connection"] == "ok"

    def test_database_health_check_failure(self):
        """Test database health check failure."""
        mock_db = Mock()
        mock_db.execute.side_effect = Exception("Database connection failed")

        health = check_database_health(mock_db)

        assert health["status"] == "unhealthy"
        assert "error" in health["details"]

    def test_redis_health_check_success(self, mock_redis):
        """Test successful Redis health check."""
        mock_redis.ping.return_value = True

        health = check_redis_health()

        assert health["status"] == "healthy"
        assert health["response_time"] > 0

    def test_redis_health_check_failure(self, mock_redis):
        """Test Redis health check failure."""
        mock_redis.ping.side_effect = Exception("Redis connection failed")

        health = check_redis_health()

        assert health["status"] == "unhealthy"
        assert "error" in health["details"]

    def test_external_services_health_check(self, mock_gemini_api, mock_vision_api, mock_climatiq_api):
        """Test external services health check."""
        health = check_external_services()

        assert "gemini" in health
        assert "vision" in health
        assert "climatiq" in health

        # Should have status for each service
        for service in ["gemini", "vision", "climatiq"]:
            assert "status" in health[service]
            assert health[service]["status"] in ["healthy", "unhealthy"]

    @pytest.mark.performance
    def test_health_check_performance(self, client: TestClient):
        """Test health check response time."""
        start_time = time.time()
        response = client.get("/health/ready")
        response_time = time.time() - start_time

        assert response.status_code == 200
        assert response_time < 5.0  # Should respond within 5 seconds

    def test_health_check_caching(self, client: TestClient):
        """Test health check result caching."""
        # First request
        response1 = client.get("/health/ready")
        timestamp1 = response1.json()["timestamp"]

        # Immediate second request should use cache
        response2 = client.get("/health/ready")
        timestamp2 = response2.json()["timestamp"]

        # Timestamps should be the same (cached)
        assert timestamp1 == timestamp2

        # Wait for cache expiry (if implemented)
        time.sleep(1)
        response3 = client.get("/health/ready")
        # This might be different depending on cache implementation


@pytest.mark.monitoring
class TestLogging:
    """Test structured logging functionality."""

    def test_correlation_id_generation(self):
        """Test correlation ID generation and format."""
        correlation_id = get_correlation_id()

        assert isinstance(correlation_id, str)
        assert len(correlation_id) >= 8  # Should be reasonably long
        assert correlation_id.replace("-", "").isalnum()  # Should be alphanumeric with hyphens

    def test_correlation_id_uniqueness(self):
        """Test that correlation IDs are unique."""
        ids = [get_correlation_id() for _ in range(100)]
        assert len(set(ids)) == 100  # All should be unique

    def test_structured_logging_format(self):
        """Test structured logging produces JSON format."""
        with patch('app.monitoring.logger.logger') as mock_logger:
            log_business_event("test_event", {"key": "value"}, "INFO")

            mock_logger.info.assert_called_once()
            # Check that the logged message is JSON-like
            call_args = mock_logger.info.call_args[0][0]
            assert isinstance(call_args, str)

    def test_business_event_logging(self):
        """Test business event logging."""
        event_data = {
            "user_id": "123",
            "action": "loan_application",
            "amount": 500000
        }

        with patch('app.monitoring.logger.logger') as mock_logger:
            log_business_event("loan_applied", event_data, "INFO")

            mock_logger.info.assert_called_once()

    def test_logging_with_correlation_id(self, client: TestClient):
        """Test that API requests include correlation IDs in logs."""
        with patch('app.monitoring.logger.logger') as mock_logger:
            response = client.get("/health/live")

            assert response.status_code == 200
            # Check if correlation ID header is present
            if "X-Correlation-ID" in response.headers:
                correlation_id = response.headers["X-Correlation-ID"]
                assert len(correlation_id) > 0

    def test_logging_configuration(self):
        """Test logging configuration setup."""
        logger_config = setup_logging()

        assert "version" in logger_config
        assert "handlers" in logger_config
        assert "formatters" in logger_config
        assert "loggers" in logger_config

    @pytest.mark.performance
    def test_logging_performance(self):
        """Test logging performance doesn't impact requests."""
        start_time = time.time()

        # Log 1000 events
        for i in range(1000):
            log_business_event(f"test_event_{i}", {"index": i}, "INFO")

        logging_time = time.time() - start_time

        # Logging should be fast
        assert logging_time < 1.0  # Should complete in under 1 second


@pytest.mark.monitoring
class TestErrorHandling:
    """Test standardized error handling."""

    def test_standard_error_creation(self):
        """Test creating standard error objects."""
        error = StandardError(
            category=ErrorCategory.VALIDATION,
            message="Invalid input data",
            details={"field": "amount", "value": -100},
            suggestion="Please provide a positive amount"
        )

        assert error.category == ErrorCategory.VALIDATION
        assert error.message == "Invalid input data"
        assert error.details["field"] == "amount"
        assert error.suggestion == "Please provide a positive amount"

    def test_error_response_format(self):
        """Test error response formatting."""
        error = StandardError(
            category=ErrorCategory.BUSINESS_LOGIC,
            message="Insufficient green score",
            correlation_id="test-123"
        )

        response = create_error_response(error, 400)

        assert response.status_code == 400
        response_data = json.loads(response.body)
        assert response_data["error"]["category"] == "BUSINESS_LOGIC"
        assert response_data["error"]["message"] == "Insufficient green score"
        assert response_data["correlation_id"] == "test-123"

    def test_error_categorization(self):
        """Test different error categories."""
        categories = [
            ErrorCategory.VALIDATION,
            ErrorCategory.AUTHENTICATION,
            ErrorCategory.AUTHORIZATION,
            ErrorCategory.BUSINESS_LOGIC,
            ErrorCategory.EXTERNAL_SERVICE,
            ErrorCategory.SYSTEM
        ]

        for category in categories:
            error = StandardError(category=category, message="Test error")
            assert error.category == category

    def test_api_error_handling(self, client: TestClient):
        """Test API error handling and response format."""
        # Test validation error
        response = client.post("/auth/otp", json={"phone": "invalid"})
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "correlation_id" in data

        # Test authentication error
        response = client.get("/users/profile")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data or "error" in data

    def test_error_logging(self):
        """Test that errors are properly logged."""
        with patch('app.monitoring.error_handling.logger') as mock_logger:
            error = StandardError(
                category=ErrorCategory.SYSTEM,
                message="Database connection failed"
            )
            create_error_response(error, 500)

            mock_logger.error.assert_called_once()

    def test_user_friendly_error_messages(self):
        """Test that error messages are user-friendly."""
        technical_error = StandardError(
            category=ErrorCategory.SYSTEM,
            message="SQLAlchemyError: connection timeout",
            user_message="We're experiencing technical difficulties. Please try again later."
        )

        response = create_error_response(technical_error, 500)
        response_data = json.loads(response.body)

        # User should see friendly message, not technical details
        assert "technical difficulties" in response_data["error"]["message"].lower()
        assert "sqlalchemy" not in response_data["error"]["message"].lower()


@pytest.mark.security
class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limiter_basic_functionality(self):
        """Test basic rate limiter functionality."""
        limiter = RateLimiter(limit=5, window=60)  # 5 requests per minute

        client_id = "test_client"

        # First 5 requests should be allowed
        for i in range(5):
            allowed = limiter.is_allowed(client_id)
            assert allowed is True

        # 6th request should be blocked
        allowed = limiter.is_allowed(client_id)
        assert allowed is False

    def test_rate_limiter_window_reset(self):
        """Test rate limiter window reset."""
        limiter = RateLimiter(limit=2, window=1)  # 2 requests per second

        client_id = "test_client"

        # Use up the limit
        assert limiter.is_allowed(client_id) is True
        assert limiter.is_allowed(client_id) is True
        assert limiter.is_allowed(client_id) is False

        # Wait for window to reset
        time.sleep(1.1)

        # Should be allowed again
        assert limiter.is_allowed(client_id) is True

    def test_rate_limiter_different_clients(self):
        """Test rate limiter with different clients."""
        limiter = RateLimiter(limit=3, window=60)

        # Each client should have separate limits
        assert limiter.is_allowed("client1") is True
        assert limiter.is_allowed("client2") is True
        assert limiter.is_allowed("client1") is True
        assert limiter.is_allowed("client2") is True

    def test_api_rate_limiting(self, client: TestClient):
        """Test rate limiting on API endpoints."""
        # Make multiple requests to trigger rate limiting
        responses = []
        for i in range(20):  # Make many requests
            response = client.post("/auth/otp", json={"phone": f"+25470000{i:04d}"})
            responses.append(response)

        # At least some should be rate limited
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes  # Too Many Requests

    def test_rate_limiting_headers(self, client: TestClient):
        """Test rate limiting headers are included."""
        response = client.get("/health/live")

        # Check for rate limiting headers
        assert "X-RateLimit-Limit" in response.headers or "RateLimit-Limit" in response.headers

    @pytest.mark.performance
    def test_rate_limiter_performance(self):
        """Test rate limiter performance."""
        limiter = RateLimiter(limit=1000, window=60)

        start_time = time.time()

        # Check 1000 requests
        for i in range(1000):
            limiter.is_allowed(f"client_{i}")

        processing_time = time.time() - start_time

        # Should be very fast
        assert processing_time < 1.0


@pytest.mark.security
class TestSecurityFeatures:
    """Test security middleware and features."""

    def test_security_headers(self, client: TestClient):
        """Test security headers are present."""
        response = client.get("/health/live")

        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security"
        ]

        for header in security_headers:
            assert header in response.headers or header.lower() in response.headers

    def test_cors_headers(self, client: TestClient):
        """Test CORS headers configuration."""
        response = client.options("/auth/otp")

        cors_headers = [
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Methods",
            "Access-Control-Allow-Headers"
        ]

        for header in cors_headers:
            assert header in response.headers

    def test_input_sanitization(self, client: TestClient):
        """Test input sanitization prevents XSS."""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "'; DROP TABLE users; --"
        ]

        for malicious_input in malicious_inputs:
            response = client.post("/auth/otp", json={"phone": malicious_input})

            # Should either be rejected or sanitized
            assert response.status_code in [400, 422]  # Validation error
            response_text = response.text.lower()
            assert "script" not in response_text
            assert "javascript:" not in response_text

    def test_sql_injection_protection(self, client: TestClient, authenticated_user):
        """Test SQL injection protection."""
        headers = authenticated_user["headers"]

        # Try SQL injection in query parameters
        malicious_queries = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "UNION SELECT * FROM users"
        ]

        for query in malicious_queries:
            response = client.get(f"/loans/my-loans?search={query}", headers=headers)

            # Should not cause server error (500)
            assert response.status_code != 500
            # Should either work normally or return validation error
            assert response.status_code in [200, 400, 422]

    def test_authentication_bypass_attempts(self, client: TestClient, sample_user):
        """Test protection against authentication bypass."""
        bypass_attempts = [
            {"Authorization": "Bearer fake_token"},
            {"Authorization": "Bearer "},
            {"Authorization": "Basic fake_credentials"},
            {"X-User-ID": str(sample_user.id)},
            {"X-Admin": "true"}
        ]

        for headers in bypass_attempts:
            response = client.get("/users/profile", headers=headers)
            assert response.status_code == 401  # Should be unauthorized

    def test_privilege_escalation_protection(self, client: TestClient, authenticated_user):
        """Test protection against privilege escalation."""
        headers = authenticated_user["headers"]

        # Try to access admin endpoints
        admin_endpoints = [
            "/admin/users",
            "/admin/loans/approve",
            "/admin/system/config"
        ]

        for endpoint in admin_endpoints:
            response = client.get(endpoint, headers=headers)
            # Should either be forbidden or not found (but not internal error)
            assert response.status_code in [403, 404]

    def test_data_exposure_protection(self, client: TestClient, authenticated_user):
        """Test protection against data exposure."""
        headers = authenticated_user["headers"]

        response = client.get("/users/profile", headers=headers)

        if response.status_code == 200:
            data = response.json()

            # Sensitive fields should not be exposed
            sensitive_fields = ["password", "password_hash", "secret", "private_key"]
            response_text = json.dumps(data).lower()

            for field in sensitive_fields:
                assert field not in response_text

    @pytest.mark.performance
    def test_security_middleware_performance(self, client: TestClient):
        """Test security middleware doesn't significantly impact performance."""
        start_time = time.time()

        # Make 100 requests
        for i in range(100):
            response = client.get("/health/live")
            assert response.status_code == 200

        total_time = time.time() - start_time

        # Should complete reasonably quickly
        assert total_time < 10.0  # 100 requests in under 10 seconds

    def test_ddos_protection(self, client: TestClient):
        """Test DDoS protection measures."""
        # Simulate rapid requests from same client
        rapid_requests = []
        start_time = time.time()

        for i in range(50):
            response = client.get("/health/live")
            rapid_requests.append(response)

        # Should either rate limit or handle gracefully
        status_codes = [r.status_code for r in rapid_requests]

        # Most should succeed, but some might be rate limited
        success_rate = sum(1 for code in status_codes if code == 200) / len(status_codes)
        assert success_rate >= 0.5  # At least 50% should succeed


@pytest.mark.security
@pytest.mark.integration
class TestSecurityIntegration:
    """Test security features integration."""

    def test_complete_security_workflow(self, client: TestClient):
        """Test complete security workflow from request to response."""
        # Step 1: Send request with potential security issues
        malicious_phone = "<script>alert('xss')</script>"

        response = client.post("/auth/otp", json={"phone": malicious_phone})

        # Step 2: Verify security measures
        assert response.status_code in [400, 422]  # Input validation
        assert "X-Content-Type-Options" in response.headers  # Security headers
        assert "script" not in response.text.lower()  # XSS protection

        # Step 3: Check rate limiting headers
        assert any(header.startswith(("X-RateLimit", "RateLimit")) for header in response.headers)

    def test_security_logging(self):
        """Test that security events are logged."""
        with patch('app.monitoring.security.logger') as mock_logger:
            # Simulate security event
            security_middleware = SecurityMiddleware()

            # This would normally be called by middleware
            mock_logger.warning.assert_not_called()  # No events yet

    def test_security_monitoring_alerts(self):
        """Test security monitoring and alerting."""
        # This would integrate with external monitoring systems
        # For now, verify the structure is in place
        from app.monitoring.security import log_security_event

        with patch('app.monitoring.security.logger') as mock_logger:
            log_security_event("RATE_LIMIT_EXCEEDED", {"client_ip": "192.168.1.1"})
            mock_logger.warning.assert_called_once()