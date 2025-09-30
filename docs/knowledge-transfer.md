# HaliCred Knowledge Transfer Documentation

## Overview

This document serves as a comprehensive knowledge transfer guide for the HaliCred AI-powered green credit scoring platform. It provides essential information for developers, operations teams, and stakeholders taking over the maintenance and enhancement of the system.

## Project Summary

### Platform Overview

HaliCred is an AI-driven platform that empowers SMEs, farmers, and informal workers to access affordable loans by proving their climate-friendly practices. The system converts eco-actions into quantifiable green scores, which banks use to offer better loan terms while SMEs earn carbon credits.

### Key Value Propositions
- **For SMEs**: Higher green scores = lower interest rates + carbon credit income
- **For Banks**: Reduced risk through AI-verified sustainability evidence
- **For Environment**: Quantified CO2 reductions and climate impact tracking

### Current System Status
- **Phase 6**: Comprehensive testing infrastructure (100% complete)
- **Phase 7**: Documentation and handover (100% complete)
- **Production Ready**: Full deployment capability with monitoring
- **Test Coverage**: 350+ test cases across all components

## Technical Architecture

### System Components

#### Backend (Python/FastAPI)
- **Location**: `backend/`
- **Framework**: FastAPI with SQLAlchemy ORM
- **Database**: PostgreSQL 15 with PostGIS extension
- **Caching**: Redis for sessions and background tasks
- **File Storage**: MinIO/S3 for evidence files

#### Frontend (React/TypeScript)
- **Location**: `frontend-web/`
- **Framework**: React with Vite build system
- **UI Library**: Tailwind CSS + ShadCN UI components
- **State Management**: React hooks and context
- **Testing**: Jest + React Testing Library + Playwright E2E

#### AI Pipeline
- **Google Gemini**: LLM orchestration and function calling
- **Google Vision**: OCR and computer vision analysis
- **Climatiq API**: Emission factors and calculations
- **Custom Logic**: Score computation and credit aggregation

### Data Flow Architecture

```mermaid
graph LR
    A[SME Evidence Upload] --> B[AI Orchestrator]
    B --> C[Evidence Processor]
    B --> D[Emission Calculator]
    B --> E[Score Computer]

    C --> F[Google Vision API]
    D --> G[Climatiq API]
    E --> H[Green Score Result]

    H --> I[Bank Portal]
    H --> J[Loan Processing]

    E --> K[Carbon Credit Pool]
    K --> L[Carbon Trading]
```

### Key Integrations

#### External APIs
- **Gemini API**: `models/gemini-2.5-flash` for AI orchestration
- **Google Vision**: OCR and image analysis (service account auth)
- **Climatiq GA**: Emission factor database and calculations
- **Africa's Talking**: SMS/USSD services (optional)

#### Authentication & Security
- **JWT Tokens**: Phone-based OTP authentication
- **Role-Based Access**: SME, Bank, Admin user types
- **Rate Limiting**: API protection and quota management
- **Data Encryption**: At rest and in transit

## Codebase Structure

