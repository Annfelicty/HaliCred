# HaliCred Phase 7 Release Notes

## Summary
- Live AI orchestration now active across Gemini, Google Vision, and Climatiq integrations.
- Backend `AIService.process_evidence_request()` routes evidence through `AIOrchestrator` and persists real `GreenScoreResult` records.
- Documentation refreshed to highlight environment variables, verification commands, and operational runbooks.
- Phase 6 automation pending Climatiq catalog alignment and evidence-type literal update.

## Key Changes
- Replaced simulation logic in `backend/app/services/ai_service.py` with live orchestrator invocation.
- Updated `backend/app/ai/evidence_processor.py` to remove mock OCR fallbacks and support local file paths.
- Adjusted `backend/run_live_ai_checks.py` for Climatiq GA API (explicit `data_version`, activity search).
- Enhanced `backend/app/ai/climatiq_client.py` caching and endpoint usage (`/data/v1/search`, `/data/v1/estimate`).
- Added Phase 7 highlights, AI configuration, and troubleshooting guidance to `backend/README.md`.
- Authored architecture and workflow documentation under `docs/`.

## Testing
- `python backend/run_live_ai_checks.py` — validates Gemini, Google Vision, and Climatiq connectivity (Climatiq dependent on dataset access).
- `python phase6_checks.py` — smoke test covering OTP, scoring, loans, and evidence flow (update `evidence_type` to `photo`).
- `pytest tests/ai` — deterministic coverage of orchestrator components.

## Deployment Notes
- Ensure `.env` contains `GEMINI_API_KEY`, `GOOGLE_APPLICATION_CREDENTIALS`, `CLIMATIQ_API_KEY`, and `CLIMATIQ_DATA_VERSION`.
- Mount Google Vision service account JSON and grant `roles/vision.user`.
- Confirm Climatiq catalog access to `electricity-supply_grid-source_residual_mix` (or supply alternate activity).
- Monitor Gemini quota and configure retry/backoff via `AIOrchestrator` if scaling horizontally.

## Follow-Ups
- Finalize Climatiq factor for Kenya-specific electricity and update automation accordingly.
- Extend `EvidenceData.type` literals or normalize inputs from Phase 6 checks.
- Add structured logging / tracing for external API calls (Gemini, Vision, Climatiq).
