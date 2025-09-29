# Phase 7 Handoff Package

## 1. Contacts & Ownership
- **Engineering Lead:** TBD (insert primary contact)
- **AI Integrations SME:** TBD
- **Ops/Support Escalation:** ops@halicred.example

## 2. Environment & Credentials Checklist
- `.env` populated with production values:
  - `DATABASE_URL`
  - `REDIS_URL`
  - `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`
  - `GEMINI_API_KEY`
  - `GOOGLE_APPLICATION_CREDENTIALS` (absolute path on server)
  - `CLIMATIQ_API_KEY`
  - `CLIMATIQ_DATA_VERSION`
- Google Vision service account JSON deployed and permissioned (`roles/vision.user`).
- Gemini API key verified in Google AI Studio project (model `models/gemini-2.5-flash`).
- Climatiq API key confirmed with dataset access to selected `activity_id`.

## 3. Deployment Steps
1. Provision infrastructure (PostgreSQL, Redis, MinIO/S3, application host).
2. Clone repository and install backend requirements (`pip install -r backend/requirements.txt`).
3. Apply migrations: `cd backend && alembic upgrade head`.
4. Configure `.env` (see `backend/README.md`).
5. Launch services:
   ```bash
   python backend/run.py  # or uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
6. Optional: start Celery worker if background jobs enabled.

## 4. Verification Suite
- `python backend/run_live_ai_checks.py`
- `python phase6_checks.py` (ensure evidence type aligned with `EvidenceData` literals)
- `pytest tests/ai`

## 5. Monitoring & Logging
- FastAPI logs (stdout) for request and AI orchestration traces.
- `AIProcessingLog` table for auditing function calls and fallback usage.
- External service dashboards:
  - Gemini usage (Google AI Studio).
  - Google Vision quota (Cloud Console → APIs & Services → Dashboard).
  - Climatiq dashboard (https://www.climatiq.io/).

## 6. Incident Response Playbook
- **Gemini Failure:** switch to deterministic path; monitor `AIProcessingLog.processing_method`. Re-attempt with smaller context or throttle requests.
- **Vision Errors:** validate credential path, regenerate service key if needed, fallback to Tesseract if configured.
- **Climatiq Errors:** verify `activity_id` and `data_version`; adjust to `GLO` region or consult support.
- **Database/App errors:** check PostgreSQL logs; re-run migrations; ensure `DATABASE_URL` reachable.

## 7. Documentation Links
- Backend setup & AI troubleshooting: `backend/README.md`
- System architecture overview: `docs/architecture.md`
- Operational workflow & runbook: `docs/workflow.md`
- Release notes: `docs/release_notes_phase7.md`

## 8. Outstanding Follow-Ups
- Secure Climatiq factor for Kenya-specific electricity baseline.
- Update Phase 6 automation evidence type or extend `EvidenceData` literals.
- Add structured logging for external API durations and errors.
