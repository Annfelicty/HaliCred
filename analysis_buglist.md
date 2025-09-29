# HaliCred Prioritized Bug List

## High Severity

- **Missing awaits in `backend/app/api/ai_engine.py`**
  - *Issue*: `get_current_greenscore()` and `get_greenscore_history()` call async methods without `await`, returning coroutines and causing `500` responses.
  - *Why critical*: Breaks the SME dashboard’s GreenScore view and blocks E2E flow.
  - *Remediation*: Add `await` when invoking the `AIService` methods and ensure response serialization is intact.

- **Hard-coded `/tmp/` path in `backend/app/api/ai_engine.py`**
  - *Issue*: Evidence uploads are written to `/tmp/...` which fails on Windows.
  - *Why critical*: Evidence processing crashes on the target Windows 10 environment.
  - *Remediation*: Use `tempfile.gettempdir()` and `os.path.join()` for cross-platform temp files.

- **Carbon credits endpoint mismatch (`backend/app/api/ai_engine.py` ↔ `backend/app/services/ai_service.py`)**
  - *Issue*: Endpoint calls a non-existent method name and the service references fields not defined on `CarbonCredit` ORM.
  - *Why critical*: `/ai/carbon-credits/portfolio` errors, breaking acceptance criteria for external integrations.
  - *Remediation*: Align endpoint to `await ai_service.get_carbon_credits_portfolio(...)`, rewrite the service to use actual ORM fields, and document response shape.

- **Celery tasks use in-memory `EVIDENCE` dict (`backend/app/utilis.py`)**
  - *Issue*: Background tasks don’t touch the database; the API workflow and Celery paths diverge.
  - *Why critical*: Evidence verification pipeline fails silently on eager tasks or Windows.
  - *Remediation*: Run Celery in eager mode for Windows (`CELERY_TASK_ALWAYS_EAGER=1`) and note that tasks must later migrate to DB-aware implementations.

## Medium Severity

- **Duplicate `get_current_user()` implementations**
  - *Issue*: `backend/app/auth.py`, `backend/app/main.py`, and `backend/app/utilis.py` maintain separate auth logic.
  - *Why important*: Risk of inconsistent JWT handling and roles.
  - *Remediation*: Standardize all routers on `app.auth.get_current_user()`.

- **Admin API route mismatches**
  - *Issue*: Frontend expects `/admin/loan-applications` and `/admin/loans/{id}/review`; backend exposes `/admin/applications` and `/admin/applications/{id}/decision`.
  - *Why important*: Bank UI fails to load or post decisions when wired to backend.
  - *Remediation*: Add alias routes on backend or update frontend API client to match.

- **Sector analytics endpoint mismatch**
  - *Issue*: Frontend calls `/ai/sector/analytics`; backend provides `/ai/analytics/sector/{sector}`.
  - *Why important*: Analytics view is broken.
  - *Remediation*: Add alias route or adjust frontend path.

- **`AIService.store_evidence()` schema drift**
  - *Issue*: Uses keys that don’t exist on `AIEvidence` ORM (`evidence_type`, `file_url`, etc.).
  - *Why important*: If invoked, raises runtime errors; signals tech debt.
  - *Remediation*: Update mapping to ORM fields or remove unused method.

## Low Severity

- **Duplicate `get_ai_service` definition in `backend/app/api/ai_engine.py`**
  - *Issue*: Redundant function causes confusion.
  - *Remediation*: Remove the duplicate.

- **Scattered CORS/log configuration**
  - *Issue*: CORS origins and logging defaults defined in multiple files.
  - *Remediation*: Centralize via `app.config.settings` for maintainability.

- **Development secrets committed in defaults**
  - *Issue*: `.env` template and `app/config.py` contain real-looking secrets.
  - *Remediation*: Document rotation plan and ensure production secrets are not hard-coded.
