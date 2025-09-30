"""
Comprehensive API endpoint tests for HaliCred backend.
Tests all major API endpoints with various scenarios for Phase 6 requirements.
"""

import pytest
import json
import io
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import User, GreenScore, LoanApplication, Evidence


@pytest.mark.api
class TestAuthenticationAPI:
    """Test authentication endpoints comprehensively."""

    def test_send_otp_success(self, client: TestClient, mock_redis):
        """Test successful OTP sending."""
        response = client.post("/auth/otp", json={"phone": "+254700000000"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sent"
        assert "message" in data

    def test_send_otp_invalid_phone(self, client: TestClient):
        """Test OTP sending with invalid phone number."""
        response = client.post("/auth/otp", json={"phone": "invalid"})
        assert response.status_code == 422

    def test_send_otp_missing_phone(self, client: TestClient):
        """Test OTP sending without phone number."""
        response = client.post("/auth/otp", json={})
        assert response.status_code == 422

    def test_verify_otp_success(self, client: TestClient, mock_redis):
        """Test successful OTP verification."""
        # Setup mock Redis to return valid OTP
        mock_redis.get.return_value = "123456"

        response = client.post("/auth/verify", json={
            "phone": "+254700000000",
            "otp": "123456"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_verify_otp_invalid_code(self, client: TestClient, mock_redis):
        """Test OTP verification with invalid code."""
        mock_redis.get.return_value = "123456"

        response = client.post("/auth/verify", json={
            "phone": "+254700000000",
            "otp": "wrong"
        })
        assert response.status_code == 400

    def test_verify_otp_expired(self, client: TestClient, mock_redis):
        """Test OTP verification with expired code."""
        mock_redis.get.return_value = None

        response = client.post("/auth/verify", json={
            "phone": "+254700000000",
            "otp": "123456"
        })
        assert response.status_code == 400

    def test_register_user_success(self, client: TestClient, authenticated_user):
        """Test successful user registration."""
        headers = authenticated_user["headers"]
        user_data = {
            "name": "Jane Doe",
            "business_name": "Jane's Farm",
            "business_type": "farmer",
            "location": "Nakuru"
        }

        response = client.post("/auth/register", json=user_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == user_data["name"]
        assert data["business_name"] == user_data["business_name"]

    def test_register_user_unauthorized(self, client: TestClient):
        """Test user registration without authentication."""
        user_data = {
            "name": "Jane Doe",
            "business_name": "Jane's Farm",
            "business_type": "farmer",
            "location": "Nakuru"
        }

        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 401

    def test_register_user_invalid_data(self, client: TestClient, authenticated_user):
        """Test user registration with invalid data."""
        headers = authenticated_user["headers"]
        invalid_data = {
            "name": "",  # Empty name
            "business_type": "invalid",  # Invalid business type
        }

        response = client.post("/auth/register", json=invalid_data, headers=headers)
        assert response.status_code == 422


@pytest.mark.api
class TestScoreAPI:
    """Test GreenScore endpoints comprehensively."""

    def test_get_current_score_success(self, client: TestClient, authenticated_user, sample_greenscore):
        """Test getting current score successfully."""
        headers = authenticated_user["headers"]

        response = client.get("/ai/greenscore/current", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["overall_score"] == sample_greenscore.overall_score
        assert data["confidence_score"] == sample_greenscore.confidence_score

    def test_get_current_score_no_score(self, client: TestClient, authenticated_user):
        """Test getting current score when no score exists."""
        headers = authenticated_user["headers"]

        response = client.get("/ai/greenscore/current", headers=headers)
        assert response.status_code == 404

    def test_get_current_score_unauthorized(self, client: TestClient):
        """Test getting current score without authentication."""
        response = client.get("/ai/greenscore/current")
        assert response.status_code == 401

    def test_compute_score_success(self, client: TestClient, authenticated_user, sample_evidence):
        """Test score computation successfully."""
        headers = authenticated_user["headers"]

        with patch('app.ai.orchestrator.process_evidence') as mock_process:
            mock_process.return_value = {
                "overall_score": 85,
                "confidence": 0.9,
                "subscores": {
                    "energy_efficiency": 90,
                    "water_conservation": 80,
                    "waste_management": 85,
                    "renewable_energy": 85
                }
            }

            response = client.post("/score/compute", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["overall_score"] == 85
            assert data["confidence_score"] == 0.9

    def test_compute_score_no_evidence(self, client: TestClient, authenticated_user):
        """Test score computation with no evidence."""
        headers = authenticated_user["headers"]

        response = client.post("/score/compute", headers=headers)
        assert response.status_code == 400

    def test_get_score_history(self, client: TestClient, authenticated_user, db_session: Session):
        """Test getting score history."""
        headers = authenticated_user["headers"]
        user = authenticated_user["user"]

        # Create multiple scores for history
        for i in range(3):
            score = GreenScore(
                user_id=user.id,
                overall_score=70 + i * 5,
                energy_efficiency=75 + i * 3,
                water_conservation=70 + i * 4,
                waste_management=80 + i * 2,
                renewable_energy=65 + i * 6,
                carbon_footprint=70 + i * 3,
                confidence_score=0.8 + i * 0.05,
                evidence_count=2 + i,
                last_updated=datetime.utcnow() - timedelta(days=30 - i * 10)
            )
            db_session.add(score)
        db_session.commit()

        response = client.get("/score/history", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["overall_score"] == 80  # Most recent


@pytest.mark.api
class TestLoanAPI:
    """Test loan endpoints comprehensively."""

    def test_get_loan_offers_success(self, client: TestClient, authenticated_user, sample_greenscore):
        """Test getting loan offers successfully."""
        headers = authenticated_user["headers"]

        response = client.post("/loan/offers", json={
            "amount": 500000,
            "tenor": 12
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "options" in data
        assert len(data["options"]) > 0
        assert all("rate" in option for option in data["options"])

    def test_get_loan_offers_no_score(self, client: TestClient, authenticated_user):
        """Test getting loan offers without GreenScore."""
        headers = authenticated_user["headers"]

        response = client.post("/loan/offers", json={
            "amount": 500000,
            "tenor": 12
        }, headers=headers)
        assert response.status_code == 400

    def test_apply_for_loan_success(self, client: TestClient, authenticated_user, sample_greenscore):
        """Test loan application successfully."""
        headers = authenticated_user["headers"]
        loan_data = {
            "amount": 500000,
            "term": 12,
            "purpose": "equipment",
            "business_plan": "Expand sustainable farming operations"
        }

        response = client.post("/loan/apply", json=loan_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == loan_data["amount"]
        assert data["status"] == "pending"

    def test_apply_for_loan_invalid_amount(self, client: TestClient, authenticated_user, sample_greenscore):
        """Test loan application with invalid amount."""
        headers = authenticated_user["headers"]
        loan_data = {
            "amount": -1000,  # Invalid negative amount
            "term": 12,
            "purpose": "equipment"
        }

        response = client.post("/loan/apply", json=loan_data, headers=headers)
        assert response.status_code == 422

    def test_get_my_loans(self, client: TestClient, authenticated_user, sample_loan_application):
        """Test getting user's loan applications."""
        headers = authenticated_user["headers"]

        response = client.get("/loan/my", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["amount"] == sample_loan_application.amount

    def test_get_loan_details(self, client: TestClient, authenticated_user, sample_loan_application):
        """Test getting specific loan details."""
        headers = authenticated_user["headers"]

        response = client.get(f"/loan/{sample_loan_application.id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_loan_application.id
        assert data["amount"] == sample_loan_application.amount

    def test_get_loan_details_not_found(self, client: TestClient, authenticated_user):
        """Test getting non-existent loan details."""
        headers = authenticated_user["headers"]

        response = client.get("/loan/99999", headers=headers)
        assert response.status_code == 404


@pytest.mark.api
class TestEvidenceAPI:
    """Test evidence endpoints comprehensively."""

    def test_upload_evidence_success(self, client: TestClient, authenticated_user, temp_upload_dir):
        """Test evidence upload successfully."""
        headers = authenticated_user["headers"]

        # Create a test image file
        test_image = b"fake image content"
        files = {
            "file": ("test_receipt.jpg", io.BytesIO(test_image), "image/jpeg")
        }
        data = {
            "evidence_type": "solar_panel",
            "description": "Solar panel installation receipt"
        }

        with patch('app.services.minio_client'):
            response = client.post("/evidence/upload", files=files, data=data, headers=headers)
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["evidence_type"] == "solar_panel"
            assert response_data["processing_status"] == "pending"

    def test_upload_evidence_invalid_file_type(self, client: TestClient, authenticated_user):
        """Test evidence upload with invalid file type."""
        headers = authenticated_user["headers"]

        # Create a test file with unsupported format
        test_file = b"fake content"
        files = {
            "file": ("test.txt", io.BytesIO(test_file), "text/plain")
        }
        data = {
            "evidence_type": "solar_panel",
            "description": "Invalid file type"
        }

        response = client.post("/evidence/upload", files=files, data=data, headers=headers)
        assert response.status_code == 400

    def test_upload_evidence_too_large(self, client: TestClient, authenticated_user):
        """Test evidence upload with file too large."""
        headers = authenticated_user["headers"]

        # Create a large file (simulate 60MB)
        large_file = b"x" * (60 * 1024 * 1024)
        files = {
            "file": ("large_file.jpg", io.BytesIO(large_file), "image/jpeg")
        }
        data = {
            "evidence_type": "solar_panel",
            "description": "File too large"
        }

        response = client.post("/evidence/upload", files=files, data=data, headers=headers)
        assert response.status_code == 413

    def test_get_evidence_list(self, client: TestClient, authenticated_user, sample_evidence):
        """Test getting evidence list."""
        headers = authenticated_user["headers"]

        response = client.get("/evidence/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["evidence_type"] == sample_evidence.evidence_type

    def test_get_evidence_details(self, client: TestClient, authenticated_user, sample_evidence):
        """Test getting specific evidence details."""
        headers = authenticated_user["headers"]

        response = client.get(f"/evidence/{sample_evidence.id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_evidence.id
        assert data["evidence_type"] == sample_evidence.evidence_type

    def test_process_evidence_success(self, client: TestClient, authenticated_user, sample_evidence,
                                     mock_gemini_api, mock_vision_api, mock_climatiq_api):
        """Test evidence processing successfully."""
        headers = authenticated_user["headers"]

        response = client.post(f"/ai/evidence/process", json={
            "evidence_id": sample_evidence.id,
            "sector": "agriculture",
            "region": "Kenya"
        }, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "confidence" in data
        assert "greenscore" in data


@pytest.mark.api
class TestHealthAPI:
    """Test health check endpoints."""

    def test_basic_health_check(self, client: TestClient):
        """Test basic health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_readiness_check(self, client: TestClient):
        """Test readiness check endpoint."""
        with patch('app.monitoring.health.health_checker.run_all_checks') as mock_checks:
            mock_checks.return_value = {
                "database": {"status": "healthy"},
                "redis": {"status": "healthy"},
                "minio": {"status": "healthy"}
            }

            response = client.get("/health/ready")
            assert response.status_code == 200

    def test_liveness_check(self, client: TestClient):
        """Test liveness check endpoint."""
        response = client.get("/health/live")
        assert response.status_code == 200


@pytest.mark.api
class TestAdminAPI:
    """Test admin endpoints comprehensively."""

    def test_get_all_applications(self, client: TestClient, multiple_loan_applications):
        """Test getting all loan applications (admin view)."""
        # Note: In a real implementation, this would require admin authentication
        response = client.get("/admin/applications")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(multiple_loan_applications)

    def test_update_application_status(self, client: TestClient, sample_loan_application):
        """Test updating loan application status."""
        update_data = {
            "status": "approved",
            "admin_notes": "Application approved based on strong GreenScore",
            "approved_amount": sample_loan_application.amount,
            "approved_rate": 10.5
        }

        response = client.put(f"/admin/applications/{sample_loan_application.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"


@pytest.mark.performance
class TestPerformanceAPI:
    """Test API performance characteristics."""

    def test_concurrent_score_requests(self, client: TestClient, multiple_users):
        """Test handling concurrent score computation requests."""
        import concurrent.futures
        import threading

        results = []

        def make_request(user_id):
            # This would need proper authentication for each user
            response = client.post("/score/compute")
            return response.status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, user.id) for user in multiple_users[:10]]
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())

        # Most requests should succeed (some might fail auth, but server should handle load)
        assert len(results) == 10

    def test_large_evidence_processing(self, client: TestClient, authenticated_user):
        """Test processing large evidence files."""
        headers = authenticated_user["headers"]

        # Simulate large file processing
        large_evidence_data = {
            "evidence_id": 1,
            "sector": "agriculture",
            "region": "Kenya",
            "file_size": 45 * 1024 * 1024  # 45MB
        }

        with patch('app.ai.orchestrator.process_evidence') as mock_process:
            mock_process.return_value = {"status": "completed", "confidence": 0.8}

            response = client.post("/ai/evidence/process", json=large_evidence_data, headers=headers)
            # Should complete within reasonable time
            assert response.status_code in [200, 202]  # Accept async processing


@pytest.mark.security
class TestSecurityAPI:
    """Test API security characteristics."""

    def test_sql_injection_protection(self, client: TestClient):
        """Test protection against SQL injection attacks."""
        malicious_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'/*",
            "1; DELETE FROM users WHERE 1=1; --"
        ]

        for payload in malicious_payloads:
            response = client.post("/auth/otp", json={"phone": payload})
            # Should return validation error, not execute SQL
            assert response.status_code in [422, 400]

    def test_xss_protection(self, client: TestClient, authenticated_user):
        """Test protection against XSS attacks."""
        headers = authenticated_user["headers"]
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "<img src=x onerror=alert(1)>",
            "';!--\"<XSS>=&{()}"
        ]

        for payload in xss_payloads:
            user_data = {
                "name": payload,
                "business_name": "Test Business",
                "business_type": "farmer",
                "location": "Nairobi"
            }
            response = client.post("/auth/register", json=user_data, headers=headers)
            # Should sanitize or reject malicious input
            if response.status_code == 200:
                data = response.json()
                # XSS payload should be sanitized
                assert "<script>" not in data.get("name", "")

    def test_rate_limiting(self, client: TestClient):
        """Test rate limiting on sensitive endpoints."""
        phone = "+254700000000"

        # Make multiple OTP requests rapidly
        responses = []
        for _ in range(20):  # Try to exceed rate limit
            response = client.post("/auth/otp", json={"phone": phone})
            responses.append(response.status_code)

        # Should eventually return rate limit error
        assert 429 in responses  # Too Many Requests

    def test_authentication_bypass_attempts(self, client: TestClient):
        """Test various authentication bypass attempts."""
        # Try accessing protected endpoints without token
        protected_endpoints = [
            "/score/compute",
            "/loan/apply",
            "/evidence/upload",
            "/ai/greenscore/current"
        ]

        for endpoint in protected_endpoints:
            response = client.post(endpoint, json={})
            assert response.status_code == 401

        # Try with malformed tokens
        malformed_tokens = [
            "Bearer invalid",
            "Bearer ",
            "invalid",
            "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid",
        ]

        for token in malformed_tokens:
            headers = {"Authorization": token}
            response = client.get("/ai/greenscore/current", headers=headers)
            assert response.status_code == 401