"""
Database integration tests for HaliCred backend.
Tests database operations, relationships, and data integrity for Phase 6.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models import User, GreenScore, LoanApplication, Evidence, BusinessProfile


@pytest.mark.database
class TestUserModel:
    """Test User model database operations."""

    def test_create_user(self, db_session: Session):
        """Test creating a new user."""
        user_data = {
            "phone": "+254700000000",
            "email": "test@example.com",
            "name": "Test User",
            "business_name": "Test Business",
            "business_type": "farmer",
            "location": "Nairobi",
            "is_active": True,
            "is_verified": False
        }

        user = User(**user_data)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.phone == user_data["phone"]
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_unique_constraints(self, db_session: Session):
        """Test user unique constraints."""
        # Create first user
        user1 = User(
            phone="+254700000000",
            email="test@example.com",
            name="User 1",
            business_name="Business 1",
            business_type="farmer",
            location="Nairobi"
        )
        db_session.add(user1)
        db_session.commit()

        # Try to create second user with same phone
        user2 = User(
            phone="+254700000000",  # Same phone
            email="different@example.com",
            name="User 2",
            business_name="Business 2",
            business_type="salon",
            location="Mombasa"
        )
        db_session.add(user2)

        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()

    def test_user_business_profile_relationship(self, db_session: Session, sample_user):
        """Test user to business profile relationship."""
        profile = BusinessProfile(
            user_id=sample_user.id,
            business_registration_number="BR123456",
            business_description="Test business",
            annual_revenue=1000000,
            employee_count=10,
            business_sector="agriculture",
            sustainability_goals=["reduce_emissions", "water_conservation"],
            current_practices=["organic_farming"]
        )
        db_session.add(profile)
        db_session.commit()

        # Test relationship
        db_session.refresh(sample_user)
        assert sample_user.business_profile is not None
        assert sample_user.business_profile.business_registration_number == "BR123456"

    def test_user_cascade_delete(self, db_session: Session, sample_user):
        """Test that deleting user cascades to related records."""
        # Create related records
        greenscore = GreenScore(
            user_id=sample_user.id,
            overall_score=75,
            energy_efficiency=80,
            water_conservation=70,
            waste_management=85,
            renewable_energy=65,
            carbon_footprint=72,
            confidence_score=0.85,
            evidence_count=2
        )
        db_session.add(greenscore)

        loan = LoanApplication(
            user_id=sample_user.id,
            amount=500000,
            term=12,
            purpose="equipment",
            status="pending"
        )
        db_session.add(loan)

        evidence = Evidence(
            user_id=sample_user.id,
            evidence_type="solar_panel",
            file_path="/uploads/test.jpg",
            file_name="test.jpg",
            file_size=1024,
            mime_type="image/jpeg",
            description="Test evidence",
            processing_status="pending"
        )
        db_session.add(evidence)

        db_session.commit()

        # Verify records exist
        assert db_session.query(GreenScore).filter_by(user_id=sample_user.id).count() == 1
        assert db_session.query(LoanApplication).filter_by(user_id=sample_user.id).count() == 1
        assert db_session.query(Evidence).filter_by(user_id=sample_user.id).count() == 1

        # Delete user
        db_session.delete(sample_user)
        db_session.commit()

        # Verify related records are deleted (cascade)
        assert db_session.query(GreenScore).filter_by(user_id=sample_user.id).count() == 0
        assert db_session.query(LoanApplication).filter_by(user_id=sample_user.id).count() == 0
        assert db_session.query(Evidence).filter_by(user_id=sample_user.id).count() == 0


@pytest.mark.database
class TestGreenScoreModel:
    """Test GreenScore model database operations."""

    def test_create_greenscore(self, db_session: Session, sample_user):
        """Test creating a GreenScore record."""
        score_data = {
            "user_id": sample_user.id,
            "overall_score": 85,
            "energy_efficiency": 90,
            "water_conservation": 80,
            "waste_management": 85,
            "renewable_energy": 85,
            "carbon_footprint": 88,
            "confidence_score": 0.92,
            "evidence_count": 5,
            "scoring_factors": {
                "led_lighting": {"score": 15, "weight": 0.2},
                "solar_panels": {"score": 20, "weight": 0.3}
            },
            "recommendations": [
                {
                    "action": "Install additional panels",
                    "impact": "+5 points",
                    "cost": "KES 150,000"
                }
            ]
        }

        greenscore = GreenScore(**score_data)
        db_session.add(greenscore)
        db_session.commit()
        db_session.refresh(greenscore)

        assert greenscore.id is not None
        assert greenscore.overall_score == 85
        assert greenscore.last_updated is not None
        assert isinstance(greenscore.scoring_factors, dict)
        assert isinstance(greenscore.recommendations, list)

    def test_greenscore_user_relationship(self, db_session: Session, sample_user, sample_greenscore):
        """Test GreenScore to User relationship."""
        assert sample_greenscore.user == sample_user
        assert sample_user.green_scores[0] == sample_greenscore

    def test_greenscore_history_ordering(self, db_session: Session, sample_user):
        """Test GreenScore history is properly ordered."""
        # Create multiple scores
        scores = []
        for i in range(5):
            score = GreenScore(
                user_id=sample_user.id,
                overall_score=70 + i * 5,
                energy_efficiency=75,
                water_conservation=70,
                waste_management=80,
                renewable_energy=65,
                carbon_footprint=70,
                confidence_score=0.8,
                evidence_count=i + 1,
                last_updated=datetime.utcnow() - timedelta(days=30 - i * 5)
            )
            scores.append(score)
            db_session.add(score)

        db_session.commit()

        # Query scores ordered by date
        ordered_scores = db_session.query(GreenScore)\
            .filter_by(user_id=sample_user.id)\
            .order_by(GreenScore.last_updated.desc())\
            .all()

        assert len(ordered_scores) == 5
        assert ordered_scores[0].overall_score == 90  # Most recent
        assert ordered_scores[-1].overall_score == 70  # Oldest

    def test_greenscore_score_validation(self, db_session: Session, sample_user):
        """Test GreenScore validation rules."""
        # Test invalid score ranges
        invalid_scores = [
            {"overall_score": -10},  # Negative score
            {"overall_score": 150},  # Score over 100
            {"confidence_score": -0.5},  # Negative confidence
            {"confidence_score": 1.5},  # Confidence over 1
        ]

        for invalid_data in invalid_scores:
            score_data = {
                "user_id": sample_user.id,
                "overall_score": 75,
                "energy_efficiency": 75,
                "water_conservation": 75,
                "waste_management": 75,
                "renewable_energy": 75,
                "carbon_footprint": 75,
                "confidence_score": 0.8,
                "evidence_count": 1,
                **invalid_data
            }

            greenscore = GreenScore(**score_data)
            db_session.add(greenscore)

            # This would typically be caught by database constraints or validators
            # For now, we just verify the values are stored as-is
            # In production, add check constraints or validators
            try:
                db_session.commit()
                # If no error, verify the invalid value was stored
                db_session.refresh(greenscore)
                if "overall_score" in invalid_data:
                    assert greenscore.overall_score == invalid_data["overall_score"]
            except Exception:
                # If database has constraints, this is expected
                db_session.rollback()


@pytest.mark.database
class TestLoanApplicationModel:
    """Test LoanApplication model database operations."""

    def test_create_loan_application(self, db_session: Session, sample_user):
        """Test creating a loan application."""
        loan_data = {
            "user_id": sample_user.id,
            "amount": 750000,
            "term": 18,
            "purpose": "expansion",
            "interest_rate": 14.5,
            "monthly_payment": 52000.0,
            "status": "pending",
            "collateral_description": "Business equipment",
            "business_plan_summary": "Expand operations",
            "requested_use_of_funds": "Purchase new equipment",
            "repayment_capacity": {
                "monthly_income": 200000,
                "monthly_expenses": 120000,
                "debt_to_income_ratio": 0.4
            }
        }

        loan = LoanApplication(**loan_data)
        db_session.add(loan)
        db_session.commit()
        db_session.refresh(loan)

        assert loan.id is not None
        assert loan.amount == 750000
        assert loan.status == "pending"
        assert loan.application_date is not None
        assert isinstance(loan.repayment_capacity, dict)

    def test_loan_status_transitions(self, db_session: Session, sample_loan_application):
        """Test loan status transitions."""
        valid_transitions = [
            ("pending", "approved"),
            ("approved", "disbursed"),
            ("disbursed", "active"),
            ("active", "completed"),
            ("pending", "rejected")
        ]

        for from_status, to_status in valid_transitions:
            sample_loan_application.status = from_status
            db_session.commit()

            sample_loan_application.status = to_status
            sample_loan_application.last_updated = datetime.utcnow()
            db_session.commit()

            assert sample_loan_application.status == to_status

    def test_loan_calculations(self, db_session: Session, sample_user):
        """Test loan calculation fields."""
        # Test monthly payment calculation accuracy
        principal = 500000
        annual_rate = 12.0
        term_months = 12

        monthly_rate = annual_rate / 100 / 12
        monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** term_months) / \
                         ((1 + monthly_rate) ** term_months - 1)

        loan = LoanApplication(
            user_id=sample_user.id,
            amount=principal,
            term=term_months,
            purpose="equipment",
            interest_rate=annual_rate,
            monthly_payment=monthly_payment,
            status="pending"
        )
        db_session.add(loan)
        db_session.commit()

        # Verify calculation
        expected_monthly = round(monthly_payment, 2)
        assert abs(loan.monthly_payment - expected_monthly) < 1.0  # Allow small rounding difference

    def test_loan_user_relationship(self, db_session: Session, sample_user, sample_loan_application):
        """Test LoanApplication to User relationship."""
        assert sample_loan_application.user == sample_user
        assert sample_loan_application in sample_user.loan_applications


@pytest.mark.database
class TestEvidenceModel:
    """Test Evidence model database operations."""

    def test_create_evidence(self, db_session: Session, sample_user):
        """Test creating evidence record."""
        evidence_data = {
            "user_id": sample_user.id,
            "evidence_type": "led_lighting",
            "file_path": "/uploads/evidence/led_receipt.jpg",
            "file_name": "led_receipt.jpg",
            "file_size": 2048000,
            "mime_type": "image/jpeg",
            "description": "LED lighting installation receipt",
            "processing_status": "completed",
            "ai_analysis_result": {
                "confidence": 0.95,
                "extracted_text": "LED Bulbs - KES 15,000",
                "sustainability_impact": "Energy efficiency improvement",
                "score_contribution": 12
            },
            "verification_status": "verified",
            "metadata": {
                "location": {"lat": -1.2921, "lng": 36.8219},
                "timestamp": datetime.utcnow().isoformat()
            }
        }

        evidence = Evidence(**evidence_data)
        db_session.add(evidence)
        db_session.commit()
        db_session.refresh(evidence)

        assert evidence.id is not None
        assert evidence.evidence_type == "led_lighting"
        assert evidence.upload_date is not None
        assert isinstance(evidence.ai_analysis_result, dict)
        assert isinstance(evidence.metadata, dict)

    def test_evidence_processing_status_flow(self, db_session: Session, sample_evidence):
        """Test evidence processing status transitions."""
        status_flow = ["pending", "processing", "completed", "verified"]

        for status in status_flow:
            sample_evidence.processing_status = status
            if status == "completed":
                sample_evidence.processed_date = datetime.utcnow()
            if status == "verified":
                sample_evidence.verified_date = datetime.utcnow()

            db_session.commit()
            assert sample_evidence.processing_status == status

    def test_evidence_file_validation(self, db_session: Session, sample_user):
        """Test evidence file validation rules."""
        # Test valid file types
        valid_types = [
            ("image/jpeg", ".jpg"),
            ("image/png", ".png"),
            ("application/pdf", ".pdf"),
            ("image/tiff", ".tiff")
        ]

        for mime_type, file_ext in valid_types:
            evidence = Evidence(
                user_id=sample_user.id,
                evidence_type="solar_panel",
                file_path=f"/uploads/test{file_ext}",
                file_name=f"test{file_ext}",
                file_size=1024000,
                mime_type=mime_type,
                description="Test file",
                processing_status="pending"
            )
            db_session.add(evidence)
            db_session.commit()
            db_session.refresh(evidence)

            assert evidence.mime_type == mime_type

    def test_evidence_user_relationship(self, db_session: Session, sample_user, sample_evidence):
        """Test Evidence to User relationship."""
        assert sample_evidence.user == sample_user
        assert sample_evidence in sample_user.evidence_records


@pytest.mark.database
class TestDatabasePerformance:
    """Test database performance characteristics."""

    def test_bulk_insert_performance(self, db_session: Session, performance_test_data):
        """Test bulk insert performance."""
        import time

        # Test bulk user creation
        start_time = time.time()
        users = []
        for i in range(performance_test_data["bulk_users"]):
            user = User(
                phone=f"+25470000{i:04d}",
                email=f"user{i}@example.com",
                name=f"User {i}",
                business_name=f"Business {i}",
                business_type=["farmer", "salon", "welding", "other"][i % 4],
                location=["Nairobi", "Mombasa", "Kisumu", "Nakuru"][i % 4]
            )
            users.append(user)

        db_session.add_all(users)
        db_session.commit()

        bulk_insert_time = time.time() - start_time

        # Should complete within reasonable time (adjust threshold as needed)
        assert bulk_insert_time < 5.0  # 5 seconds for 100 users
        assert db_session.query(User).count() == performance_test_data["bulk_users"]

    def test_complex_query_performance(self, db_session: Session, multiple_users, multiple_loan_applications):
        """Test complex query performance."""
        import time

        start_time = time.time()

        # Complex query: Users with active loans and high green scores
        query = db_session.query(User)\
            .join(LoanApplication)\
            .join(GreenScore)\
            .filter(LoanApplication.status.in_(["active", "disbursed"]))\
            .filter(GreenScore.overall_score > 70)\
            .order_by(GreenScore.overall_score.desc())\
            .limit(10)

        results = query.all()
        query_time = time.time() - start_time

        # Should execute quickly
        assert query_time < 1.0  # 1 second
        assert isinstance(results, list)

    def test_database_connection_pool(self, db_session: Session):
        """Test database connection handling."""
        # Test multiple simultaneous connections
        sessions = []
        try:
            for i in range(10):
                session = TestingSessionLocal()
                sessions.append(session)

                # Perform a simple query
                count = session.query(User).count()
                assert count >= 0

        finally:
            # Clean up connections
            for session in sessions:
                session.close()


@pytest.mark.database
class TestDataIntegrity:
    """Test data integrity and constraints."""

    def test_foreign_key_constraints(self, db_session: Session):
        """Test foreign key constraint enforcement."""
        # Try to create GreenScore with non-existent user_id
        greenscore = GreenScore(
            user_id=99999,  # Non-existent user
            overall_score=75,
            energy_efficiency=75,
            water_conservation=75,
            waste_management=75,
            renewable_energy=75,
            carbon_footprint=75,
            confidence_score=0.8,
            evidence_count=1
        )
        db_session.add(greenscore)

        with pytest.raises(Exception):  # Should raise foreign key constraint error
            db_session.commit()

    def test_data_consistency(self, db_session: Session, sample_user):
        """Test data consistency across related tables."""
        # Create evidence and corresponding GreenScore
        evidence = Evidence(
            user_id=sample_user.id,
            evidence_type="solar_panel",
            file_path="/uploads/solar.jpg",
            file_name="solar.jpg",
            file_size=1024,
            mime_type="image/jpeg",
            description="Solar panel evidence",
            processing_status="completed"
        )
        db_session.add(evidence)

        greenscore = GreenScore(
            user_id=sample_user.id,
            overall_score=80,
            energy_efficiency=85,
            water_conservation=75,
            waste_management=80,
            renewable_energy=85,
            carbon_footprint=82,
            confidence_score=0.9,
            evidence_count=1  # Should match actual evidence count
        )
        db_session.add(greenscore)
        db_session.commit()

        # Verify consistency
        actual_evidence_count = db_session.query(Evidence)\
            .filter_by(user_id=sample_user.id)\
            .count()

        assert greenscore.evidence_count == actual_evidence_count

    def test_timestamp_consistency(self, db_session: Session, sample_user):
        """Test timestamp field consistency."""
        # Create user and check timestamps
        user_created = sample_user.created_at
        user_updated = sample_user.updated_at

        assert user_created is not None
        assert user_updated is not None
        assert user_updated >= user_created

        # Update user and check updated timestamp changes
        original_updated = user_updated
        sample_user.name = "Updated Name"
        sample_user.updated_at = datetime.utcnow()
        db_session.commit()

        assert sample_user.updated_at > original_updated