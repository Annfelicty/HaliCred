# Phase 7 Operational Workflow

## 1. Daily Ops Checklist
- Verify `.env` secrets loaded (`GEMINI_API_KEY`, `GOOGLE_APPLICATION_CREDENTIALS`, `CLIMATIQ_API_KEY`).
- Confirm external service quotas in Google AI Studio and Climatiq dashboard.
- Run `python backend/run_live_ai_checks.py` to sanity check Gemini, Vision, Climatiq.
- Monitor FastAPI and Celery logs for AI processing latency.

## 2. Evidence Processing Runbook
1. SME uploads evidence via `POST /ai/evidence/process` with metadata.
2. Service writes `AIEvidence` row and copies file to `AI_EVIDENCE_TMP_DIR` (default `backend/uploads/tmp`).
3. `AIOrchestrator` executes:
   - `EvidenceProcessor.process_evidence()` → Google Vision OCR/CV.
   - `EmissionCalculator.calculate_emissions()` → Climatiq `/data/v1/estimate`.
   - `ScoreComputer.compute_score()` → sector-weighted GreenScore.
   - `CarbonCreditAggregator.calculate_carbon_credits()` → optional credit projections.
4. Persist `GreenScoreResult`, update `AIEvidence.processing_status`.
5. Publish notifications or trigger downstream workflows (loan decisions, dashboards).

## 3. Failure Handling
- **OCR unavailable**: `_extract_text()` raises; request returns 500. Check Vision credentials or Tesseract install.
- **Climatiq errors**: API returns 400 `no_emission_factors_found`. Adjust `activity_id`, `region`, `data_version`, or engage Climatiq support.
- **Gemini quota exceeded**: orchestrator falls back to deterministic path; monitor `AIProcessingLog` for `processing_method`.
- **Database errors**: transactions rolled back and evidence flagged `failed`.

## 4. Validation & Testing
- `python backend/run_live_ai_checks.py` — direct API integration check.
- `python phase6_checks.py` — end-to-end smoke suite (update evidence type to `photo`).
- `pytest tests/ai` — unit coverage for orchestrator components.

## 5. Release Procedure (Phase 7)
1. Ensure documentation updated (`backend/README.md`, `docs/architecture.md`).
2. Verify environment variable diffs captured in deployment manifests.
3. Run live checks + smoke tests against staging.
4. Tag release and attach Changelog/Release Notes.
5. Notify ops/banking partners with handoff package.

