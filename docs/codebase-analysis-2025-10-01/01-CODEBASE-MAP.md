# HaliCred Codebase Map

**Document:** 01-CODEBASE-MAP.md
**Focus:** Complete directory structure and key file purposes

---

## Project Structure Overview

```
HaliCred/
├── backend/                      # FastAPI backend application
│   ├── app/                      # Main application package
│   │   ├── ai/                   # AI and ML modules
│   │   │   ├── api_client.py     # ⭐ External API client (3 APIs)
│   │   │   ├── startup_validation.py  # ⭐ API validation on startup
│   │   │   ├── climatiq_client.py     # Climatiq API integration
│   │   │   ├── confidence_manager.py  # AI confidence scoring
│   │   │   ├── emission_calculator.py # Carbon emissions calculation
│   │   │   ├── evidence_processor.py  # Evidence analysis
│   │   │   ├── orchestrator.py       # AI pipeline orchestration
│   │   │   ├── score_computer.py     # GreenScore calculation
│   │   │   ├── score_computation.py  # Production-ready scoring
│   │   │   └── sector_baseline.py    # Sector-specific baselines
│   │   │
│   │   ├── api/                  # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── auth.py           # ⭐ OTP and authentication endpoints
│   │   │   ├── evidence.py       # Evidence upload endpoints
│   │   │   └── ai_engine.py      # AI processing endpoints
│   │   │
│   │   ├── db/                   # Database configuration
│   │   │   ├── __init__.py       # Database session management
│   │   │   ├── models.py         # SQLAlchemy models
│   │   │   └── ai_models.py      # AI-related models
│   │   │
│   │   ├── monitoring/           # Observability infrastructure
│   │   │   ├── __init__.py       # Module exports
│   │   │   ├── logger.py         # Structured logging
│   │   │   ├── metrics.py        # Metrics collection
│   │   │   ├── health.py         # ⭐ Health checks (3 APIs)
│   │   │   ├── tracing.py        # Request tracing
│   │   │   ├── security.py       # Security middleware
│   │   │   └── error_handling.py # Exception handlers
│   │   │
│   │   ├── services/             # Business logic services
│   │   │   ├── __init__.py
│   │   │   ├── ai_service.py     # AI orchestration service
│   │   │   └── loan_service.py   # Loan processing service
│   │   │
│   │   ├── main.py               # ⭐ FastAPI app & startup event
│   │   ├── config.py             # Configuration management
│   │   ├── auth.py               # Authentication utilities
│   │   ├── models.py             # SQLAlchemy models
│   │   ├── schemas.py            # Pydantic schemas
│   │   ├── init_db.py            # Database initialization
│   │   └── utilis.py             # Utility functions
│   │
│   ├── alembic/                  # Database migrations
│   │   ├── versions/             # Migration scripts
│   │   └── env.py                # Alembic configuration
│   │
│   ├── tests/                    # Test suite
│   │   ├── test_endpoints.py
│   │   ├── test_ai_pipeline.py
│   │   └── conftest.py
│   │
│   ├── sample-data/              # Test data
│   │   └── solar-panel.jpg       # Used for Vision API validation
│   │
│   ├── keys/                     # API credentials
│   │   ├── google-vision.json    # Google Vision service account
│   │   ├── private_key.pem       # JWT signing (optional)
│   │   └── public_key.pem        # JWT verification (optional)
│   │
│   ├── .env                      # ⭐ Environment configuration
│   ├── requirements.txt          # Python dependencies
│   ├── start.py                  # Application startup script
│   ├── run.py                    # Alternative startup
│   └── alembic.ini               # Alembic configuration
│
├── frontend-web/                 # React frontend application
│   ├── src/
│   │   ├── Components/
│   │   │   ├── Bank/             # Bank portal components
│   │   │   │   ├── BankLogin.tsx
│   │   │   │   ├── BankDashboard.tsx
│   │   │   │   ├── PortfolioDashboard.tsx
│   │   │   │   └── CaseReview.tsx
│   │   │   │
│   │   │   ├── Ui/               # Reusable UI components
│   │   │   │   ├── button.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   ├── input-otp.tsx # ⭐ OTP input component
│   │   │   │   ├── card.tsx
│   │   │   │   └── ... (50+ ShadCN components)
│   │   │   │
│   │   │   └── BankApp.tsx       # Bank app container
│   │   │
│   │   ├── lib/
│   │   │   └── utils.ts          # Utility functions
│   │   │
│   │   ├── App.tsx               # Main app component
│   │   ├── main.tsx              # Application entry point
│   │   └── Guidelines/
│   │       └── Guidelines.md     # Development guidelines
│   │
│   ├── .env                      # Frontend environment variables
│   ├── package.json              # Node dependencies
│   ├── vite.config.ts            # Vite configuration
│   └── tsconfig.json             # TypeScript configuration
│
├── docs/                         # Documentation
│   ├── pitch.md                  # Product pitch
│   └── codebase-analysis-2025-10-01/  # ⭐ This analysis
│       ├── 00-OVERVIEW.md
│       ├── 01-CODEBASE-MAP.md   # (This file)
│       ├── 02-API-ANALYSIS.md
│       ├── 03-OTP-ANALYSIS.md
│       └── 04-IMPLEMENTATION-PLAN.md
│
├── USSD/                         # USSD implementation (future)
│   └── README.md
│
└── README.md                     # ⭐ Project README

```

