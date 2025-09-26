import pytest
from datetime import datetime

from backend.app.ai.orchestrator import AIOrchestrator
from backend.app.ai.models import (
    ProcessedEvidence,
    OCRResult,
    CVResult,
    EmissionFeatures,
    EmissionResult,
    AIOrchestrationRequest,
    GreenScoreResult,
    CarbonCredit,
)


@pytest.mark.asyncio
async def test_deterministic_processing_pipeline(monkeypatch):
    orchestrator = AIOrchestrator(config={})

    sample_ocr = OCRResult(
        vendor="Solar Solutions Ltd",
        amount_ksh=50000.0,
        date="2024-02-10",
        items=["Solar Pump System"],
        confidence=0.9,
        raw_text="Invoice for Solar Pump System",
    )
    sample_cv = CVResult(
        labels=["solar_panel", "water_pump"],
        caption="Image shows solar panels and pump",
        confidence=0.8,
    )
    processed = ProcessedEvidence(
        evidence_id="ev-123",
        user_id="user-123",
        type="receipt",
        ocr=sample_ocr,
        cv=sample_cv,
        features=EmissionFeatures(solar_kwh_generated=120.0),
        geo={"lat": -1.28, "lon": 36.82},
        timestamp=datetime.utcnow(),
        processing_confidence=0.85,
    )
    request = AIOrchestrationRequest(
        evidence=processed,
        sector="farmer",
        region="Kenya",
    )

    async def fake_calculate_emissions(**kwargs):
        return EmissionResult(
            evidence_id=processed.evidence_id,
            co2_kg_components={"solar_generation": 54.0},
            co2_kg_total=54.0,
            method="test_method",
            provenance={"source": "test"},
            confidence=0.9,
        )

    def fake_estimate_user_metrics(*args, **kwargs):
        return {"renewable_pct": 0.8, "water_m3_saved_ann": 600.0}

    async def fake_compute_score(**kwargs):
        return GreenScoreResult(
            user_id=processed.user_id,
            evidence_id=processed.evidence_id,
            greenscore=82,
            subscores={"energy": 25.0, "water": 15.0},
            co2_saved_tonnes=0.054,
            confidence=0.88,
            explainers=["Energy improvements"],
            actions=["Great job"],
        )

    async def fake_carbon_credits(**kwargs):
        return [
            CarbonCredit(
                user_id=processed.user_id,
                evidence_ids=[processed.evidence_id],
                verified_co2_tonnes=0.05,
                credits_eligible=0.04,
            )
        ]

    monkeypatch.setattr(
        orchestrator.emission_calculator,
        "calculate_emissions",
        fake_calculate_emissions,
    )
    monkeypatch.setattr(
        orchestrator.score_computer,
        "estimate_user_metrics_from_evidence",
        fake_estimate_user_metrics,
    )
    monkeypatch.setattr(
        orchestrator.score_computer,
        "compute_score",
        fake_compute_score,
    )
    monkeypatch.setattr(
        orchestrator.carbon_credit_aggregator,
        "calculate_carbon_credits",
        fake_carbon_credits,
    )

    result = await orchestrator._deterministic_processing(request)

    assert result.greenscore == 82
    assert result.carbon_credits is not None
    assert result.co2_saved_tonnes == 0.054
    assert result.subscores["energy"] == 25.0
