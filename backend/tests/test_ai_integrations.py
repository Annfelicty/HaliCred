import numpy as np
import pytest
from datetime import datetime, timezone

from backend.app.ai.evidence_processor import EvidenceProcessor
from backend.app.ai.emission_calculator import EmissionCalculator
from backend.app.ai.models import EvidenceData, OCRResult, CVResult, EmissionFeatures


@pytest.mark.asyncio
async def test_evidence_processor_vision_pipeline(monkeypatch):
    processor = EvidenceProcessor()

    evidence = EvidenceData(
        evidence_id="ev-vision-1",
        user_id="user-vision-1",
        type="photo",
        file_url="https://example.com/image.jpg",
        timestamp=datetime.now(timezone.utc),
        geo={"lat": -1.28, "lon": 36.82},
        metadata={"source": "unit-test"},
    )

    async def fake_download_image(_):
        return np.zeros((64, 64, 3), dtype=np.uint8)

    async def fake_google_vision_ocr(*args, **kwargs):
        return OCRResult(
            vendor="Bright Solar Ltd",
            amount_ksh=60000.0,
            date="2024-05-15",
            items=["Solar Irrigation Pump"],
            confidence=0.95,
            raw_text="Invoice Solar Irrigation Pump Amount 60000 KES",
        )

    async def fake_google_vision_cv(*args, **kwargs):
        return CVResult(
            labels=["solar_panel", "water_pump"],
            caption="Image shows solar irrigation pump",
            confidence=0.9,
            detected_objects=[{"name": "solar_panel", "score": 0.92}],
        )

    monkeypatch.setattr(processor, "_download_image", fake_download_image)
    monkeypatch.setattr(processor, "_vision_available", lambda: True)
    monkeypatch.setattr(processor, "_google_vision_ocr", fake_google_vision_ocr)
    monkeypatch.setattr(processor, "_google_vision_cv", fake_google_vision_cv)

    result = await processor.process_evidence(evidence)

    assert result.ocr.vendor == "Bright Solar Ltd"
    assert result.cv.labels == ["solar_panel", "water_pump"]
    assert result.features is not None
    assert result.features.solar_kwh_generated is not None
    assert result.processing_confidence > 0.0


class DummyClimatiqClient:
    def __init__(self) -> None:
        self.api_key = "mock-key"

    def get_emission_factor(self, **kwargs):
        if kwargs.get("category") == "electricity":
            return {"co2e": 0.35, "id": "grid-factor"}
        if kwargs.get("activity_id") == "fuel-type_diesel":
            return {"co2e": 2.4, "id": "diesel-factor"}
        if kwargs.get("category") == "waste":
            return {"co2e": 5.5, "id": "waste-factor"}
        return None


@pytest.mark.asyncio
async def test_emission_calculator_climatiq_factors():
    calculator = EmissionCalculator(climatiq_client=DummyClimatiqClient())

    features = EmissionFeatures(
        solar_kwh_generated=150.0,
        diesel_liters_avoided=20.0,
        plastic_kg_recycled=5.0,
    )

    result = await calculator.calculate_emissions(
        evidence_id="ev-emission-1",
        sector="farmer",
        region="Kenya",
        features=features,
    )

    assert pytest.approx(result.co2_kg_components["solar_generation"], rel=1e-3) == 52.5
    assert pytest.approx(result.co2_kg_components["diesel"], rel=1e-3) == 48.0
    assert result.method == "climatiq factors"
    assert result.provenance["factor_source"] == "climatiq"
    assert result.confidence >= 0.5