---

## Key Files for Critical Issues

### API Logging (Priority 1)

**Primary Files:**
- `backend/app/ai/api_client.py` - API initialization and testing
- `backend/app/ai/startup_validation.py` - Validation orchestration
- `backend/app/monitoring/health.py` - Health check endpoints
- `backend/app/main.py` - Startup event handler

**Lines of Interest:**
- `api_client.py:66-85` - Gemini initialization
- `api_client.py:87-104` - Google Vision initialization
- `api_client.py:193-242` - Credential validation
- `api_client.py:244-253` - Gemini test (debug log)
- `api_client.py:280-304` - Climatiq test (debug log)
- `startup_validation.py:52-63` - Results logger
- `main.py:195-217` - Startup event

### OTP Delivery (Priority 2)

**Primary Files:**
- `backend/app/api/auth.py` - Authentication endpoints
- `backend/.env` - Configuration (SMS/Email credentials)
- `backend/app/config.py` - Settings class
- `frontend-web/src/Components/Ui/input-otp.tsx` - OTP input UI

**Lines of Interest:**
- `auth.py:204-245` - OTP sending endpoint
- `auth.py:233` - **THE CRITICAL LINE** (print statement)
- `auth.py:253-342` - OTP verification (working)
- `auth.py:68-86` - OTP storage (Redis)
- `.env:50-60` - SMS/Email configuration placeholders

---

## Critical File Purposes

### Backend Core

**`backend/app/main.py`**
- FastAPI application initialization
- Middleware configuration (CORS, security, monitoring)
- API router inclusion
- **Startup event handler** - Validates external APIs
- Health check endpoints
- Metrics endpoints

**`backend/app/config.py`**
- Environment variable loading via Pydantic
- Settings validation
- Database URLs
- API keys
- JWT configuration

**`backend/app/auth.py`**
- JWT token decoding
- Current user resolution
- Bearer token authentication dependency

### AI & External APIs

**`backend/app/ai/api_client.py`**
- **External API client** (Gemini, Vision, Climatiq)
- Circuit breaker pattern
- Retry with exponential backoff
- Credential validation
- Connection testing

**`backend/app/ai/startup_validation.py`**
- Orchestrates API validation on startup
- Logs validation results
- Checks critical services
- Returns availability summary

**`backend/app/ai/score_computation.py`**
- Production-ready GreenScore calculation
- Caching layer
- Multiple computation methods (AI-enhanced, rule-based, hybrid)
- Confidence scoring
- Fallback mechanisms

### Authentication

**`backend/app/api/auth.py`**
- **OTP generation and sending** (needs implementation)
- OTP verification and user creation
- JWT token issuance
- Password login (requires prior OTP)
- Rate limiting (3 requests per 10 minutes)
- Redis-backed OTP storage

### Monitoring & Observability

**`backend/app/monitoring/health.py`**
- Comprehensive health checks
- Database connectivity testing
- Redis connectivity testing
- MinIO storage testing
- **External API health checks** (Gemini, Vision, Climatiq)
- Application health metrics
- Response time tracking
- Cache management

