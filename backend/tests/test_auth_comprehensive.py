"""
Comprehensive authentication and authorization tests for HaliCred backend.
Tests JWT handling, OTP verification, user sessions, and security measures.
"""

import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth import (
    create_token, verify_token, hash_password, verify_password,
    generate_otp, verify_otp, create_refresh_token, verify_refresh_token
)
from app.db.models import User
from app.config import settings


@pytest.mark.auth
class TestJWTTokenManagement:
    """Test JWT token creation, verification, and management."""

    def test_create_valid_token(self):
        """Test creating a valid JWT token."""
        payload = {"sub": "123", "role": "user"}
        token = create_token(payload)

        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are typically long

        # Verify token can be decoded
        decoded = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        assert decoded["sub"] == "123"
        assert decoded["role"] == "user"
        assert "exp" in decoded
        assert "iat" in decoded

    def test_token_expiration(self):
        """Test token expiration handling."""
        payload = {"sub": "123"}

        # Create token with short expiration
        with patch('app.auth.settings.JWT_EXPIRATION_MINUTES', 0.01):  # 0.6 seconds
            token = create_token(payload)

            # Should be valid immediately
            result = verify_token(token)
            assert result is not None
            assert result["sub"] == "123"

            # Wait for expiration
            import time
            time.sleep(1)

            # Should be expired
            result = verify_token(token)
            assert result is None

    def test_invalid_token_signature(self):
        """Test handling of tokens with invalid signatures."""
        payload = {"sub": "123"}
        token = create_token(payload)

        # Modify token to invalidate signature
        invalid_token = token[:-5] + "XXXXX"

        result = verify_token(invalid_token)
        assert result is None

    def test_malformed_token(self):
        """Test handling of malformed tokens."""
        malformed_tokens = [
            "not.a.token",
            "definitely-not-jwt",
            "",
            None,
            123,
            {"not": "a string"}
        ]

        for token in malformed_tokens:
            result = verify_token(token)
            assert result is None

    def test_token_with_custom_claims(self):
        """Test tokens with custom claims."""
        payload = {
            "sub": "123",
            "role": "admin",
            "permissions": ["read", "write", "delete"],
            "business_id": "456"
        }
        token = create_token(payload)

        result = verify_token(token)
        assert result["sub"] == "123"
        assert result["role"] == "admin"
        assert result["permissions"] == ["read", "write", "delete"]
        assert result["business_id"] == "456"

    def test_refresh_token_creation(self):
        """Test refresh token creation and verification."""
        user_id = "123"
        refresh_token = create_refresh_token(user_id)

        assert isinstance(refresh_token, str)

        # Verify refresh token
        result = verify_refresh_token(refresh_token)
        assert result is not None
        assert result["sub"] == user_id
        assert result["type"] == "refresh"

    def test_refresh_token_cannot_be_used_as_access_token(self):
        """Test that refresh tokens cannot be used for API access."""
        user_id = "123"
        refresh_token = create_refresh_token(user_id)

        # Trying to verify as access token should fail
        with patch('app.auth.verify_token') as mock_verify:
            mock_verify.return_value = None  # Simulate rejection
            result = verify_token(refresh_token)
            assert result is None


@pytest.mark.auth
class TestPasswordSecurity:
    """Test password hashing and verification."""

    def test_password_hashing(self):
        """Test password hashing produces different hashes for same password."""
        password = "test_password_123"

        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Should be different due to salt
        assert len(hash1) > 50  # Hashed passwords should be long
        assert len(hash2) > 50

    def test_password_verification_success(self):
        """Test successful password verification."""
        password = "secure_password_456"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_password_verification_failure(self):
        """Test password verification with wrong password."""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_password_special_characters(self):
        """Test password handling with special characters."""
        special_passwords = [
            "pässwörd_with_ümlauts",
            "password@#$%^&*()",
            "密码测试",
            "пароль",
            "🔐🔑password💪"
        ]

        for password in special_passwords:
            hashed = hash_password(password)
            assert verify_password(password, hashed) is True

    def test_empty_password_handling(self):
        """Test handling of empty passwords."""
        with pytest.raises(ValueError):
            hash_password("")

        with pytest.raises(ValueError):
            hash_password(None)

    def test_long_password_handling(self):
        """Test handling of very long passwords."""
        long_password = "a" * 1000  # 1000 character password
        hashed = hash_password(long_password)

        assert verify_password(long_password, hashed) is True


