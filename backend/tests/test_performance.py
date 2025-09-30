"""
Performance and load testing for HaliCred backend.
Tests system performance under various load conditions and measures response times.
"""

import pytest
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth import create_token
from app.db.models import User, GreenScore, LoanApplication, Evidence


@pytest.mark.performance
class TestAPIPerformance:
    """Test API endpoint performance."""

    def test_authentication_performance(self, client: TestClient, mock_redis):
        """Test authentication endpoint performance."""
        mock_redis.get.return_value = "123456".encode()

        # Test OTP verification performance
        times = []
        for i in range(50):
            start_time = time.time()
            response = client.post("/auth/verify", json={
                "phone": f"+25470000{i:04d}",
                "otp": "123456"
            })
            response_time = time.time() - start_time
            times.append(response_time)

        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18]  # 95th percentile

        assert avg_time < 0.5  # Average response under 500ms
        assert p95_time < 1.0  # 95th percentile under 1 second
        assert max(times) < 2.0  # No response over 2 seconds

    def test_green_score_calculation_performance(self, client: TestClient, authenticated_user):
        """Test green score calculation performance."""
        headers = authenticated_user["headers"]

        times = []
        for i in range(20):
            start_time = time.time()
            response = client.get("/scores/current", headers=headers)
            response_time = time.time() - start_time
            times.append(response_time)

            if response.status_code != 200:
                break

        if times:  # Only test if we got responses
            avg_time = statistics.mean(times)
            assert avg_time < 1.0  # Score calculation under 1 second

    def test_loan_application_performance(self, client: TestClient, authenticated_user):
        """Test loan application creation performance."""
        headers = authenticated_user["headers"]

        loan_data = {
            "amount": 500000,
            "term": 12,
            "purpose": "equipment",
            "collateral_description": "Farm equipment",
            "business_plan_summary": "Expand operations"
        }

        times = []
        for i in range(10):
            start_time = time.time()
            response = client.post("/loans/apply", json=loan_data, headers=headers)
            response_time = time.time() - start_time
            times.append(response_time)

        avg_time = statistics.mean(times)
        assert avg_time < 2.0  # Loan application under 2 seconds

    def test_evidence_upload_performance(self, client: TestClient, authenticated_user):
        """Test evidence upload performance."""
        headers = authenticated_user["headers"]

        # Simulate file upload
        files = {"file": ("test.jpg", b"fake image data" * 1000, "image/jpeg")}
        data = {
            "evidence_type": "solar_panel",
            "description": "Solar panel installation"
        }

        start_time = time.time()
        response = client.post("/evidence/upload", files=files, data=data, headers=headers)
        response_time = time.time() - start_time

        assert response_time < 5.0  # File upload under 5 seconds

    @pytest.mark.slow
    def test_concurrent_requests_performance(self, client: TestClient, multiple_users):
        """Test performance under concurrent requests."""
        def make_request(user):
            token = create_token({"sub": str(user.id)})
            headers = {"Authorization": f"Bearer {token}"}

            start_time = time.time()
            response = client.get("/users/profile", headers=headers)
            response_time = time.time() - start_time

            return {
                "status_code": response.status_code,
                "response_time": response_time
            }

        # Make concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, user) for user in multiple_users]
            results = [future.result() for future in as_completed(futures)]

        # Analyze results
        response_times = [r["response_time"] for r in results]
        success_rate = sum(1 for r in results if r["status_code"] == 200) / len(results)

        assert success_rate >= 0.9  # 90% success rate
        assert statistics.mean(response_times) < 2.0  # Average under 2 seconds
        assert max(response_times) < 5.0  # No request over 5 seconds


@pytest.mark.performance
class TestDatabasePerformance:
    """Test database operation performance."""

    def test_user_query_performance(self, db_session: Session, multiple_users):
        """Test user query performance."""
        # Test single user lookup
        start_time = time.time()
        for user in multiple_users[:10]:
            found_user = db_session.query(User).filter(User.id == user.id).first()
            assert found_user is not None
        query_time = time.time() - start_time

        assert query_time < 1.0  # 10 queries under 1 second

    def test_bulk_insert_performance(self, db_session: Session):
        """Test bulk insert performance."""
        # Create bulk evidence records
        evidence_records = []
        for i in range(100):
            evidence = Evidence(
                user_id=1,  # Assuming user exists
                evidence_type="solar_panel",
                file_path=f"/test/file_{i}.jpg",
                file_name=f"file_{i}.jpg",
                file_size=1024,
                mime_type="image/jpeg",
                processing_status="pending"
            )
            evidence_records.append(evidence)

        start_time = time.time()
        db_session.bulk_save_objects(evidence_records)
        db_session.commit()
        insert_time = time.time() - start_time

        assert insert_time < 2.0  # 100 inserts under 2 seconds

    def test_complex_query_performance(self, db_session: Session, multiple_users):
        """Test complex query performance."""
        # Create test data
        for user in multiple_users:
            score = GreenScore(
                user_id=user.id,
                overall_score=75,
                confidence_score=0.8,
                evidence_count=3
            )
            db_session.add(score)

            loan = LoanApplication(
                user_id=user.id,
                amount=500000,
                term=12,
                purpose="equipment",
                status="pending"
            )
            db_session.add(loan)
        db_session.commit()

        # Test complex query with joins
        start_time = time.time()
        result = db_session.query(User)\
            .join(GreenScore)\
            .join(LoanApplication)\
            .filter(GreenScore.overall_score > 70)\
            .filter(LoanApplication.status == "pending")\
            .all()
        query_time = time.time() - start_time

        assert len(result) > 0
        assert query_time < 1.0  # Complex query under 1 second

    def test_database_connection_pool_performance(self, db_session: Session):
        """Test database connection pool performance."""
        def query_operation():
            return db_session.query(User).count()

        start_time = time.time()
        # Simulate multiple concurrent database operations
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(query_operation) for _ in range(20)]
            results = [future.result() for future in as_completed(futures)]

        total_time = time.time() - start_time

        assert len(results) == 20
        assert total_time < 5.0  # 20 concurrent queries under 5 seconds