### Backend Architecture

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry
│   ├── config.py            # Configuration management
│   ├── auth.py              # Authentication utilities
│   ├── utilis.py            # Utility functions
│   │
│   ├── api/                 # API route handlers
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── evidence.py      # Evidence management
│   │   └── ai_engine.py     # AI processing endpoints
│   │
│   ├── ai/                  # AI processing pipeline
│   │   ├── orchestrator.py  # Main AI coordinator
│   │   ├── evidence_processor.py
│   │   ├── emission_calculator.py
│   │   ├── score_computation.py
│   │   └── carbon_credit.py
│   │
│   ├── db/                  # Database models and utilities
│   │   ├── models.py        # SQLAlchemy models
│   │   └── ai_models.py     # AI-specific models
│   │
│   ├── services/            # Business logic services
│   │   ├── ai_service.py    # AI service coordination
│   │   └── loan_service.py  # Loan processing logic
│   │
│   └── monitoring/          # Monitoring and observability
│       ├── logger.py        # Structured logging
│       ├── metrics.py       # Performance metrics
│       └── health.py        # Health check endpoints
│
├── tests/                   # Comprehensive test suite
│   ├── conftest.py          # Test configuration
│   ├── test_api_comprehensive.py
│   ├── test_database_integration.py
│   ├── test_auth_comprehensive.py
│   ├── test_ai_processing.py
│   ├── test_loan_system.py
│   ├── test_monitoring_security.py
│   └── test_performance.py
│
├── alembic/                 # Database migrations
├── keys/                    # API keys and certificates
└── run_tests.py            # Test runner with multiple modes
```

### Frontend Architecture

```
frontend-web/
├── src/
│   ├── App.tsx              # Main application component
│   ├── main.tsx             # Application entry point
│   │
│   ├── Components/          # React components
│   │   ├── Sme/             # SME user interface
│   │   │   ├── SMEDashboard.tsx
│   │   │   ├── EvidenceUpload.tsx
│   │   │   └── LoanOffers.tsx
│   │   ├── Bank/            # Bank portal interface
│   │   │   ├── BankDashboard.tsx
│   │   │   └── CaseReview.tsx
│   │   └── Ui/              # Shared UI components
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       └── loading.tsx
│   │
│   ├── hooks/               # Custom React hooks
│   │   ├── useAuth.ts       # Authentication hook
│   │   ├── useGreenScore.ts # Green score management
│   │   └── useLoans.ts      # Loan data management
│   │
│   ├── lib/                 # Utility libraries
│   │   ├── api.ts           # API client configuration
│   │   └── utils.ts         # Helper functions
│   │
│   ├── test/                # Testing infrastructure
│   │   ├── setup.ts         # Test environment setup
│   │   ├── utils/test-utils.tsx
│   │   └── mocks/server.ts  # MSW mock server
│   │
│   └── e2e/                 # End-to-end tests
│       ├── auth.spec.ts
│       ├── loan-application.spec.ts
│       └── evidence-upload.spec.ts
│
├── jest.config.js           # Jest test configuration
├── playwright.config.ts     # Playwright E2E config
└── package.json             # Dependencies and scripts
```

## Key Technical Decisions

### Architecture Decisions

#### Why FastAPI?
- **Performance**: High-performance async framework
- **Documentation**: Automatic OpenAPI/Swagger docs
- **Type Safety**: Native Python type hints
- **Ecosystem**: Rich ecosystem for AI/ML integrations

#### Why React with Vite?
- **Developer Experience**: Fast builds and hot reload
- **TypeScript**: Type safety for large codebase
- **Component Library**: ShadCN for consistent UI
- **Testing**: Mature testing ecosystem

#### Why PostgreSQL?
- **Geospatial**: PostGIS for location-based features
- **JSON Support**: JSONB for flexible AI result storage
- **Performance**: Excellent for complex queries
- **Reliability**: ACID compliance and backup capabilities

### AI Pipeline Decisions

#### Why Google Gemini?
- **Function Calling**: Excellent for orchestrating AI pipelines
- **Performance**: Fast response times for real-time use
- **Reliability**: Google's enterprise-grade infrastructure
- **Cost**: Competitive pricing for high-volume usage

#### Why Climatiq API?
- **Data Quality**: High-quality emission factor database
- **Coverage**: Comprehensive activity coverage
- **Standards**: Aligned with international emission standards
- **Regional Data**: Kenya-specific emission factors

#### Why Confidence Scoring?
- **Quality Control**: Ensures reliability of AI results
- **User Trust**: Transparency in AI decision-making
- **Fallback Logic**: Enables manual review for low confidence
- **Continuous Improvement**: Feedback loop for model enhancement

## Environment Configuration

### Development Environment

#### Required Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/halicred_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# AI Services
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_VISION_API_KEY=your_google_vision_key
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
CLIMATIQ_API_KEY=your_climatiq_api_key

# File Storage
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
BUCKET_NAME=halicred-dev-files

# Security
SECRET_KEY=your_256_bit_secret
ALGORITHM=HS256

# Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
```

