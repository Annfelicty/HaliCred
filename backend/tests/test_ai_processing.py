"""
Comprehensive AI processing tests for HaliCred backend.
Tests evidence processing, score calculation, and AI orchestration.
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from pathlib import Path

from app.ai.orchestrator import process_evidence_with_ai, calculate_green_score
from app.ai.evidence_processor import EvidenceProcessor
from app.ai.score_calculator import ScoreCalculator
from app.ai.emission_calculator import EmissionCalculator
from app.db.models import Evidence, User, GreenScore


@pytest.mark.ai
class TestEvidenceProcessor:
    """Test evidence processing functionality."""

    def test_process_image_evidence_success(self, mock_vision_api, mock_gemini_api):
        """Test successful image evidence processing."""
        processor = EvidenceProcessor()

        # Mock file data
        mock_file_data = b"fake image data"
        evidence_type = "solar_panel"

        result = processor.process_image(mock_file_data, evidence_type)

        assert result["confidence"] >= 0.8
        assert "analysis" in result
        assert "score_impact" in result
        assert result["score_impact"] > 0

    def test_process_document_evidence_success(self, mock_vision_api, mock_gemini_api):
        """Test successful document evidence processing."""
        processor = EvidenceProcessor()

        mock_file_data = b"fake document data"
        evidence_type = "energy_bill"

        result = processor.process_document(mock_file_data, evidence_type)

        assert result["confidence"] >= 0.7
        assert "extracted_text" in result
        assert "sustainability_impact" in result

    def test_process_invalid_evidence_type(self):
        """Test processing with invalid evidence type."""
        processor = EvidenceProcessor()

        with pytest.raises(ValueError, match="Unsupported evidence type"):
            processor.process_image(b"data", "invalid_type")

    def test_process_corrupted_file(self, mock_vision_api):
        """Test processing corrupted file data."""
        processor = EvidenceProcessor()
        mock_vision_api.text_detection.side_effect = Exception("Corrupted file")

        with pytest.raises(Exception):
            processor.process_image(b"corrupted", "solar_panel")

    @pytest.mark.performance
    def test_large_file_processing(self, mock_vision_api, mock_gemini_api):
        """Test processing large files within time limits."""
        processor = EvidenceProcessor()

        # Simulate 10MB file
        large_file_data = b"x" * (10 * 1024 * 1024)

        import time
        start_time = time.time()
        result = processor.process_image(large_file_data, "solar_panel")
        processing_time = time.time() - start_time

        assert processing_time < 30  # Should process within 30 seconds
        assert result["confidence"] > 0


@pytest.mark.ai
class TestScoreCalculator:
    """Test green score calculation functionality."""

    def test_calculate_initial_score(self, sample_user, db_session):
        """Test initial score calculation for new user."""
        calculator = ScoreCalculator()

        score = calculator.calculate_score(sample_user.id, db_session)

        assert score["overall_score"] >= 0
        assert score["overall_score"] <= 100
        assert "energy_efficiency" in score
        assert "water_conservation" in score
        assert "waste_management" in score
        assert "renewable_energy" in score
        assert "carbon_footprint" in score

    def test_calculate_score_with_evidence(self, sample_user, sample_evidence, db_session):
        """Test score calculation with existing evidence."""
        calculator = ScoreCalculator()

        score = calculator.calculate_score(sample_user.id, db_session)

        assert score["overall_score"] > 50  # Should be higher with evidence
        assert score["evidence_count"] >= 1
        assert score["confidence_score"] > 0.5

    def test_score_improvement_tracking(self, sample_user, db_session):
        """Test score improvement over time."""
        calculator = ScoreCalculator()

        # Initial score
        initial_score = calculator.calculate_score(sample_user.id, db_session)

        # Add evidence and recalculate
        evidence = Evidence(
            user_id=sample_user.id,
            evidence_type="led_lighting",
            file_path="/test/led.jpg",
            ai_analysis_result={"score_contribution": 10},
            processing_status="completed"
        )
        db_session.add(evidence)
        db_session.commit()

        new_score = calculator.calculate_score(sample_user.id, db_session)

        assert new_score["overall_score"] >= initial_score["overall_score"]

    def test_score_validation_ranges(self, sample_user, db_session):
        """Test that all score components are within valid ranges."""
        calculator = ScoreCalculator()

        score = calculator.calculate_score(sample_user.id, db_session)

        # Check all components are 0-100
        for component in ["overall_score", "energy_efficiency", "water_conservation",
                         "waste_management", "renewable_energy", "carbon_footprint"]:
            assert 0 <= score[component] <= 100

        # Check confidence is 0-1
        assert 0 <= score["confidence_score"] <= 1

    @pytest.mark.performance
    def test_bulk_score_calculation(self, multiple_users, db_session):
        """Test bulk score calculation performance."""
        calculator = ScoreCalculator()

        import time
        start_time = time.time()

        scores = []
        for user in multiple_users:
            score = calculator.calculate_score(user.id, db_session)
            scores.append(score)

        calculation_time = time.time() - start_time

        assert len(scores) == len(multiple_users)
        assert calculation_time < 10  # Should complete within 10 seconds
        assert all(0 <= score["overall_score"] <= 100 for score in scores)


@pytest.mark.ai
class TestEmissionCalculator:
    """Test carbon emission calculation functionality."""

    def test_calculate_energy_emissions(self, mock_climatiq_api):
        """Test energy consumption emission calculation."""
        calculator = EmissionCalculator()

        emissions = calculator.calculate_energy_emissions(
            energy_kwh=1000,
            energy_source="grid_mix"
        )

        assert emissions["co2e"] > 0
        assert emissions["co2e_unit"] == "tonnes"
        assert "activity_data" in emissions

    def test_calculate_transport_emissions(self, mock_climatiq_api):
        """Test transportation emission calculation."""
        calculator = EmissionCalculator()

        emissions = calculator.calculate_transport_emissions(
            distance_km=100,
            transport_mode="car"
        )

        assert emissions["co2e"] > 0
        assert emissions["activity_data"]["value"] == 100

    def test_calculate_waste_emissions(self, mock_climatiq_api):
        """Test waste disposal emission calculation."""
        calculator = EmissionCalculator()

        emissions = calculator.calculate_waste_emissions(
            waste_kg=50,
            waste_type="organic"
        )

        assert emissions["co2e"] >= 0  # Could be negative for composting
        assert "emission_factor" in emissions

    def test_invalid_energy_source(self):
        """Test error handling for invalid energy source."""
        calculator = EmissionCalculator()

        with pytest.raises(ValueError, match="Unsupported energy source"):
            calculator.calculate_energy_emissions(1000, "invalid_source")

    @pytest.mark.integration
    def test_emission_api_timeout(self, mock_climatiq_api):
        """Test handling of API timeout."""
        calculator = EmissionCalculator()
        mock_climatiq_api.estimate_emissions.side_effect = TimeoutError("API timeout")

        with pytest.raises(TimeoutError):
            calculator.calculate_energy_emissions(1000, "grid_mix")


@pytest.mark.ai
@pytest.mark.integration
class TestAIOrchestrator:
    """Test AI orchestrator integration functionality."""

    @pytest.mark.asyncio
    async def test_process_evidence_end_to_end(self, sample_user, db_session,
                                             mock_vision_api, mock_gemini_api):
        """Test complete evidence processing workflow."""
        evidence_data = {
            "user_id": sample_user.id,
            "evidence_type": "solar_panel",
            "file_path": "/test/solar.jpg",
            "file_name": "solar.jpg",
            "file_size": 1024,
            "mime_type": "image/jpeg"
        }

        evidence = Evidence(**evidence_data)
        db_session.add(evidence)
        db_session.commit()

        result = await process_evidence_with_ai(evidence.id, db_session)

        assert result["status"] == "completed"
        assert result["confidence"] > 0.8
        assert result["score_impact"] > 0

        # Verify evidence was updated
        db_session.refresh(evidence)
        assert evidence.processing_status == "completed"
        assert evidence.ai_analysis_result is not None

    @pytest.mark.asyncio
    async def test_score_recalculation_after_evidence(self, sample_user, db_session,
                                                    mock_vision_api, mock_gemini_api):
        """Test score recalculation after evidence processing."""
        # Get initial score
        initial_score = calculate_green_score(sample_user.id, db_session)

        # Add and process evidence
        evidence = Evidence(
            user_id=sample_user.id,
            evidence_type="energy_bill",
            file_path="/test/bill.pdf",
            processing_status="pending"
        )
        db_session.add(evidence)
        db_session.commit()

        await process_evidence_with_ai(evidence.id, db_session)

        # Get updated score
        updated_score = calculate_green_score(sample_user.id, db_session)

        assert updated_score["overall_score"] >= initial_score["overall_score"]
        assert updated_score["evidence_count"] > initial_score["evidence_count"]

    def test_ai_processing_error_handling(self, sample_user, db_session):
        """Test error handling in AI processing pipeline."""
        evidence = Evidence(
            user_id=sample_user.id,
            evidence_type="solar_panel",
            file_path="/nonexistent/file.jpg",
            processing_status="pending"
        )
        db_session.add(evidence)
        db_session.commit()

        with patch('app.ai.orchestrator.EvidenceProcessor') as mock_processor:
            mock_processor.return_value.process_image.side_effect = Exception("Processing failed")

            with pytest.raises(Exception):
                process_evidence_with_ai(evidence.id, db_session)

            # Verify evidence status was updated
            db_session.refresh(evidence)
            assert evidence.processing_status == "failed"

    @pytest.mark.performance
    def test_concurrent_ai_processing(self, multiple_users, db_session,
                                    mock_vision_api, mock_gemini_api):
        """Test concurrent AI processing performance."""
        import asyncio
        import time

        # Create multiple evidence records
        evidence_list = []
        for user in multiple_users[:3]:  # Test with 3 users
            evidence = Evidence(
                user_id=user.id,
                evidence_type="solar_panel",
                file_path=f"/test/solar_{user.id}.jpg",
                processing_status="pending"
            )
            db_session.add(evidence)
            evidence_list.append(evidence)
        db_session.commit()

        async def process_all():
            tasks = [process_evidence_with_ai(evidence.id, db_session)
                    for evidence in evidence_list]
            return await asyncio.gather(*tasks)

        start_time = time.time()
        results = asyncio.run(process_all())
        processing_time = time.time() - start_time

        assert len(results) == len(evidence_list)
        assert all(result["status"] == "completed" for result in results)
        assert processing_time < 15  # Should complete concurrent processing quickly

    @pytest.mark.security
    def test_ai_input_sanitization(self, sample_user, db_session):
        """Test input sanitization in AI processing."""
        malicious_evidence = Evidence(
            user_id=sample_user.id,
            evidence_type="solar_panel",
            file_path="/test/<script>alert('xss')</script>.jpg",
            description="<script>alert('xss')</script>",
            processing_status="pending"
        )
        db_session.add(malicious_evidence)
        db_session.commit()

        # Should not raise security exceptions
        with patch('app.ai.orchestrator.EvidenceProcessor') as mock_processor:
            mock_processor.return_value.process_image.return_value = {
                "confidence": 0.8,
                "analysis": "Clean analysis",
                "score_impact": 10
            }

            result = process_evidence_with_ai(malicious_evidence.id, db_session)

            # Verify no script tags in result
            assert "<script>" not in str(result)
            assert "alert(" not in str(result)


@pytest.mark.ai
class TestAIModelIntegration:
    """Test integration with external AI models."""

    def test_gemini_api_integration(self, mock_gemini_api):
        """Test Gemini API integration and response parsing."""
        from app.ai.orchestrator import process_with_gemini

        test_prompt = "Analyze this sustainability evidence"
        test_image_data = b"fake image data"

        result = process_with_gemini(test_prompt, test_image_data)

        assert result["confidence"] > 0
        assert "analysis" in result
        assert "score_impact" in result

    def test_vision_api_integration(self, mock_vision_api):
        """Test Google Vision API integration."""
        from app.ai.evidence_processor import extract_text_from_image

        test_image_data = b"fake image data"

        result = extract_text_from_image(test_image_data)

        assert "text_annotations" in result
        assert len(result["text_annotations"]) > 0

    def test_climatiq_api_integration(self, mock_climatiq_api):
        """Test Climatiq API integration."""
        from app.ai.emission_calculator import get_emission_factor

        result = get_emission_factor("electricity-energy_source_grid_mix")

        assert "co2e" in result
        assert result["co2e"] > 0

    @pytest.mark.integration
    def test_api_rate_limiting(self):
        """Test handling of API rate limiting."""
        from app.ai.orchestrator import handle_rate_limit

        # Should implement exponential backoff
        with patch('time.sleep') as mock_sleep:
            handle_rate_limit(attempt=3)
            mock_sleep.assert_called_once()

    @pytest.mark.integration
    def test_api_error_recovery(self, mock_gemini_api):
        """Test recovery from API errors."""
        from app.ai.orchestrator import process_with_gemini

        # Simulate API failure then success
        mock_gemini_api.side_effect = [
            Exception("API Error"),
            {"confidence": 0.8, "analysis": "Success", "score_impact": 10}
        ]

        result = process_with_gemini("test prompt", b"test data")

        assert result["confidence"] == 0.8
        assert result["analysis"] == "Success"