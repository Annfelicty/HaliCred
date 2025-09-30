"""
Comprehensive loan application and management tests for HaliCred backend.
Tests loan application flow, eligibility, approval process, and financial calculations.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, Mock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import LoanApplication, User, GreenScore
from app.api.loans import calculate_loan_terms, assess_loan_eligibility


@pytest.mark.api
@pytest.mark.loans
class TestLoanApplicationAPI:
    """Test loan application API endpoints."""

    def test_create_loan_application_success(self, client: TestClient, authenticated_user):
        """Test successful loan application creation."""
        headers = authenticated_user["headers"]

        loan_data = {
            "amount": 500000,
            "term": 12,
            "purpose": "equipment",
            "collateral_description": "Farm equipment",
            "business_plan_summary": "Expand farming operations",
            "requested_use_of_funds": "Purchase new irrigation system"
        }

        response = client.post("/loans/apply", json=loan_data, headers=headers)

        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == 500000
        assert data["term"] == 12
        assert data["purpose"] == "equipment"
        assert data["status"] == "pending"
        assert "application_id" in data
        assert "monthly_payment" in data
        assert "interest_rate" in data

    def test_create_loan_application_invalid_amount(self, client: TestClient, authenticated_user):
        """Test loan application with invalid amount."""
        headers = authenticated_user["headers"]

        invalid_amounts = [0, -1000, 10000000]  # Zero, negative, too large

        for amount in invalid_amounts:
            loan_data = {
                "amount": amount,
                "term": 12,
                "purpose": "equipment"
            }

            response = client.post("/loans/apply", json=loan_data, headers=headers)
            assert response.status_code == 400

    def test_create_loan_application_invalid_term(self, client: TestClient, authenticated_user):
        """Test loan application with invalid term."""
        headers = authenticated_user["headers"]

        invalid_terms = [0, -6, 61]  # Zero, negative, too long

        for term in invalid_terms:
            loan_data = {
                "amount": 500000,
                "term": term,
                "purpose": "equipment"
            }

            response = client.post("/loans/apply", json=loan_data, headers=headers)
            assert response.status_code == 400

    def test_get_loan_applications_list(self, client: TestClient, authenticated_user, sample_loan_application):
        """Test retrieving user's loan applications."""
        headers = authenticated_user["headers"]

        response = client.get("/loans/my-loans", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(loan["id"] == sample_loan_application.id for loan in data)

    def test_get_specific_loan_application(self, client: TestClient, authenticated_user, sample_loan_application):
        """Test retrieving specific loan application."""
        headers = authenticated_user["headers"]

        response = client.get(f"/loans/{sample_loan_application.id}", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_loan_application.id
        assert data["amount"] == sample_loan_application.amount
        assert data["status"] == sample_loan_application.status

    def test_get_loan_application_unauthorized(self, client: TestClient, sample_loan_application):
        """Test accessing loan application without authentication."""
        response = client.get(f"/loans/{sample_loan_application.id}")

        assert response.status_code == 401

    def test_get_other_user_loan_application(self, client: TestClient, authenticated_user,
                                           sample_loan_application, multiple_users, db_session):
        """Test accessing another user's loan application."""
        headers = authenticated_user["headers"]

        # Create loan for different user
        other_user = multiple_users[1]
        other_loan = LoanApplication(
            user_id=other_user.id,
            amount=300000,
            term=6,
            purpose="expansion",
            status="pending"
        )
        db_session.add(other_loan)
        db_session.commit()

        response = client.get(f"/loans/{other_loan.id}", headers=headers)

        assert response.status_code == 403  # Forbidden

    def test_update_loan_application(self, client: TestClient, authenticated_user,
                                   sample_loan_application, db_session):
        """Test updating loan application."""
        headers = authenticated_user["headers"]

        # Only pending loans should be updatable
        sample_loan_application.status = "pending"
        db_session.commit()

        update_data = {
            "amount": 600000,
            "term": 18,
            "business_plan_summary": "Updated business plan"
        }

        response = client.put(f"/loans/{sample_loan_application.id}",
                            json=update_data, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 600000
        assert data["term"] == 18

    def test_update_approved_loan_application(self, client: TestClient, authenticated_user,
                                            sample_loan_application, db_session):
        """Test updating approved loan application should fail."""
        headers = authenticated_user["headers"]

        sample_loan_application.status = "approved"
        db_session.commit()

        update_data = {"amount": 600000}

        response = client.put(f"/loans/{sample_loan_application.id}",
                            json=update_data, headers=headers)

        assert response.status_code == 400  # Cannot update approved loans

    def test_cancel_loan_application(self, client: TestClient, authenticated_user,
                                   sample_loan_application):
        """Test canceling loan application."""
        headers = authenticated_user["headers"]

        response = client.delete(f"/loans/{sample_loan_application.id}", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"


@pytest.mark.loans
class TestLoanEligibilityAssessment:
    """Test loan eligibility assessment logic."""

    def test_assess_eligibility_with_high_green_score(self, sample_user, db_session):
        """Test eligibility assessment with high green score."""
        # Create high green score
        high_score = GreenScore(
            user_id=sample_user.id,
            overall_score=85,
            confidence_score=0.9,
            evidence_count=5
        )
        db_session.add(high_score)
        db_session.commit()

        eligibility = assess_loan_eligibility(sample_user.id, 500000, db_session)

        assert eligibility["eligible"] is True
        assert eligibility["max_amount"] >= 500000
        assert eligibility["interest_rate"] <= 15.0  # Should get better rate
        assert "green_score_bonus" in eligibility["factors"]

    def test_assess_eligibility_with_low_green_score(self, sample_user, db_session):
        """Test eligibility assessment with low green score."""
        # Create low green score
        low_score = GreenScore(
            user_id=sample_user.id,
            overall_score=30,
            confidence_score=0.5,
            evidence_count=1
        )
        db_session.add(low_score)
        db_session.commit()

        eligibility = assess_loan_eligibility(sample_user.id, 500000, db_session)

        assert eligibility["eligible"] is False or eligibility["max_amount"] < 500000
        assert eligibility["interest_rate"] >= 18.0  # Higher rate due to low score

    def test_assess_eligibility_no_green_score(self, sample_user, db_session):
        """Test eligibility assessment without green score."""
        eligibility = assess_loan_eligibility(sample_user.id, 300000, db_session)

        assert eligibility["eligible"] is False
        assert "no_green_score" in eligibility["reasons"]

    def test_assess_eligibility_new_user(self, sample_user, db_session):
        """Test eligibility for newly registered user."""
        # User created today
        sample_user.created_at = datetime.utcnow()
        db_session.commit()

        eligibility = assess_loan_eligibility(sample_user.id, 200000, db_session)

        assert eligibility["max_amount"] <= 200000  # Limited for new users
        assert "new_user" in eligibility["factors"]

    def test_assess_eligibility_repeat_borrower(self, sample_user, db_session):
        """Test eligibility for user with loan history."""
        # Create completed loan history
        completed_loan = LoanApplication(
            user_id=sample_user.id,
            amount=300000,
            term=12,
            status="completed",
            application_date=datetime.utcnow() - timedelta(days=400)
        )
        db_session.add(completed_loan)

        # Add decent green score
        score = GreenScore(
            user_id=sample_user.id,
            overall_score=70,
            confidence_score=0.8,
            evidence_count=3
        )
        db_session.add(score)
        db_session.commit()

        eligibility = assess_loan_eligibility(sample_user.id, 500000, db_session)

        assert eligibility["eligible"] is True
        assert "repeat_borrower_bonus" in eligibility["factors"]

    def test_assess_eligibility_active_loan(self, sample_user, db_session):
        """Test eligibility when user has active loan."""
        # Create active loan
        active_loan = LoanApplication(
            user_id=sample_user.id,
            amount=400000,
            term=12,
            status="disbursed",
            application_date=datetime.utcnow() - timedelta(days=30)
        )
        db_session.add(active_loan)
        db_session.commit()

        eligibility = assess_loan_eligibility(sample_user.id, 300000, db_session)

        assert eligibility["eligible"] is False
        assert "active_loan" in eligibility["reasons"]

    def test_assess_eligibility_excessive_amount(self, sample_user, db_session):
        """Test eligibility for excessive loan amount."""
        # Add high green score
        high_score = GreenScore(
            user_id=sample_user.id,
            overall_score=90,
            confidence_score=0.95,
            evidence_count=8
        )
        db_session.add(high_score)
        db_session.commit()

        # Request excessive amount
        eligibility = assess_loan_eligibility(sample_user.id, 5000000, db_session)

        assert eligibility["eligible"] is False or eligibility["max_amount"] < 5000000
        assert "amount_too_high" in eligibility["reasons"]


@pytest.mark.loans
class TestLoanCalculations:
    """Test loan financial calculations."""

    def test_calculate_monthly_payment(self):
        """Test monthly payment calculation."""
        from app.api.loans import calculate_monthly_payment

        # Standard loan terms
        principal = 500000
        annual_rate = 12.0
        term_months = 12

        payment = calculate_monthly_payment(principal, annual_rate, term_months)

        assert payment > 0
        assert payment < principal  # Should be less than principal
        assert isinstance(payment, (int, float, Decimal))

        # Verify calculation is reasonable (approximate check)
        expected_range = (40000, 50000)  # Expected range for these terms
        assert expected_range[0] <= payment <= expected_range[1]

    def test_calculate_total_interest(self):
        """Test total interest calculation."""
        from app.api.loans import calculate_total_interest

        principal = 500000
        annual_rate = 12.0
        term_months = 12

        total_interest = calculate_total_interest(principal, annual_rate, term_months)

        assert total_interest > 0
        assert total_interest < principal  # Interest should be less than principal for 1 year

    def test_calculate_loan_terms_with_green_score_discount(self, sample_user, db_session):
        """Test loan terms calculation with green score discount."""
        # High green score for discount
        high_score = GreenScore(
            user_id=sample_user.id,
            overall_score=85,
            confidence_score=0.9,
            evidence_count=5
        )
        db_session.add(high_score)
        db_session.commit()

        terms = calculate_loan_terms(sample_user.id, 500000, 12, db_session)

        assert terms["interest_rate"] < 18.0  # Should get discount
        assert "green_score_discount" in terms["rate_factors"]
        assert terms["monthly_payment"] > 0

    def test_calculate_loan_terms_high_risk(self, sample_user, db_session):
        """Test loan terms calculation for high-risk profile."""
        # Low green score
        low_score = GreenScore(
            user_id=sample_user.id,
            overall_score=40,
            confidence_score=0.6,
            evidence_count=1
        )
        db_session.add(low_score)
        db_session.commit()

        terms = calculate_loan_terms(sample_user.id, 300000, 12, db_session)

        assert terms["interest_rate"] >= 18.0  # Higher rate for risk
        assert "risk_premium" in terms["rate_factors"]

    def test_loan_amortization_schedule(self):
        """Test loan amortization schedule generation."""
        from app.api.loans import generate_amortization_schedule

        principal = 500000
        annual_rate = 12.0
        term_months = 6  # Short term for testing

        schedule = generate_amortization_schedule(principal, annual_rate, term_months)

        assert len(schedule) == term_months
        assert all("payment_number" in payment for payment in schedule)
        assert all("principal_payment" in payment for payment in schedule)
        assert all("interest_payment" in payment for payment in schedule)
        assert all("remaining_balance" in payment for payment in schedule)

        # Verify balance decreases
        balances = [payment["remaining_balance"] for payment in schedule]
        assert balances == sorted(balances, reverse=True)
        assert balances[-1] <= 1  # Should be nearly zero at end

    def test_loan_calculations_edge_cases(self):
        """Test loan calculations with edge cases."""
        from app.api.loans import calculate_monthly_payment

        # Very low interest rate
        payment_low = calculate_monthly_payment(100000, 0.1, 12)
        assert payment_low > 8300  # Approximately principal/12

        # Very high interest rate
        payment_high = calculate_monthly_payment(100000, 50.0, 12)
        assert payment_high > 12000  # Should be significantly higher

        # Long term
        payment_long = calculate_monthly_payment(100000, 12.0, 60)
        payment_short = calculate_monthly_payment(100000, 12.0, 12)
        assert payment_long < payment_short  # Longer term = lower payment


@pytest.mark.loans
@pytest.mark.integration
class TestLoanWorkflow:
    """Test complete loan application workflow."""

    def test_complete_loan_application_workflow(self, client: TestClient, authenticated_user, db_session):
        """Test complete loan workflow from application to approval."""
        headers = authenticated_user["headers"]
        user = authenticated_user["user"]

        # Add green score for eligibility
        score = GreenScore(
            user_id=user.id,
            overall_score=75,
            confidence_score=0.8,
            evidence_count=3
        )
        db_session.add(score)
        db_session.commit()

        # Step 1: Apply for loan
        loan_data = {
            "amount": 400000,
            "term": 12,
            "purpose": "equipment",
            "collateral_description": "Farm equipment and land",
            "business_plan_summary": "Expand sustainable farming operations",
            "requested_use_of_funds": "Purchase organic fertilizers and irrigation system"
        }

        response = client.post("/loans/apply", json=loan_data, headers=headers)
        assert response.status_code == 201
        loan_id = response.json()["application_id"]

        # Step 2: Check application status
        response = client.get(f"/loans/{loan_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["status"] == "pending"

        # Step 3: Admin reviews and approves (simulated)
        loan = db_session.query(LoanApplication).filter(LoanApplication.id == loan_id).first()
        loan.status = "approved"
        loan.approved_date = datetime.utcnow()
        db_session.commit()

        # Step 4: Check updated status
        response = client.get(f"/loans/{loan_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["status"] == "approved"

        # Step 5: Simulate disbursement
        loan.status = "disbursed"
        loan.disbursed_date = datetime.utcnow()
        db_session.commit()

        response = client.get(f"/loans/{loan_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "disbursed"
        assert "disbursed_date" in data

    def test_loan_rejection_workflow(self, client: TestClient, authenticated_user, db_session):
        """Test loan rejection workflow."""
        headers = authenticated_user["headers"]

        # No green score for automatic rejection
        loan_data = {
            "amount": 1000000,  # High amount
            "term": 12,
            "purpose": "expansion"
        }

        response = client.post("/loans/apply", json=loan_data, headers=headers)

        # Should either be rejected immediately or created with pending status
        if response.status_code == 201:
            loan_id = response.json()["application_id"]

            # Admin rejects (simulated)
            loan = db_session.query(LoanApplication).filter(LoanApplication.id == loan_id).first()
            loan.status = "rejected"
            loan.rejection_reason = "Insufficient green score and excessive amount"
            db_session.commit()

            # Check rejection
            response = client.get(f"/loans/{loan_id}", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "rejected"
            assert "rejection_reason" in data
        else:
            assert response.status_code == 400  # Immediate rejection


@pytest.mark.loans
@pytest.mark.performance
class TestLoanPerformance:
    """Test loan system performance."""

    def test_bulk_loan_applications(self, client: TestClient, multiple_users, db_session):
        """Test handling multiple loan applications."""
        import time

        # Create green scores for users
        for user in multiple_users:
            score = GreenScore(
                user_id=user.id,
                overall_score=70,
                confidence_score=0.8,
                evidence_count=3
            )
            db_session.add(score)
        db_session.commit()

        start_time = time.time()

        # Create loan applications for all users
        loan_ids = []
        for user in multiple_users:
            token = create_token({"sub": str(user.id)})
            headers = {"Authorization": f"Bearer {token}"}

            loan_data = {
                "amount": 300000,
                "term": 12,
                "purpose": "equipment"
            }

            response = client.post("/loans/apply", json=loan_data, headers=headers)
            if response.status_code == 201:
                loan_ids.append(response.json()["application_id"])

        processing_time = time.time() - start_time

        assert len(loan_ids) >= 3  # At least 3 successful applications
        assert processing_time < 10  # Should complete within 10 seconds

    def test_loan_calculation_performance(self):
        """Test performance of loan calculations."""
        from app.api.loans import calculate_monthly_payment
        import time

        start_time = time.time()

        # Perform 1000 calculations
        for i in range(1000):
            payment = calculate_monthly_payment(500000, 12.0, 12)
            assert payment > 0

        calculation_time = time.time() - start_time

        assert calculation_time < 1.0  # Should complete in under 1 second