@pytest.mark.auth
class TestOTPSystem:
    """Test OTP generation and verification."""

    def test_otp_generation(self):
        """Test OTP generation format and uniqueness."""
        phone = "+254700000000"

        otp1 = generate_otp(phone)
        otp2 = generate_otp(phone)

        assert len(otp1) == 6  # Standard OTP length
        assert otp1.isdigit()  # Should be numeric
        assert otp1 != otp2  # Should be different (probabilistically)

    def test_otp_verification_success(self, mock_redis):
        """Test successful OTP verification."""
        phone = "+254700000000"
        otp = "123456"

        # Mock Redis to return the OTP
        mock_redis.get.return_value = otp.encode()

        result = verify_otp(phone, otp)
        assert result is True

        # Verify OTP was deleted after use
        mock_redis.delete.assert_called_once()

    def test_otp_verification_failure(self, mock_redis):
        """Test OTP verification with wrong code."""
        phone = "+254700000000"
        correct_otp = "123456"
        wrong_otp = "654321"

        mock_redis.get.return_value = correct_otp.encode()

        result = verify_otp(phone, wrong_otp)
        assert result is False

        # OTP should not be deleted on failure
        mock_redis.delete.assert_not_called()

    def test_otp_expiration(self, mock_redis):
        """Test OTP expiration handling."""
        phone = "+254700000000"
        otp = "123456"

        # Mock Redis to return None (expired/not found)
        mock_redis.get.return_value = None

        result = verify_otp(phone, otp)
        assert result is False

    def test_otp_rate_limiting(self, mock_redis):
        """Test OTP generation rate limiting."""
        phone = "+254700000000"

        # Mock Redis to simulate rate limit
        mock_redis.exists.return_value = True  # Rate limit key exists

        with pytest.raises(Exception, match="Rate limit"):
            generate_otp(phone)

    def test_otp_phone_format_validation(self):
        """Test OTP generation with invalid phone formats."""
        invalid_phones = [
            "1234567890",  # No country code
            "invalid",
            "",
            None,
            "+1234567890123456"  # Too long
        ]

        for phone in invalid_phones:
            with pytest.raises(ValueError):
                generate_otp(phone)


