# HaliCred System Architecture (Phase 7)

## 1. Platform Overview
HaliCred is an AI-powered green credit scoring platform that ingests sustainability evidence from SMEs, analyzes it with live AI services, and produces loan-ready insights. The stack combines a FastAPI backend, a React (Vite) web client, PostgreSQL persistence, and integrations with Gemini, Google Vision, and Climatiq.

```
Client (Web / Mobile) ─┐
                      │    ┌──────────┐     ┌────────────┐
USSD Gateway (AT) ───▶│───▶│ FastAPI   │────▶│ PostgreSQL │
                      │    │ Backend   │     └────────────┘
                      │    │           │     ┌──────────┐
Backoffice Tools ────▶┘    │           │────▶│ Redis    │
                           │           │     └──────────┘
                           │           │     ┌──────────┐
                           │           │────▶│ MinIO/S3 │
                           │           │     └──────────┘
                           │           │
                           │           │     ┌───────────────┐
                           │           └────▶│ AI Orchestrator│
                           │                 └───────────────┘
                           │                       │
                           │                       │ LLM Function Calls
                           │                       ▼
                           │            ┌────────────────────────┐
                           │            │Google Gemini (LLM)     │
                           │            ├────────────────────────┤
                           │            │Google Vision (OCR + CV)│
                           │            ├────────────────────────┤
                           │            │Climatiq (Emissions)    │
                           │            └────────────────────────┘
                           │
                           ▼
                 Analytics & Carbon Credit Reporting
```

## 2. Backend Service Layers
- **API Layer (`app/api/`)**: FastAPI routers expose authentication, evidence, scoring, and loan endpoints.
- **Service Layer (`app/services/`)**: Houses business logic such as `AIService` (live orchestrator integration), `LoanService`, and portfolio calculations.
- **AI Modules (`app/ai/`)**:
  - `AIOrchestrator`: Coordinates Gemini function calls, deterministic fallbacks, and microservice execution.
  - `EvidenceProcessor`: Handles file acquisition, Google Vision OCR/CV, and feature extraction.
  - `EmissionCalculator`: Calls Climatiq GA APIs with validated `activity_id`/`data_version` pairs.
  - `ScoreComputer`: Converts emissions + derived features into weighted pillar scores.
  - `CarbonCreditAggregator`: Generates carbon credit projections and pooling summaries.

## 3. Data Stores
- **PostgreSQL**: Primary relational database via SQLAlchemy models (`app/db/models.py`, `app/db/ai_models.py`). Stores users, evidence metadata, AI outputs, loans, and audit logs.
- **Redis**: Celery broker/cache and transient storage (rate limiting, OTPs, background jobs).
- **MinIO/S3**: Evidence file storage; signed URLs allow upload while AI pipeline streams local copies when required.

## 4. AI Evidence Processing Flow
1. `POST /ai/evidence/process` accepts multi-part evidence + metadata.
2. `AIService.process_evidence_request()` creates an `AIEvidence` row, ensures file accessibility, and calls `AIOrchestrator`.
3. `EvidenceProcessor` downloads the file (local path or HTTP), runs Google Vision OCR/CV, and estimates features.
4. `EmissionCalculator` fetches live emission factors from Climatiq GA (`/data/v1/search`) and computes emissions via `/estimate`.
5. `ScoreComputer` calculates the GreenScore with sector baselines; `CarbonCreditAggregator` projects credits.
6. Results persist to `GreenScoreResult` and optional `CarbonCredit` tables for downstream reporting.

## 5. External Integrations
- **Gemini** (`GEMINI_API_KEY`): Provides LLM orchestration + function calling. Current model: `models/gemini-2.5-flash`.
- **Google Vision** (`GOOGLE_APPLICATION_CREDENTIALS` or `GOOGLE_VISION_API_KEY`): OCR & CV. Service account JSON stored in `backend/keys/google-vision.json` (development) or fetched via Secret Manager in production.
- **Climatiq** (`CLIMATIQ_API_KEY`): Emission factor search (`/data/v1/search`) and estimates (`/data/v1/estimate`). Requires explicit `activity_id` and `data_version`.

## 6. Deployment Concerns
- **Environment Configuration**: `.env` controls database URLs, AI credentials, and feature flags; ensure production keys loaded via vault/secret manager.
- **Background Processing**: Celery workers needed when enabling asynchronous evidence pipelines; currently AI pipeline runs inside request coroutine with awaited tasks.
- **Observability**: Use FastAPI logging + `AIProcessingLog` table for audit trails. Integrate with preferred APM (e.g., OpenTelemetry) for latency tracking.
- **Scalability**: Frontend served separately; backend can scale horizontally (stateless) with shared Postgres/Redis/MinIO. AI orchestration calls external services—monitor quotas and implement retry/backoff.

## 7. Outstanding Follow-Ups (Phase 7)
- **Climatiq Dataset Verification**: Secure catalog access or support confirmation for Kenya-specific electricity factors to finalize emissions baseline.
- **Phase 6 Test Alignment**: Update automation to use accepted evidence types (e.g., `photo`) or extend `EvidenceData` literals.
- **Telemetry Enhancements**: Add structured logs/traces around external API interactions to aid ops runbooks.