**`backend/app/monitoring/logger.py`**
- Structured logging setup
- Log level configuration
- Format selection (simple/structured)
- Logger instances

**`backend/app/monitoring/metrics.py`**
- Metrics collection
- Request counting
- Error rate tracking
- Response time aggregation
- Health metrics

### Database

**`backend/app/models.py`**
- SQLAlchemy ORM models
- User, BusinessProfile, GreenScore, LoanApplication, Evidence, AuditLog
- UUID primary keys
- JSONB fields for flexible data
- Relationships and foreign keys

**`backend/app/db/__init__.py`**
- Database session management
- Session factory
- Dependency injection for routes

### Business Logic

**`backend/app/services/loan_service.py`**
- Loan quote generation
- Eligibility assessment
- Application submission
- Risk assessment
- Compliance checks
- Admin decision processing

**`backend/app/services/ai_service.py`**
- AI pipeline orchestration
- Evidence processing
- Score computation coordination

---

## Database Schema

**Users Table:**
- id (UUID, PK)
- phone (String, unique)
- email (String, unique)
- full_name (String)
- roles (JSONB)
- password_hash (String, nullable)
- last_otp_verified_at (DateTime)
- last_login_at (DateTime)
- created_at, updated_at

**Business Profiles Table:**
- id (UUID, PK)
- user_id (UUID, FK → users.id)
- business_type (String)
- business_name (String)
- consents (JSONB)
- created_at, updated_at

**Green Scores Table:**
- id (UUID, PK)
- user_id (UUID, FK → users.id)
- score (Float)
- subscores (JSONB)
- explanation_json (JSONB)
- computed_at (DateTime)
- created_at

**Loan Applications Table:**
- id (UUID, PK)
- user_id (UUID, FK → users.id)
- amount (Decimal)
- tenor_months (Integer)
- quoted_rate (Float)
- greenscore_snapshot (JSONB)
- status (String)
- created_at, updated_at

**Evidence Table:**
- id (UUID, PK)
- user_id (UUID, FK → users.id)
- evidence_type (String)
- file_path (String)
- analysis_result (JSONB)
- confidence (Float)
- verified_at (DateTime)
- created_at

**Audit Logs Table:**
- id (UUID, PK)
- actor_user_id (UUID, FK → users.id)
- action (String)
- entity (String)
- entity_id (UUID)
- payload (JSONB)
- audit_hmac (String) - Tamper detection
- created_at

---

## Frontend Structure

### Component Organization

**Bank Portal:** `frontend-web/src/Components/Bank/`
- Login screen with role selection
- Dashboard with application queue
- Portfolio analytics
- Case review with decision workflow

**UI Components:** `frontend-web/src/Components/Ui/`
- ShadCN UI library (Radix UI primitives)
- 50+ reusable components
- Consistent design system
- Tailwind CSS styling

### Key Frontend Files

**`frontend-web/src/App.tsx`**
- Main application routing
- App shell and layout

**`frontend-web/src/Components/BankApp.tsx`**
- Bank portal container
- Authentication state management
- Role-based view rendering

**`frontend-web/src/Components/Bank/BankLogin.tsx`**
- Login form
- Role selection (underwriter, manager, admin)
- Mock authentication (to be replaced with real OTP)

**`frontend-web/src/Components/Ui/input-otp.tsx`**
- OTP input component (6 digits)
- Built on `input-otp` library
- Ready to use, not yet integrated

---

## Configuration Files

### Backend Configuration

**`.env`** - Environment variables
- Database credentials
- Redis configuration
- JWT secrets
- API keys (Gemini, Vision, Climatiq)
- **SMS/Email placeholders** (need configuration)
- File storage settings
- CORS origins

**`requirements.txt`** - Python dependencies
- FastAPI, Uvicorn
- SQLAlchemy, Alembic, asyncpg
- Redis, Celery
- Boto3, MinIO
- Cryptography, python-jose
- ML libraries (numpy, pandas, scikit-learn)
- AI SDKs (google-generativeai, google-cloud-vision)

**`alembic.ini`** - Database migration configuration

### Frontend Configuration