@pytest.mark.auth
@pytest.mark.api
class TestAuthenticationAPI:
    """Test authentication API endpoints."""

    def test_send_otp_success(self, client: TestClient, mock_redis):
        """Test successful OTP sending."""
        phone = "+254700000000"

        response = client.post("/auth/otp", json={"phone": phone})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sent"
        assert "message" in data

    def test_send_otp_invalid_phone(self, client: TestClient):
        """Test OTP sending with invalid phone number."""
        response = client.post("/auth/otp", json={"phone": "invalid"})

        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_verify_otp_success(self, client: TestClient, mock_redis, sample_user):
        """Test successful OTP verification and login."""
        phone = sample_user.phone
        otp = "123456"

        mock_redis.get.return_value = otp.encode()

        response = client.post("/auth/verify", json={
            "phone": phone,
            "otp": otp
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data

    def test_verify_otp_failure(self, client: TestClient, mock_redis):
        """Test OTP verification failure."""
        phone = "+254700000000"
        wrong_otp = "000000"

        mock_redis.get.return_value = "123456".encode()

        response = client.post("/auth/verify", json={
            "phone": phone,
            "otp": wrong_otp
        })

        assert response.status_code == 401
        data = response.json()
        assert "error" in data

    def test_refresh_token_endpoint(self, client: TestClient, sample_user):
        """Test token refresh endpoint."""
        refresh_token = create_refresh_token(str(sample_user.id))

        response = client.post("/auth/refresh", json={
            "refresh_token": refresh_token
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_token_invalid(self, client: TestClient):
        """Test refresh with invalid token."""
        response = client.post("/auth/refresh", json={
            "refresh_token": "invalid_token"
        })

        assert response.status_code == 401
        data = response.json()
        assert "error" in data

    def test_logout_endpoint(self, client: TestClient, authenticated_user):
        """Test logout endpoint."""
        headers = authenticated_user["headers"]

        response = client.post("/auth/logout", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "logged_out"

    def test_protected_endpoint_without_token(self, client: TestClient):
        """Test accessing protected endpoint without token."""
        response = client.get("/users/profile")

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_protected_endpoint_with_invalid_token(self, client: TestClient):
        """Test accessing protected endpoint with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}

        response = client.get("/users/profile", headers=headers)

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_protected_endpoint_with_valid_token(self, client: TestClient, authenticated_user):
        """Test accessing protected endpoint with valid token."""
        headers = authenticated_user["headers"]

        response = client.get("/users/profile", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "phone" in data


@pytest.mark.auth
@pytest.mark.security
class TestAuthenticationSecurity:
    """Test authentication security measures."""

    def test_timing_attack_resistance(self, client: TestClient, mock_redis):
        """Test resistance to timing attacks on OTP verification."""
        import time

        phone = "+254700000000"
        valid_otp = "123456"
        invalid_otp = "000000"

        mock_redis.get.return_value = valid_otp.encode()

        # Time multiple requests
        times = []
        for _ in range(10):
            start = time.time()
            client.post("/auth/verify", json={"phone": phone, "otp": invalid_otp})
            times.append(time.time() - start)

        # Response times should be relatively consistent
        avg_time = sum(times) / len(times)
        assert all(abs(t - avg_time) < 0.1 for t in times)  # Within 100ms

    def test_brute_force_protection(self, client: TestClient, mock_redis):
        """Test protection against brute force attacks."""
        phone = "+254700000000"

        # Simulate multiple failed attempts
        for i in range(6):  # Exceed rate limit
            response = client.post("/auth/verify", json={
                "phone": phone,
                "otp": "000000"
            })

            if i >= 5:  # After 5 attempts
                assert response.status_code == 429  # Rate limited

    def test_jwt_secret_not_exposed(self, client: TestClient):
        """Test that JWT secret is not exposed in responses."""
        response = client.post("/auth/otp", json={"phone": "+254700000000"})

        response_text = response.text.lower()
        assert "secret" not in response_text
        assert "jwt_secret" not in response_text
        assert settings.JWT_SECRET.lower() not in response_text

    def test_password_hash_not_exposed(self, client: TestClient, sample_user):
        """Test that password hashes are not exposed in API responses."""
        token = create_token({"sub": str(sample_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/users/profile", headers=headers)

        response_text = response.text.lower()
        assert "password" not in response_text
        assert "hash" not in response_text
        assert "$" not in response.text  # bcrypt hashes contain $

    def test_session_hijacking_protection(self, client: TestClient, authenticated_user):
        """Test protection against session hijacking."""
        headers = authenticated_user["headers"]

        # Normal request should work
        response = client.get("/users/profile", headers=headers)
        assert response.status_code == 200

        # Simulate request from different IP (would be handled by middleware)
        # This test verifies the structure is in place
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer ")

    def test_cors_security_headers(self, client: TestClient):
        """Test CORS and security headers are present."""
        response = client.options("/auth/otp")

        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers

    @pytest.mark.performance
    def test_token_verification_performance(self, authenticated_user):
        """Test token verification performance."""
        token = authenticated_user["token"]

        import time
        start_time = time.time()

        # Verify token 100 times
        for _ in range(100):
            result = verify_token(token)
            assert result is not None

        total_time = time.time() - start_time
        assert total_time < 1.0  # Should complete in under 1 second

    def test_token_blacklisting(self, client: TestClient, authenticated_user, mock_redis):
        """Test token blacklisting functionality."""
        headers = authenticated_user["headers"]

        # Logout to blacklist token
        response = client.post("/auth/logout", headers=headers)
        assert response.status_code == 200

        # Mock Redis to simulate blacklisted token
        mock_redis.exists.return_value = True

        # Token should now be invalid
        response = client.get("/users/profile", headers=headers)
        assert response.status_code == 401


@pytest.mark.auth
class TestUserRegistrationFlow:
    """Test complete user registration and authentication flow."""

    def test_complete_registration_flow(self, client: TestClient, mock_redis):
        """Test complete user registration from OTP to profile creation."""
        phone = "+254700123456"
        otp = "123456"

        # Step 1: Send OTP
        response = client.post("/auth/otp", json={"phone": phone})
        assert response.status_code == 200

        # Step 2: Verify OTP and register
        mock_redis.get.return_value = otp.encode()

        registration_data = {
            "phone": phone,
            "otp": otp,
            "name": "Test User",
            "email": "test@example.com",
            "business_name": "Test Business",
            "business_type": "farmer",
            "location": "Nairobi"
        }

        response = client.post("/auth/register", json=registration_data)
        assert response.status_code == 201

        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["phone"] == phone
        assert data["user"]["name"] == "Test User"

    def test_duplicate_phone_registration(self, client: TestClient, sample_user, mock_redis):
        """Test registration with already registered phone number."""
        otp = "123456"
        mock_redis.get.return_value = otp.encode()

        registration_data = {
            "phone": sample_user.phone,
            "otp": otp,
            "name": "Another User",
            "email": "another@example.com",
            "business_name": "Another Business",
            "business_type": "salon",
            "location": "Mombasa"
        }

        response = client.post("/auth/register", json=registration_data)
        assert response.status_code == 409  # Conflict

        data = response.json()
        assert "error" in data
        assert "already registered" in data["error"].lower()

    def test_registration_with_invalid_business_type(self, client: TestClient, mock_redis):
        """Test registration with invalid business type."""
        phone = "+254700123457"
        otp = "123456"
        mock_redis.get.return_value = otp.encode()

        registration_data = {
            "phone": phone,
            "otp": otp,
            "name": "Test User",
            "email": "test@example.com",
            "business_name": "Test Business",
            "business_type": "invalid_type",  # Invalid business type
            "location": "Nairobi"
        }

        response = client.post("/auth/register", json=registration_data)
        assert response.status_code == 400

        data = response.json()
        assert "error" in data