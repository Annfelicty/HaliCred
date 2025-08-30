"""
Comprehensive tests for HaliScore backend.

This module tests all major API endpoints and functionality.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.models import Base
from app.config import settings

# Create in-memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

class TestAuthentication:
    """Test authentication endpoints."""
    
    def test_send_otp(self):
        """Test OTP sending."""
        response = client.post("/auth/otp", json={"phone": "+254700000000"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sent"
        assert "message" in data
    
    def test_verify_otp_success(self):
        """Test successful OTP verification."""
        # First send OTP
        client.post("/auth/otp", json={"phone": "+254700000001"})
        
        # Verify with correct code (this will work in development)
        response = client.post("/auth/verify", json={
            "phone": "+254700000001",
            "code": "123456",
            "full_name": "Test User"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_verify_otp_invalid(self):
        """Test invalid OTP verification."""
        response = client.post("/auth/verify", json={
            "phone": "+254700000002",
            "code": "000000"
        })
        assert response.status_code == 400

class TestUserProfile:
    """Test user profile endpoints."""
    
    def test_get_me_without_auth(self):
        """Test getting user profile without authentication."""
        response = client.get("/me")
        assert response.status_code == 401
    
    def test_get_me_with_auth(self):
        """Test getting user profile with authentication."""
        # First authenticate
        client.post("/auth/otp", json={"phone": "+254700000003"})
        auth_response = client.post("/auth/verify", json={
            "phone": "+254700000003",
            "code": "123456",
            "full_name": "Test User"
        })
        token = auth_response.json()["access_token"]
        
        # Get profile
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "phone" in data
        assert "full_name" in data
    
    def test_update_profile(self):
        """Test profile update."""
        # First authenticate
        client.post("/auth/otp", json={"phone": "+254700000004"})
        auth_response = client.post("/auth/verify", json={
            "phone": "+254700000004",
            "code": "123456",
            "full_name": "Test User"
        })
        token = auth_response.json()["access_token"]
        
        # Update profile
        headers = {"Authorization": f"Bearer {token}"}
        response = client.patch("/me/profile", 
                              json={"business_type": "agriculture", "business_name": "Test Farm"},
                              headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["business_type"] == "agriculture"
        assert data["business_name"] == "Test Farm"

class TestEvidence:
    """Test evidence management endpoints."""
    
    def test_create_evidence(self):
        """Test evidence creation."""
        # First authenticate
        client.post("/auth/otp", json={"phone": "+254700000005"})
        auth_response = client.post("/auth/verify", json={
            "phone": "+254700000005",
            "code": "123456",
            "full_name": "Test User"
        })
        token = auth_response.json()["access_token"]
        
        # Create evidence
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/evidence", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "url" in data
        assert data["status"] == "pending"
    
    def test_list_evidence(self):
        """Test listing evidence."""
        # First authenticate
        client.post("/auth/otp", json={"phone": "+254700000006"})
        auth_response = client.post("/auth/verify", json={
            "phone": "+254700000006",
            "code": "123456",
            "full_name": "Test User"
        })
        token = auth_response.json()["access_token"]
        
        # List evidence
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/evidence", headers=headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

class TestScoring:
    """Test Green Score calculation endpoints."""
    
    def test_compute_score(self):
        """Test score computation."""
        # First authenticate
        client.post("/auth/otp", json={"phone": "+254700000007"})
        auth_response = client.post("/auth/verify", json={
            "phone": "+254700000007",
            "code": "123456",
            "full_name": "Test User"
        })
        token = auth_response.json()["access_token"]
        
        # Compute score
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/score/compute", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "score_raw" in data
        assert "score_0_100" in data
        assert "subscores" in data
    
    def test_get_score(self):
        """Test getting user score."""
        # First authenticate
        client.post("/auth/otp", json={"phone": "+254700000008"})
        auth_response = client.post("/auth/verify", json={
            "phone": "+254700000008",
            "code": "123456",
            "full_name": "Test User"
        })
        token = auth_response.json()["access_token"]
        
        # Get score
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/score/me", headers=headers)
        assert response.status_code == 200

class TestLoanManagement:
    """Test loan management endpoints."""
    
    def test_loan_quote(self):
        """Test loan quote generation."""
        # First authenticate
        client.post("/auth/otp", json={"phone": "+254700000009"})
        auth_response = client.post("/auth/verify", json={
            "phone": "+254700000009",
            "code": "123456",
            "full_name": "Test User"
        })
        token = auth_response.json()["access_token"]
        
        # Get loan quote
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/loan/quote", 
                              json={"amount": 10000, "tenor": 12},
                              headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "options" in data
        assert len(data["options"]) > 0
    
    def test_loan_apply(self):
        """Test loan application."""
        # First authenticate
        client.post("/auth/otp", json={"phone": "+254700000010"})
        auth_response = client.post("/auth/verify", json={
            "phone": "+254700000010",
            "code": "123456",
            "full_name": "Test User"
        })
        token = auth_response.json()["access_token"]
        
        # Apply for loan
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/loan/apply", 
                              json={"amount": 10000, "tenor": 12},
                              headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] == "submitted"

class TestHealthCheck:
    """Test health check endpoint."""
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "haliscore-backend"

# Import get_db for dependency override
from app.db import get_db
