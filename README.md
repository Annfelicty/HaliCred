# HaliCred

HaliCred is an AI-powered eco-finance platform that transforms sustainable actions into financial credibility using Google Gemini 2.5 Pro AI engine. By analyzing evidence of green practices, the platform generates GreenScores that enable access to climate-friendly financing.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- PostgreSQL 13+
- Redis (optional, for caching)

### 1. Environment Setup
Copy and configure the environment variables:
```bash
cp .env.example .env
```

**Required Environment Variables:**
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/haliscore

# AI Services
GEMINI_API_KEY=your_gemini_api_key_here

# JWT Authentication
JWT_SECRET_KEY=your_jwt_secret_here
JWT_PRIVATE_KEY_PATH=./keys/private_key.pem
JWT_PUBLIC_KEY_PATH=./keys/public_key.pem

# Basic Configuration
DEBUG=true
ENVIRONMENT=development
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Generate JWT keys
mkdir keys
openssl genrsa -out keys/private_key.pem 2048
openssl rsa -in keys/private_key.pem -pubout -out keys/public_key.pem

# Run database migrations (requires PostgreSQL)
alembic upgrade head

# Start the backend server
python start.py
```

Backend will be available at: `http://localhost:8000`

### 3. Frontend Setup
```bash
cd frontend-web
npm install
./start.sh
```

Frontend will be available at: `http://localhost:5173`

## 🏗️ Architecture

### Backend (FastAPI)
- **AI Engine**: Gemini 2.5 Pro integration with function calling
- **Database**: PostgreSQL with comprehensive AI data models
- **Authentication**: JWT with RS256 signing
- **API Routes**: 
  - `/auth` - Authentication endpoints
  - `/ai` - AI processing and GreenScore management
  - `/loans` - Loan applications and offers
  - `/admin` - Bank/admin functions

### Frontend (React + TypeScript)
- **SME App**: Business onboarding, evidence upload, GreenScore dashboard
- **Bank App**: Loan application review, portfolio management
- **API Integration**: Axios-based client with authentication
- **State Management**: React hooks for auth, GreenScore, and loans

### AI Engine Components
- **Orchestrator**: Coordinates AI microservices using Gemini
- **Evidence Processing**: OCR, computer vision, emission calculations
- **Scoring**: Multi-pillar GreenScore computation with sector baselines
- **Carbon Credits**: Automatic carbon credit calculations and aggregation
- **Confidence Management**: Human-in-loop review system

## 📊 Features

### For SMEs
- **Evidence Upload**: Photos, receipts, certificates of green practices
- **AI Analysis**: Automated processing using computer vision and NLP
- **GreenScore**: Real-time sustainability scoring (0-100)
- **Carbon Credits**: Automatic carbon credit calculations
- **Loan Access**: Green financing based on sustainability performance

### For Banks
- **Application Review**: AI-powered loan application assessment
- **Risk Analysis**: GreenScore-based creditworthiness evaluation
- **Portfolio Management**: Track green loan performance
- **Sector Analytics**: Industry benchmarks and trends

### AI Capabilities
- **Computer Vision**: Solar panel detection, equipment recognition
- **OCR**: Receipt and document text extraction
- **Emission Calculations**: CO2 impact quantification
- **Sector Baselines**: Kenya-specific sustainability benchmarks
- **Confidence Scoring**: Fraud detection and review triggers

## 🔧 Configuration

### Database Models
The platform includes comprehensive database models for:
- User management and business profiles
- AI evidence processing and results
- GreenScore calculations and history
- Carbon credit tracking and aggregation
- Human review cases and audit logs

### API Endpoints

**Authentication:**
- `POST /auth/register` - User registration
- `POST /auth/token` - Login and token generation

**AI Engine:**
- `POST /ai/evidence/process` - Upload and process evidence
- `GET /ai/greenscore/current` - Get current GreenScore
- `GET /ai/greenscore/history` - GreenScore trends
- `GET /ai/carbon-credits/portfolio` - Carbon credits summary

**Loans:**
- `POST /loans/apply` - Submit loan application
- `GET /loans/offers` - Available loan offers
- `POST /loans/{id}/accept` - Accept loan offer

## 🧪 Testing

### Backend Testing
```bash
cd backend
pytest tests/
```

### Frontend Testing
```bash
cd frontend-web
npm test
```

### Integration Testing
1. Start backend: `cd backend && python start.py`
2. Start frontend: `cd frontend-web && ./start.sh`
3. Navigate to `http://localhost:5173`
4. Test SME and Bank workflows

## 🚀 Deployment

### Environment Variables for Production
Update `.env` with production values:
- Set `DEBUG=false`
- Configure production database URL
- Add real API keys (Gemini, external services)
- Set secure JWT keys
- Configure CORS for production domains

### Docker Deployment (Optional)
```bash
# Build and run with Docker Compose
docker-compose up --build
```

## 📚 API Documentation

Interactive API documentation available at:
- Development: `http://localhost:8000/docs`
- Redoc: `http://localhost:8000/redoc`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `pytest` and `npm test`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the API documentation at `/docs`
- Review the configuration in `.env`
- Ensure all required environment variables are set
- Verify database connection and migrations

Refer to the documentation in the `docs/` folder for more details on project setup and workflows.
