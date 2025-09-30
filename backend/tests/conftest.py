"""
Test configuration and fixtures for HaliCred backend tests.
Provides comprehensive test infrastructure for Phase 6 testing requirements.
"""

import pytest
import asyncio
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Generator, Dict, Any
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db import Base, get_db
from app.db.models import User, GreenScore, LoanApplication, Evidence, BusinessProfile
from app.auth import create_token
from app.config import settings

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
Base.metadata.create_all(bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    """Override database dependency for tests."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override dependencies
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a database session for testing."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client() -> TestClient:
    """Create a test client."""
    return TestClient(app)


@pytest.fixture(scope="function")
def temp_upload_dir() -> Generator[Path, None, None]:
    """Create temporary directory for file uploads."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


# User fixtures
@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Sample user data for testing."""
    return {
        "phone": "+254700000001",
        "email": "test@example.com",
        "name": "John Doe",
        "business_name": "Doe Enterprises",
        "business_type": "farmer",
        "location": "Nairobi",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_active": True,
        "is_verified": True
    }


@pytest.fixture
def sample_user(db_session: Session, sample_user_data: Dict[str, Any]) -> User:
    """Create a sample user in the database."""
    user = User(**sample_user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_user_with_profile(db_session: Session, sample_user: User) -> User:
    """Create a sample user with business profile."""
    profile = BusinessProfile(
        user_id=sample_user.id,
        business_registration_number="BR123456",
        business_description="Sustainable farming operations",
        annual_revenue=1000000,
        employee_count=5,
        business_sector="agriculture",
        sustainability_goals=["reduce_emissions", "water_conservation"],
        current_practices=["organic_farming", "drip_irrigation"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(sample_user)
    return sample_user


@pytest.fixture
def authenticated_user(sample_user: User) -> Dict[str, Any]:
    """Create an authenticated user with token."""
    token = create_token({"sub": str(sample_user.id)})
    return {
        "user": sample_user,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"}
    }


# GreenScore fixtures
@pytest.fixture
def sample_greenscore_data() -> Dict[str, Any]:
    """Sample GreenScore data for testing."""
    return {
        "overall_score": 75,
        "energy_efficiency": 80,
        "water_conservation": 70,
        "waste_management": 85,
        "renewable_energy": 65,
        "carbon_footprint": 72,
        "confidence_score": 0.85,
        "evidence_count": 5,
        "last_updated": datetime.utcnow(),
        "scoring_factors": {
            "led_lighting": {"score": 15, "weight": 0.2},
            "solar_panels": {"score": 20, "weight": 0.3},
            "water_recycling": {"score": 18, "weight": 0.25}
        },
        "recommendations": [
            {
                "action": "Install additional solar panels",
                "potential_impact": "+5 score points",
                "estimated_cost": "KES 150,000",
                "payback_period": "18 months"
            }
        ]
    }


@pytest.fixture
def sample_greenscore(db_session: Session, sample_user: User, sample_greenscore_data: Dict[str, Any]) -> GreenScore:
    """Create a sample GreenScore in the database."""
    greenscore = GreenScore(
        user_id=sample_user.id,
        **sample_greenscore_data
    )
    db_session.add(greenscore)
    db_session.commit()
    db_session.refresh(greenscore)
    return greenscore


# Loan application fixtures
@pytest.fixture
def sample_loan_data() -> Dict[str, Any]:
    """Sample loan application data for testing."""
    return {
        "amount": 500000,
        "term": 12,
        "purpose": "equipment",
        "interest_rate": 12.5,
        "monthly_payment": 44471.0,
        "status": "pending",
        "application_date": datetime.utcnow(),
        "last_updated": datetime.utcnow(),
        "collateral_description": "Farm equipment and land title",
        "business_plan_summary": "Expand sustainable farming operations",
        "requested_use_of_funds": "Purchase organic fertilizers and irrigation equipment",
        "repayment_capacity": {
            "monthly_income": 150000,
            "monthly_expenses": 80000,
            "debt_to_income_ratio": 0.3
        }
    }


@pytest.fixture
def sample_loan_application(db_session: Session, sample_user: User, sample_loan_data: Dict[str, Any]) -> LoanApplication:
    """Create a sample loan application in the database."""
    loan = LoanApplication(
        user_id=sample_user.id,
        **sample_loan_data
    )
    db_session.add(loan)
    db_session.commit()
    db_session.refresh(loan)
    return loan


# Evidence fixtures
@pytest.fixture
def sample_evidence_data() -> Dict[str, Any]:
    """Sample evidence data for testing."""
    return {
        "evidence_type": "solar_panel",
        "file_path": "/uploads/evidence/solar_panel_receipt.jpg",
        "file_name": "solar_panel_receipt.jpg",
        "file_size": 1024000,
        "mime_type": "image/jpeg",
        "description": "Receipt for solar panel installation",
        "upload_date": datetime.utcnow(),
        "processing_status": "completed",
        "ai_analysis_result": {
            "confidence": 0.92,
            "extracted_text": "Solar Panel System - KES 200,000",
            "sustainability_impact": "High - Renewable energy adoption",
            "score_contribution": 15
        },
        "verification_status": "verified",
        "verified_date": datetime.utcnow(),
        "metadata": {
            "coordinates": {"lat": -1.2921, "lng": 36.8219},
            "timestamp": datetime.utcnow().isoformat(),
            "device_info": "iPhone 12 Pro"
        }
    }


@pytest.fixture
def sample_evidence(db_session: Session, sample_user: User, sample_evidence_data: Dict[str, Any]) -> Evidence:
    """Create a sample evidence record in the database."""
    evidence = Evidence(
        user_id=sample_user.id,
        **sample_evidence_data
    )
    db_session.add(evidence)
    db_session.commit()
    db_session.refresh(evidence)
    return evidence


# Mock external services
@pytest.fixture
def mock_redis():
    """Mock Redis for testing."""
    with patch('app.auth.redis_client') as mock:
        mock.get.return_value = None
        mock.set.return_value = True
        mock.delete.return_value = True
        mock.exists.return_value = False
        yield mock


@pytest.fixture
def mock_minio():
    """Mock MinIO for testing."""
    with patch('app.services.minio_client') as mock:
        mock.put_object.return_value = None
        mock.get_object.return_value = Mock()
        mock.bucket_exists.return_value = True
        yield mock


@pytest.fixture
def mock_gemini_api():
    """Mock Gemini API for testing."""
    mock_response = {
        "confidence": 0.85,
        "analysis": "Solar panel installation receipt verified",
        "score_impact": 15,
        "recommendations": ["Consider additional panels for optimal efficiency"]
    }

    with patch('app.ai.orchestrator.process_with_gemini') as mock:
        mock.return_value = mock_response
        yield mock


@pytest.fixture
def mock_vision_api():
    """Mock Google Vision API for testing."""
    mock_response = {
        "text_annotations": [
            {"description": "Solar Panel System Invoice\nAmount: KES 200,000\nDate: 2024-01-15"}
        ],
        "full_text_annotation": {
            "text": "Solar Panel System Invoice\nAmount: KES 200,000\nDate: 2024-01-15"
        }
    }

    with patch('app.ai.evidence_processor.vision_client') as mock:
        mock.text_detection.return_value = mock_response
        yield mock


@pytest.fixture
def mock_climatiq_api():
    """Mock Climatiq API for testing."""
    mock_response = {
        "co2e": 2.5,
        "co2e_unit": "tonnes",
        "activity_data": {"value": 1000, "unit": "kWh"},
        "emission_factor": {
            "activity_id": "electricity-energy_source_grid_mix",
            "data_version": "v2024.1"
        }
    }

    with patch('app.ai.emission_calculator.climatiq_client') as mock:
        mock.estimate_emissions.return_value = mock_response
        yield mock


# Test data collections
@pytest.fixture
def multiple_users(db_session: Session) -> list[User]:
    """Create multiple test users."""
    users = []
    for i in range(5):
        user_data = {
            "phone": f"+25470000000{i}",
            "email": f"user{i}@example.com",
            "name": f"User {i}",
            "business_name": f"Business {i}",
            "business_type": ["farmer", "salon", "welding", "other"][i % 4],
            "location": ["Nairobi", "Mombasa", "Kisumu", "Nakuru"][i % 4],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True,
            "is_verified": True
        }
        user = User(**user_data)
        db_session.add(user)
        users.append(user)

    db_session.commit()
    for user in users:
        db_session.refresh(user)

    return users


@pytest.fixture
def multiple_loan_applications(db_session: Session, multiple_users: list[User]) -> list[LoanApplication]:
    """Create multiple loan applications with different statuses."""
    statuses = ["pending", "approved", "disbursed", "completed", "rejected"]
    loans = []

    for i, user in enumerate(multiple_users):
        loan_data = {
            "user_id": user.id,
            "amount": 100000 * (i + 1),
            "term": 6 + (i * 6),
            "purpose": ["equipment", "expansion", "inventory", "working_capital"][i % 4],
            "interest_rate": 10.0 + (i * 2),
            "status": statuses[i % len(statuses)],
            "application_date": datetime.utcnow() - timedelta(days=i * 10),
            "last_updated": datetime.utcnow() - timedelta(days=i * 5)
        }
        loan = LoanApplication(**loan_data)
        db_session.add(loan)
        loans.append(loan)

    db_session.commit()
    for loan in loans:
        db_session.refresh(loan)

    return loans


# Performance testing fixtures
@pytest.fixture
def performance_test_data():
    """Generate large dataset for performance testing."""
    return {
        "bulk_users": 100,
        "bulk_evidence": 500,
        "bulk_scores": 200,
        "bulk_loans": 150
    }


# Error scenario fixtures
@pytest.fixture
def invalid_user_data():
    """Invalid user data for error testing."""
    return [
        {"phone": "invalid"},  # Invalid phone format
        {"email": "invalid-email"},  # Invalid email format
        {"name": ""},  # Empty name
        {"business_type": "invalid"},  # Invalid business type
        {},  # Missing required fields
    ]


@pytest.fixture
def invalid_loan_data():
    """Invalid loan data for error testing."""
    return [
        {"amount": -1000},  # Negative amount
        {"term": 0},  # Zero term
        {"purpose": ""},  # Empty purpose
        {"amount": "invalid"},  # Invalid amount type
        {},  # Missing required fields
    ]


# Async testing support
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Test utilities
@pytest.fixture
def api_headers():
    """Standard API headers for testing."""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }


@pytest.fixture
def file_upload_headers():
    """Headers for file upload testing."""
    return {
        "Accept": "application/json"
        # Content-Type will be set automatically for multipart uploads
    }


# Database state management
@pytest.fixture(autouse=True)
def clean_database(db_session: Session):
    """Clean database before each test."""
    # This fixture runs automatically before each test
    # Truncate all tables to ensure clean state
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(table.delete())
    db_session.commit()

    yield

    # Clean up after test
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(table.delete())
    db_session.commit()


# Test markers for categorization
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "security: Security tests")
    config.addinivalue_line("markers", "auth: Authentication tests")
    config.addinivalue_line("markers", "api: API endpoint tests")
    config.addinivalue_line("markers", "database: Database tests")
    config.addinivalue_line("markers", "ai: AI processing tests")
    config.addinivalue_line("markers", "slow: Slow running tests")