@pytest.mark.performance
@pytest.mark.slow
class TestLoadTesting:
    """Test system behavior under load."""

    def test_sustained_load(self, client: TestClient):
        """Test system performance under sustained load."""
        def make_health_check():
            start_time = time.time()
            response = client.get("/health/live")
            response_time = time.time() - start_time
            return {
                "status_code": response.status_code,
                "response_time": response_time
            }

        # Run sustained load for 30 seconds
        results = []
        end_time = time.time() + 30

        while time.time() < end_time:
            result = make_health_check()
            results.append(result)
            time.sleep(0.1)  # 10 requests per second

        # Analyze results
        success_rate = sum(1 for r in results if r["status_code"] == 200) / len(results)
        response_times = [r["response_time"] for r in results]
        avg_response_time = statistics.mean(response_times)

        assert success_rate >= 0.95  # 95% success rate
        assert avg_response_time < 1.0  # Average response under 1 second
        assert len(results) >= 200  # At least 200 requests processed

    def test_spike_load(self, client: TestClient, multiple_users):
        """Test system behavior under spike load."""
        def burst_requests():
            results = []
            for user in multiple_users:
                token = create_token({"sub": str(user.id)})
                headers = {"Authorization": f"Bearer {token}"}

                start_time = time.time()
                response = client.get("/users/profile", headers=headers)
                response_time = time.time() - start_time

                results.append({
                    "status_code": response.status_code,
                    "response_time": response_time
                })
            return results

        # Simulate spike load
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(burst_requests) for _ in range(3)]
            all_results = []
            for future in as_completed(futures):
                all_results.extend(future.result())

        total_time = time.time() - start_time

        # Analyze spike performance
        success_rate = sum(1 for r in all_results if r["status_code"] == 200) / len(all_results)

        assert success_rate >= 0.8  # 80% success rate during spike
        assert total_time < 10.0  # Spike handled within 10 seconds

    def test_memory_usage_under_load(self, client: TestClient):
        """Test memory usage doesn't grow excessively under load."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Generate load
        for i in range(100):
            response = client.get("/health/live")
            assert response.status_code == 200

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50 * 1024 * 1024

    @pytest.mark.integration
    def test_ai_processing_load(self, client: TestClient, authenticated_user,
                              mock_vision_api, mock_gemini_api):
        """Test AI processing performance under load."""
        headers = authenticated_user["headers"]

        def upload_evidence():
            files = {"file": ("test.jpg", b"fake image data" * 100, "image/jpeg")}
            data = {
                "evidence_type": "solar_panel",
                "description": "Test evidence"
            }

            start_time = time.time()
            response = client.post("/evidence/upload", files=files, data=data, headers=headers)
            response_time = time.time() - start_time

            return {
                "status_code": response.status_code,
                "response_time": response_time
            }

        # Test concurrent AI processing
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(upload_evidence) for _ in range(5)]
            results = [future.result() for future in as_completed(futures)]

        success_rate = sum(1 for r in results if r["status_code"] in [200, 201]) / len(results)
        avg_time = statistics.mean([r["response_time"] for r in results])

        assert success_rate >= 0.8  # 80% success rate
        assert avg_time < 10.0  # Average processing under 10 seconds


@pytest.mark.performance
class TestResourceUtilization:
    """Test resource utilization and optimization."""

    def test_cpu_usage_under_normal_load(self, client: TestClient):
        """Test CPU usage remains reasonable under normal load."""
        import psutil
        import threading

        cpu_readings = []
        monitoring = True

        def monitor_cpu():
            while monitoring:
                cpu_readings.append(psutil.cpu_percent(interval=0.1))

        # Start CPU monitoring
        monitor_thread = threading.Thread(target=monitor_cpu)
        monitor_thread.start()

        # Generate normal load
        for i in range(50):
            response = client.get("/health/live")
            assert response.status_code == 200
            time.sleep(0.1)

        # Stop monitoring
        monitoring = False
        monitor_thread.join()

        if cpu_readings:
            avg_cpu = statistics.mean(cpu_readings)
            max_cpu = max(cpu_readings)

            # CPU usage should be reasonable
            assert avg_cpu < 80.0  # Average CPU under 80%
            assert max_cpu < 95.0  # Peak CPU under 95%

    def test_response_time_consistency(self, client: TestClient):
        """Test response time consistency over time."""
        response_times = []

        # Collect response times over period
        for i in range(100):
            start_time = time.time()
            response = client.get("/health/live")
            response_time = time.time() - start_time
            response_times.append(response_time)

            assert response.status_code == 200
            time.sleep(0.05)  # Small delay between requests

        # Analyze consistency
        avg_time = statistics.mean(response_times)
        std_dev = statistics.stdev(response_times)

        assert avg_time < 0.5  # Average under 500ms
        assert std_dev < 0.2  # Low standard deviation for consistency

    def test_database_connection_efficiency(self, db_session: Session):
        """Test database connection usage efficiency."""
        # Test connection reuse
        start_time = time.time()

        for i in range(50):
            # Simple query that should reuse connections
            count = db_session.query(User).count()
            assert isinstance(count, int)

        total_time = time.time() - start_time

        # Should be very fast with connection reuse
        assert total_time < 2.0  # 50 queries under 2 seconds

    @pytest.mark.slow
    def test_long_running_stability(self, client: TestClient):
        """Test system stability over extended period."""
        start_time = time.time()
        error_count = 0
        total_requests = 0

        # Run for 2 minutes
        while time.time() - start_time < 120:
            response = client.get("/health/live")
            total_requests += 1

            if response.status_code != 200:
                error_count += 1

            time.sleep(1)  # 1 request per second

        error_rate = error_count / total_requests if total_requests > 0 else 1

        assert total_requests >= 100  # At least 100 requests made
        assert error_rate < 0.05  # Less than 5% error rate


@pytest.mark.performance
@pytest.mark.integration
class TestEndToEndPerformance:
    """Test end-to-end workflow performance."""

    def test_complete_loan_application_workflow_performance(self, client: TestClient, db_session):
        """Test complete loan workflow performance."""
        # Step 1: User registration performance
        start_time = time.time()

        with patch('app.auth.redis_client') as mock_redis:
            mock_redis.get.return_value = "123456".encode()

            registration_data = {
                "phone": "+254700999999",
                "otp": "123456",
                "name": "Performance Test User",
                "email": "perf@test.com",
                "business_name": "Test Business",
                "business_type": "farmer",
                "location": "Nairobi"
            }

            response = client.post("/auth/register", json=registration_data)
            registration_time = time.time() - start_time

            if response.status_code == 201:
                token = response.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}

                # Step 2: Green score calculation
                score_start = time.time()
                score_response = client.get("/scores/current", headers=headers)
                score_time = time.time() - score_start

                # Step 3: Loan application
                loan_start = time.time()
                loan_data = {
                    "amount": 500000,
                    "term": 12,
                    "purpose": "equipment"
                }
                loan_response = client.post("/loans/apply", json=loan_data, headers=headers)
                loan_time = time.time() - loan_start

                total_time = time.time() - start_time

                # Performance assertions
                assert registration_time < 2.0  # Registration under 2 seconds
                assert score_time < 1.0  # Score calculation under 1 second
                assert loan_time < 3.0  # Loan application under 3 seconds
                assert total_time < 10.0  # Complete workflow under 10 seconds

    def test_evidence_processing_workflow_performance(self, client: TestClient, authenticated_user,
                                                    mock_vision_api, mock_gemini_api):
        """Test evidence processing workflow performance."""
        headers = authenticated_user["headers"]

        # Complete evidence upload and processing workflow
        start_time = time.time()

        # Step 1: Upload evidence
        files = {"file": ("solar.jpg", b"fake solar panel image data" * 500, "image/jpeg")}
        data = {
            "evidence_type": "solar_panel",
            "description": "Solar panel installation receipt"
        }

        upload_response = client.post("/evidence/upload", files=files, data=data, headers=headers)
        upload_time = time.time() - start_time

        if upload_response.status_code in [200, 201]:
            evidence_id = upload_response.json().get("evidence_id")

            # Step 2: Check processing status
            status_start = time.time()
            status_response = client.get(f"/evidence/{evidence_id}", headers=headers)
            status_time = time.time() - status_start

            # Step 3: Get updated green score
            score_start = time.time()
            score_response = client.get("/scores/current", headers=headers)
            score_time = time.time() - score_start

            total_time = time.time() - start_time

            # Performance assertions
            assert upload_time < 5.0  # Upload under 5 seconds
            assert status_time < 0.5  # Status check under 500ms
            assert score_time < 1.0  # Score update under 1 second
            assert total_time < 10.0  # Complete workflow under 10 seconds