#### Setup Instructions
1. **Clone Repository**: `git clone https://github.com/Annfelicty/hali-cred.git`
2. **Backend Setup**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your credentials
   alembic upgrade head
   uvicorn app.main:app --reload
   ```
3. **Frontend Setup**:
   ```bash
   cd frontend-web
   npm install
   cp .env.example .env.local
   # Edit .env.local with API URLs
   npm run dev
   ```

### Production Environment

#### Infrastructure Requirements
- **Server**: Ubuntu 20.04+ with 8GB RAM, 4+ CPU cores
- **Database**: PostgreSQL 15+ with PostGIS extension
- **Cache**: Redis 7+ for session management
- **Storage**: S3-compatible object storage
- **Monitoring**: Prometheus + Grafana for observability

#### Deployment Process
1. **Server Preparation**: Install Docker, Docker Compose, PostgreSQL
2. **Environment Setup**: Configure production environment variables
3. **Database Migration**: Run Alembic migrations
4. **Application Deployment**: Use Docker Compose for containerization
5. **SSL Configuration**: Setup Let's Encrypt certificates
6. **Monitoring Setup**: Configure Prometheus metrics collection

## Critical Knowledge Areas

### AI Pipeline Understanding

#### Evidence Processing Flow
1. **File Upload**: SME uploads evidence (photo/document)
2. **Preprocessing**: File validation and optimization
3. **AI Orchestration**: Gemini coordinates processing pipeline
4. **OCR/Vision**: Google Vision extracts text and identifies objects
5. **Feature Extraction**: Extract sustainability-relevant information
6. **Emission Calculation**: Climatiq API calculates environmental impact
7. **Score Computation**: Algorithm converts impact to green score
8. **Credit Calculation**: Determine carbon credits earned

#### Confidence Management
- **High Confidence (80-100%)**: Automatic processing and scoring
- **Medium Confidence (60-79%)**: Automatic with monitoring
- **Low Confidence (40-59%)**: Flagged for manual review
- **Very Low (<40%)**: Rejected with feedback for improvement

#### Fallback Mechanisms
- **AI Service Outages**: Deterministic scoring algorithms
- **Low Confidence**: Human review workflows
- **Data Quality**: Request additional evidence
- **Regional Limitations**: Default to global emission factors

### Database Schema Critical Points

#### Core Relationships
- `User` (1) → (1) `BusinessProfile`: Business information
- `User` (1) → (N) `Evidence`: Uploaded sustainability evidence
- `User` (1) → (N) `GreenScore`: Historical green scores
- `User` (1) → (N) `LoanApplication`: Loan requests
- `Evidence` (1) → (1) `AIEvidence`: AI processing results

#### Data Integrity
- **UUID Primary Keys**: All tables use UUID for global uniqueness
- **Audit Logging**: All changes tracked in `audit_logs` table
- **JSONB Storage**: Flexible schema for AI results and evidence data
- **Geospatial Data**: PostGIS for location-based analysis

#### Performance Considerations
- **Indexes**: Strategic indexing on user_id, status, created_at
- **Partitioning**: Consider partitioning large tables by date
- **Connection Pooling**: Configure appropriate pool sizes
- **Query Optimization**: Monitor slow queries and optimize

### Security Implementation

#### Authentication Flow
1. **Phone Verification**: SMS OTP to +254XXXXXXXXX format
2. **JWT Generation**: Signed tokens with user claims
3. **Token Validation**: Middleware validates all protected routes
4. **Role-Based Access**: SME, Bank, Admin role enforcement

#### Data Protection
- **Encryption at Rest**: Database and file storage encryption
- **Encryption in Transit**: TLS 1.3 for all communications
- **PII Handling**: Minimal collection and secure processing
- **Audit Trail**: Comprehensive logging for compliance

#### API Security
- **Rate Limiting**: Per-user and per-IP rate limits
- **Input Validation**: Strict validation on all inputs
- **Error Handling**: Secure error messages without information leakage
- **CORS Configuration**: Restricted to allowed origins

## Operational Procedures

### Monitoring and Alerting

#### Key Metrics to Monitor
- **API Response Times**: 95th percentile < 500ms
- **Error Rates**: < 1% across all endpoints
- **AI Processing Success**: > 95% successful processing
- **Database Performance**: Query times and connection pool usage
- **External API Health**: Gemini, Vision, Climatiq availability

#### Critical Alerts
- **API Downtime**: Immediate escalation
- **Database Connectivity**: High priority alert
- **AI Service Failures**: Medium priority with fallback activation
- **High Error Rates**: Investigate within 15 minutes
- **Resource Exhaustion**: CPU, memory, disk space alerts

#### Health Check Endpoints
- `/health`: Overall system health
- `/health/db`: Database connectivity
- `/health/ai`: AI services status
- `/health/redis`: Cache system status

### Backup and Recovery

#### Backup Strategy
- **Database**: Daily full backups with point-in-time recovery
- **Files**: S3 cross-region replication
- **Configuration**: Git-based infrastructure as code
- **Secrets**: Secure key management system

#### Recovery Procedures
- **RTO (Recovery Time Objective)**: 4 hours for full system
- **RPO (Recovery Point Objective)**: 1 hour for data loss
- **Disaster Recovery**: Multi-region deployment capability
- **Backup Validation**: Monthly restore testing

### Maintenance Procedures

#### Regular Maintenance
- **Weekly**: Database VACUUM and ANALYZE
- **Monthly**: Security updates and dependency upgrades
- **Quarterly**: Performance optimization review
- **Annually**: Security audit and penetration testing

#### Deployment Procedures
1. **Testing**: Full test suite execution in staging
2. **Database Migration**: Alembic migration review and execution
3. **Blue-Green Deployment**: Zero-downtime deployment process
4. **Rollback Plan**: Automated rollback for failed deployments
5. **Monitoring**: Enhanced monitoring during and after deployment

## Known Issues and Limitations

### Current Technical Debt

#### AI Pipeline Limitations
- **Single Region**: Currently optimized for Kenya-specific data
- **Language Support**: English-only OCR and processing
- **Batch Processing**: No bulk evidence processing capabilities
- **Cache Strategy**: Limited caching of AI results

#### Performance Bottlenecks
- **Large File Processing**: 20MB limit may be restrictive
- **Concurrent AI Calls**: No rate limiting for external APIs
- **Database Queries**: Some complex green score queries need optimization
- **Frontend Bundle Size**: Could benefit from code splitting

#### Security Considerations
- **API Key Rotation**: Manual process, needs automation
- **Session Management**: Redis-dependent, needs fallback
- **Audit Log Retention**: No automated cleanup policy
- **File Upload Validation**: Basic validation, needs enhancement

### Future Enhancement Opportunities

#### Phase 8 Planned Improvements
- **Multi-language Support**: Swahili OCR and interface
- **Advanced ML Models**: Custom-trained models for Kenya context
- **Real-time Processing**: Stream processing for instant results
- **Mobile Optimization**: Enhanced mobile app performance

#### Scalability Improvements
- **Microservices**: Break down monolithic AI pipeline
- **Kubernetes**: Container orchestration for better scaling
- **Database Sharding**: Horizontal scaling for large datasets
- **CDN Integration**: Global content delivery network

#### Feature Enhancements
- **Bulk Operations**: Batch evidence processing
- **Advanced Analytics**: Machine learning for fraud detection
- **Integration APIs**: Third-party system integrations
- **White-label Solutions**: Multi-tenant architecture

## Team Handover Information

### Development Team Structure

#### Backend Team Responsibilities
- **API Development**: RESTful endpoint implementation
- **Database Design**: Schema evolution and optimization
- **AI Integration**: External service integration and coordination
- **Performance**: Query optimization and caching strategies

#### Frontend Team Responsibilities
- **User Experience**: SME and bank portal interfaces
- **Component Library**: Reusable UI component maintenance
- **Testing**: Unit, integration, and E2E test coverage
- **Performance**: Bundle optimization and loading performance

#### DevOps Team Responsibilities
- **Infrastructure**: Server provisioning and management
- **Deployment**: CI/CD pipeline maintenance
- **Monitoring**: System observability and alerting
- **Security**: Infrastructure and application security

### Key Contacts and Responsibilities

#### Technical Leadership
- **Backend Lead**: Responsible for API architecture and AI pipeline
- **Frontend Lead**: Responsible for user interface and experience
- **DevOps Lead**: Responsible for infrastructure and deployment
- **Security Lead**: Responsible for security architecture and compliance

#### External Relationships
- **Google Cloud**: AI services support and quota management
- **Climatiq**: Emission data API support and updates
- **AWS/Cloud Provider**: Infrastructure support and billing
- **Regulatory Bodies**: Compliance and reporting requirements

### Knowledge Transition Checklist

#### Technical Knowledge Transfer
- [ ] Codebase walkthrough with detailed explanation
- [ ] AI pipeline deep-dive and troubleshooting
- [ ] Database schema and migration procedures
- [ ] Deployment and rollback procedures
- [ ] Monitoring and alerting configuration

#### Operational Knowledge Transfer
- [ ] Incident response procedures and escalation paths
- [ ] Backup and recovery testing
- [ ] Security protocols and compliance requirements
- [ ] Performance optimization techniques
- [ ] Third-party service management

#### Business Knowledge Transfer
- [ ] Product requirements and roadmap understanding
- [ ] User personas and journey mapping
- [ ] Business metrics and KPI tracking
- [ ] Regulatory compliance requirements
- [ ] Go-to-market strategy and customer feedback

## Resources and References

### Documentation Links
- **API Documentation**: `/docs/api-documentation.md`
- **Architecture Guide**: `/docs/architecture.md`
- **Deployment Guide**: `/docs/deployment-guide.md`
- **Monitoring Runbook**: `/docs/monitoring-runbook.md`
- **User Guides**: `/docs/user-guide-sme.md`, `/docs/user-guide-bank.md`

### External Resources
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **React Documentation**: https://react.dev/
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/
- **Google Cloud AI**: https://cloud.google.com/ai/
- **Climatiq API**: https://docs.climatiq.io/

### Training Materials
- **Video Tutorials**: Internal team training recordings
- **Code Walkthroughs**: Detailed component explanations
- **Architecture Decisions**: Historical decision documentation
- **Best Practices**: Development and operational guidelines

### Support Channels
- **Internal Documentation**: Confluence/Wiki system
- **Code Repository**: GitHub with detailed commit history
- **Issue Tracking**: GitHub Issues with labels and milestones
- **Communication**: Slack channels for real-time discussion

---

**Document Version**: 7.0.0
**Knowledge Transfer Date**: September 30, 2025
**Next Review**: March 30, 2026
**Prepared By**: HaliCred Development Team
**Approved By**: Technical Leadership Team