# HaliScore Backend - Local Development Setup

## Overview
HaliScore is an AI-powered eco-finance platform that transforms sustainable actions into financial credibility. This backend provides APIs for user authentication, evidence management, AI-powered Green Score calculation, and loan management.

### Phase 7 Highlights
- Live AI orchestration now runs against external services (Google Gemini, Google Vision, Climatiq GA API) with no simulation fallbacks.
- `AIService.process_evidence_request()` streams evidence through `AIOrchestrator`, persisting genuine `GreenScoreResult` rows.
- Climatiq GA factor discovery requires a valid `activity_id`/`data_version`; see [AI Services](#ai-services) for current guidance.

## Prerequisites

### System Requirements
- Python 3.10 or higher
- PostgreSQL 13 or higher
- Redis 6 or higher
- MinIO (S3-compatible storage)

### Python Dependencies
All dependencies are listed in `requirements.txt` and include:
- FastAPI for API framework
- SQLAlchemy for database ORM
- Celery for background tasks
- OpenCV and Tesseract for OCR
- Machine learning libraries (scikit-learn, numpy, pandas)

## Installation & Setup

### 1. Clone and Setup Python Environment
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Install System Dependencies

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib redis-server tesseract-ocr tesseract-ocr-eng
```

#### macOS:
```bash
brew install postgresql redis tesseract
```

#### Windows:
- Install PostgreSQL from https://www.postgresql.org/download/windows/
- Install Redis from https://redis.io/download
- Install Tesseract from https://github.com/UB-Mannheim/tesseract/wiki

### 3. Setup Database
```bash
# Create database
sudo -u postgres createdb haliscore
sudo -u postgres createuser user
sudo -u postgres psql -c "ALTER USER user WITH PASSWORD 'password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE haliscore TO user;"
```

### 4. Setup MinIO (S3-compatible storage)
```bash
# Download MinIO
wget https://dl.min.io/server/minio/release/linux-amd64/minio
### 5. Environment Configuration
Create a `.env` file in the backend directory:
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/haliscore

# JWT Authentication
JWT_PRIVATE_KEY_PATH=jwtRS256.key
JWT_PUBLIC_KEY_PATH=jwtRS256.key.pub
JWT_ALGORITHM=RS256
JWT_EXPIRY_HOURS=24

# S3/MinIO Storage
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=haliscore

# Redis and Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Security
AUDIT_HMAC_SECRET=your-secret-key-here
SECRET_KEY=your-secret-key-change-in-production

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# Environment
ENVIRONMENT=development
DEBUG=true

# AI Integrations (Phase 7)
GEMINI_API_KEY=your-gemini-api-key
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/google-vision.json
CLIMATIQ_API_KEY=your-climatiq-api-key
CLIMATIQ_DATA_VERSION=26.26
GOOGLE_VISION_CREDENTIALS_PATH=/absolute/path/to/google-vision.json  # optional alias
AI_EVIDENCE_TMP_DIR=./uploads/tmp
```

### 6. Generate JWT Keys (Optional)
```bash
# Generate RSA key pair for JWT
openssl genrsa -out jwtRS256.key 2048
openssl rsa -in jwtRS256.key -pubout -out jwtRS256.key.pub
```

### 7. Initialize Database
```bash
# Initialize database tables
python app/init_db.py

# Run migrations (if using Alembic)
alembic upgrade head
```

## Running the Application

### 1. Start Required Services
```bash
# Start PostgreSQL (if not running as service)
sudo systemctl start postgresql

# Start Redis (if not running as service)
sudo systemctl start redis

# Start MinIO (in a separate terminal)
./minio server /tmp/minio --console-address ":9001"
```

### 2. Start Celery Worker (Background Tasks)
```bash
# In a separate terminal
celery -A app.utilis.celery_app worker --loglevel=info
```

### 3. Start the Backend Server
```bash
# Development mode with auto-reload
python run.py

# Or using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Documentation

Once the server is running, you can access:
- **API Documentation**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Key API Endpoints

### Authentication
- `POST /auth/otp` - Send OTP to phone number
- `POST /auth/verify` - Verify OTP and get JWT token

### User Profile
- `GET /me` - Get current user info
- `POST /me/consents` - Save user consents
- `PATCH /me/profile` - Update user profile

### Evidence Management
- `POST /evidence` - Create evidence upload URL
- `POST /evidence/{id}/finalize` - Finalize evidence processing

### Green Score
- `POST /score/compute` - Compute AI-powered Green Score
- `GET /score/me` - Get current user's Green Score

### AI Engine
- `POST /ai/evidence/process` - Run evidence through the live AI orchestrator
- `GET /ai/greenscore/current` - Fetch the most recent AI-generated score
- `GET /ai/greenscore/history` - Retrieve score history
- `GET /ai/carbon-credits/portfolio` - Summaries of projected carbon credits

### Loan Management
- `POST /loan/quote` - Get loan quote based on Green Score
- `POST /loan/apply` - Apply for loan

### Admin (Underwriter)
- `GET /admin/applications` - List loan applications
- `POST /admin/applications/{id}/decision` - Approve/decline loan

## AI Features

### Green Score Calculation
The platform uses AI to analyze:
- Receipt images for sustainable purchases
- Business type and location data
- Historical evidence of climate-smart practices

### OCR Processing
- Automatic text extraction from receipt images
- Detection of sustainable product purchases
- Integration with climate-smart practice database

### Background Processing
- Celery workers handle OCR processing
- Async evidence analysis
- Real-time score updates

### AI Services
- Gemini orchestrates function calls to internal services.
- Google Vision provides OCR + CV. Ensure `GOOGLE_APPLICATION_CREDENTIALS` points to a service account JSON with Vision scopes.
- Climatiq GA `/data/v1/search` + `/data/v1/estimate` require a whitelisted `activity_id` and `data_version`. Current fallback: `electricity-supply_grid-source_residual_mix` with `26.26` (verify availability for your key).

#### Verifying External Integrations
```bash
# Gemini sanity check
python backend/run_live_ai_checks.py

# Individual curl for Climatiq search
curl -H "Authorization: Bearer $CLIMATIQ_API_KEY" \
  "https://api.climatiq.io/data/v1/search?activity_id=electricity-supply_grid-source_residual_mix&data_version=26.26&results_per_page=1"

# Google Vision basic OCR (requires gcloud SDK)
python - <<'PY'
from google.cloud import vision
from google.oauth2 import service_account
creds = service_account.Credentials.from_service_account_file('backend/keys/google-vision.json')
client = vision.ImageAnnotatorClient(credentials=creds)
with open('backend/sample-data/solar-panel.jpg','rb') as fh:
    image = vision.Image(content=fh.read())
print(client.label_detection(image=image).label_annotations[0].description)
PY
```

## Development Workflow

### Testing
```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=app tests/
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Code Quality
```bash
# Format code
black app/
isort app/

# Lint code
flake8 app/
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure PostgreSQL is running
   - Check DATABASE_URL in .env file
   - Verify database and user exist

2. **Redis Connection Error**
   - Ensure Redis is running
   - Check CELERY_BROKER_URL in .env file

3. **S3/MinIO Error**
   - Ensure MinIO is running
   - Check S3 credentials in .env file
   - Verify bucket exists

4. **OCR Processing Error**
   - Ensure Tesseract is installed
   - Check image file permissions
   - Verify image format is supported

5. **Gemini API Error**
   - Confirm `GEMINI_API_KEY` is loaded (no trailing spaces)
   - Ensure the `models/gemini-2.5-flash` model is enabled for your project
   - Monitor quota usage in the Google AI Studio console

6. **Google Vision Credential Error**
   - Path in `GOOGLE_APPLICATION_CREDENTIALS` must be absolute
   - Service account requires `roles/vision.user`
   - For container deployments, mount the credential JSON and set permissions

7. **Climatiq 400 `no_emission_factors_found`**
   - Confirm the requested `activity_id` exists in your catalog tier
   - Try broadening `region` to `GLO` or using `lax=true`
   - Reach out to Climatiq support to confirm dataset access or adjust `data_version`

### Logs
- Application logs: Check terminal output
- Celery logs: Check Celery worker terminal
- Database logs: Check PostgreSQL logs

## Production Deployment

For production deployment:
1. Set `ENVIRONMENT=production`
2. Use proper JWT keys
3. Configure proper CORS origins
4. Set up proper database credentials
5. Use production-grade Redis and PostgreSQL
6. Configure proper logging
7. Set up monitoring and health checks

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review API documentation
3. Check logs for error messages
4. Verify all services are running