**`package.json`** - Node dependencies
- React 18.2, TypeScript
- Vite build tool
- Radix UI components
- Tailwind CSS
- Axios for HTTP
- React Hook Form
- Recharts for visualizations

**`vite.config.ts`** - Vite configuration
- React plugin
- Path aliases
- Build optimization

**`tsconfig.json`** - TypeScript configuration
- Compiler options
- Path mappings
- Type checking rules

---

## Entry Points

### Backend Entry Points

1. **`backend/start.py`** (Recommended)
   - Loads .env file
   - Initializes database
   - Starts Uvicorn server
   - Hot reload in development

2. **`backend/run.py`** (Alternative)
   - Similar to start.py
   - Different configuration options

3. **Direct Uvicorn:**
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Entry Points

1. **Development Server:**
   ```bash
   npm run dev
   ```
   - Vite dev server
   - Hot module replacement
   - Port 5173

2. **Production Build:**
   ```bash
   npm run build
   npm run preview
   ```

---

## Data Flow

### Authentication Flow

```
User → Frontend (Phone/Email Input)
     → POST /auth/otp
     → Backend (Generate OTP)
     → Redis (Store hashed OTP, TTL 5min)
     → [MISSING] SMS/Email Delivery
     ← Response (status: "sent")

User → Frontend (Enter OTP Code)
     → POST /auth/verify
     → Backend (Validate OTP)
     → Redis (Retrieve & verify hash)
     → Database (Create/update user)
     ← JWT Token + User Data
```

### Evidence Processing Flow

```
User → Upload Evidence (POST /evidence)
     → MinIO/S3 Storage
     → AI Pipeline Orchestrator
     → Gemini AI (Text analysis)
     → Google Vision (Image OCR)
     → Confidence Manager
     → Evidence Processor
     ← Analysis Result + Confidence Score
```

### Score Computation Flow

```
User → Request Score (POST /score/compute)
     → Score Computation Service
     → Retrieve All Evidence
     → Calculate Sector Baseline
     → Apply Climatiq Emissions Data
     → Compute Subscores
     → AI-Enhanced Reasoning (Gemini)
     → Aggregate Total Score
     → Store in Database
     ← GreenScore + Breakdown + Explanations
```

### Loan Application Flow

```
User → Get Quote (POST /loan/quote)
     → Loan Service
     → Retrieve Latest GreenScore
     → Calculate Risk Factors
     → Dynamic Rate Calculation
     ← Quote with Terms

User → Apply (POST /loan/apply)
     → Loan Service
     → Eligibility Check
     → Compliance Validation
     → Store Application
     → Snapshot GreenScore
     ← Application ID + Status

Bank → Review (GET /admin/applications)
     → Filter by Status
     → Sort by Priority
     ← Application List

Bank → Decision (POST /admin/applications/{id}/decision)
     → Update Status
     → Create Audit Log
     → HMAC Signature
     ← Updated Application
```

---

## Deployment Architecture

### Production Stack

```
┌─────────────────┐
│   Load Balancer │
│    (Nginx)      │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│ Web   │ │ API   │
│ (Vite)│ │(FastAPI)
└───────┘ └───┬───┘
              │
      ┌───────┼───────┐
      │       │       │
  ┌───▼──┐ ┌─▼───┐ ┌─▼────┐
  │ Redis│ │ DB  │ │MinIO │
  │      │ │(PG) │ │(S3)  │
  └──────┘ └─────┘ └──────┘
```

### External Services

```
FastAPI Backend
    │
    ├──► Google Gemini AI
    │       (Text analysis)
    │
    ├──► Google Vision API
    │       (Image OCR)
    │
    ├──► Climatiq API
    │       (Emissions data)
    │
    ├──► Twilio (To be added)
    │       (SMS delivery)
    │
    └──► SMTP (To be added)
            (Email delivery)
```

---

## Security Layers

1. **API Gateway:** Rate limiting, CORS, security headers
2. **Authentication:** JWT with HS256, OTP verification
3. **Authorization:** Role-based access control
4. **Data:** Encrypted at rest, HTTPS in transit
5. **Audit:** HMAC-signed audit logs
6. **Input Validation:** Pydantic schemas, middleware
7. **External APIs:** Circuit breakers, retry logic

---

**Document Status:** Complete
**Last Updated:** 2025-10-01
