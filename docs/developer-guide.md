# HaliCred Developer Guide

## Overview

This guide provides comprehensive information for developers working on the HaliCred platform. It covers setup procedures, development workflows, coding standards, and best practices for contributing to the codebase.

## Getting Started

### Prerequisites

#### System Requirements
- **Operating System**: Windows 10+, macOS 10.15+, or Ubuntu 18.04+
- **Memory**: 8GB RAM minimum (16GB recommended)
- **Storage**: 10GB free space for development environment
- **Network**: Stable internet connection for API integrations

#### Required Software
- **Node.js**: Version 18+ (LTS recommended)
- **Python**: Version 3.11+
- **Git**: Version 2.20+
- **Docker**: Latest version (for containerized development)
- **PostgreSQL**: Version 15+ (or use Docker)
- **Redis**: Version 7+ (or use Docker)

#### Development Tools
- **Code Editor**: VS Code (recommended) with extensions:
  - Python extension pack
  - TypeScript and JavaScript
  - Prettier for code formatting
  - ESLint for JavaScript/TypeScript
  - Python Docstring Generator
- **API Testing**: Postman or similar tool
- **Database Tool**: pgAdmin, DBeaver, or similar

### Repository Setup

#### Cloning the Repository
```bash
git clone https://github.com/Annfelicty/hali-cred.git
cd hali-cred
```

#### Repository Structure
```
hali-cred/
├── backend/                 # FastAPI backend application
├── frontend-web/           # React web application
├── docs/                   # Documentation
├── .github/                # GitHub workflows and templates
├── docker-compose.yml      # Development environment
└── README.md              # Project overview
```

### Development Environment Setup

#### Backend Setup

1. **Navigate to Backend Directory**
   ```bash
   cd backend
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your configuration:
   ```bash
   # Database
   DATABASE_URL=postgresql://halicred:password@localhost:5432/halicred_dev

   # Redis
   REDIS_URL=redis://localhost:6379/0

   # AI Services (get your own API keys)
   GEMINI_API_KEY=your_gemini_api_key_here
   GOOGLE_VISION_API_KEY=your_google_vision_api_key_here
   CLIMATIQ_API_KEY=your_climatiq_api_key_here

   # Development settings
   ENVIRONMENT=development
   DEBUG=true
   LOG_LEVEL=DEBUG
   ```

5. **Database Setup**
   ```bash
   # Start PostgreSQL (if using Docker)
   docker run --name halicred-postgres -e POSTGRES_PASSWORD=password -e POSTGRES_USER=halicred -e POSTGRES_DB=halicred_dev -p 5432:5432 -d postgres:15

   # Run migrations
   alembic upgrade head
   ```

6. **Start Development Server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

#### Frontend Setup

1. **Navigate to Frontend Directory**
   ```bash
   cd frontend-web
   ```

2. **Install Dependencies**
   ```bash
   npm install
   ```

3. **Environment Configuration**
   ```bash
   cp .env.example .env.local
   ```

   Edit `.env.local`:
   ```bash
   VITE_API_BASE_URL=http://localhost:8000
   VITE_APP_ENV=development
   ```

4. **Start Development Server**
   ```bash
   npm run dev
   ```

#### Docker Development Environment

For a complete development environment with all services:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### API Keys and External Services

#### Google Gemini API
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create new API key
3. Add to `.env` as `GEMINI_API_KEY`

#### Google Vision API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Vision API
3. Create service account and download JSON key
4. Place JSON file in `backend/keys/` directory
5. Set `GOOGLE_APPLICATION_CREDENTIALS` path in `.env`

#### Climatiq API
1. Register at [Climatiq](https://www.climatiq.io/)
2. Generate API key
3. Add to `.env` as `CLIMATIQ_API_KEY`

## Development Workflow

### Git Workflow

#### Branch Strategy
- **main**: Production-ready code
- **develop**: Integration branch for features
- **feature/**: Feature development branches
- **hotfix/**: Critical bug fixes

#### Creating Feature Branches
```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

#### Making Changes
```bash
# Make your changes
git add .
git commit -m "feat: add green score calculation algorithm"

# Push to remote
git push origin feature/your-feature-name
```

#### Commit Message Format
Follow conventional commits:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `test:` Adding or modifying tests
- `refactor:` Code refactoring
- `style:` Code style changes
- `chore:` Maintenance tasks

#### Pull Request Process
1. Push feature branch to GitHub
2. Create pull request to `develop` branch
3. Ensure all tests pass
4. Request code review
5. Address review feedback
6. Merge after approval

### Code Quality Standards

#### Python (Backend) Standards

##### Code Formatting
```bash
# Format code with Black
black app/ tests/

# Sort imports with isort
isort app/ tests/

# Lint with flake8
flake8 app/ tests/ --max-line-length=100
```

##### Type Hints
```python
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

def calculate_green_score(
    evidence_data: List[Dict[str, Any]],
    sector: str,
    confidence_threshold: float = 0.8
) -> Optional[float]:
    """Calculate green score from evidence data.

    Args:
        evidence_data: List of processed evidence items
        sector: Business sector for baseline calculation
        confidence_threshold: Minimum confidence for inclusion

    Returns:
        Calculated green score or None if insufficient data
    """
    pass
```

##### Error Handling
```python
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

async def process_evidence(evidence_id: str) -> Dict[str, Any]:
    try:
        result = await ai_service.process(evidence_id)
        return result
    except ExternalAPIError as e:
        logger.error(f"AI service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service temporarily unavailable"
        )
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
```

#### TypeScript (Frontend) Standards

##### Component Structure
```typescript
import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/hooks/useAuth';

interface GreenScoreDisplayProps {
  userId: string;
  refreshInterval?: number;
}

export const GreenScoreDisplay: React.FC<GreenScoreDisplayProps> = ({
  userId,
  refreshInterval = 30000
}) => {
  const [score, setScore] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const { token } = useAuth();

  useEffect(() => {
    const fetchScore = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/score/${userId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        const data = await response.json();
        setScore(data.score);
      } catch (error) {
        console.error('Failed to fetch green score:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchScore();
    const interval = setInterval(fetchScore, refreshInterval);
    return () => clearInterval(interval);
  }, [userId, token, refreshInterval]);

  if (loading) return <div>Loading...</div>;
  if (!score) return <div>No score available</div>;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Green Score</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold text-green-600">
          {score}
        </div>
      </CardContent>
    </Card>
  );
};
```

##### API Integration
```typescript
import { ApiResponse, EvidenceData, ProcessingResult } from '@/types/api';

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  setToken(token: string) {
    this.token = token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(this.token && { Authorization: `Bearer ${this.token}` }),
      ...options.headers,
    };

    const response = await fetch(url, { ...options, headers });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async processEvidence(evidenceData: EvidenceData): Promise<ProcessingResult> {
    const formData = new FormData();
    formData.append('file', evidenceData.file);
    formData.append('sector', evidenceData.sector);
    formData.append('evidence_type', evidenceData.evidenceType);

    const response = await this.request<ProcessingResult>('/ai/evidence/process', {
      method: 'POST',
      body: formData,
      headers: {}, // Don't set Content-Type for FormData
    });

    return response.data;
  }
}
```

### Testing Guidelines

#### Backend Testing

##### Unit Tests
```python
import pytest
from unittest.mock import Mock, patch
from app.ai.score_computation import ScoreComputer

@pytest.fixture
def score_computer():
    return ScoreComputer()

@pytest.fixture
def sample_evidence_data():
    return [
        {
            "type": "renewable_energy",
            "impact": 2.5,
            "confidence": 0.89,
            "emission_reduction": 1200.5
        }
    ]

class TestScoreComputer:
    def test_calculate_score_with_valid_data(self, score_computer, sample_evidence_data):
        """Test score calculation with valid evidence data."""
        result = score_computer.calculate_score(
            evidence_data=sample_evidence_data,
            sector="agriculture"
        )

        assert result is not None
        assert 0 <= result <= 100
        assert isinstance(result, float)

    def test_calculate_score_with_low_confidence(self, score_computer):
        """Test score calculation filters low confidence evidence."""
        low_confidence_data = [
            {
                "type": "renewable_energy",
                "impact": 2.5,
                "confidence": 0.3,  # Below threshold
                "emission_reduction": 1200.5
            }
        ]

        result = score_computer.calculate_score(
            evidence_data=low_confidence_data,
            sector="agriculture",
            confidence_threshold=0.8
        )

        # Should return baseline score since no high-confidence evidence
        assert result == score_computer.get_baseline_score("agriculture")

    @patch('app.ai.score_computation.SectorBaselineService')
    def test_sector_baseline_integration(self, mock_baseline_service, score_computer):
        """Test integration with sector baseline service."""
        mock_baseline_service.get_baseline.return_value = 45.0

        result = score_computer.calculate_score(
            evidence_data=[],
            sector="manufacturing"
        )

        mock_baseline_service.get_baseline.assert_called_once_with("manufacturing")
        assert result == 45.0
```

##### Integration Tests
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db import get_db, Base

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client

class TestEvidenceAPI:
    def test_create_evidence_success(self, client, authenticated_user):
        """Test successful evidence creation."""
        response = client.post(
            "/evidence/",
            headers={"Authorization": f"Bearer {authenticated_user.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "evidence_id" in data
        assert "upload_url" in data

    def test_process_evidence_with_file(self, client, authenticated_user):
        """Test evidence processing with file upload."""
        with open("tests/fixtures/solar_receipt.jpg", "rb") as f:
            response = client.post(
                "/ai/evidence/process",
                headers={"Authorization": f"Bearer {authenticated_user.token}"},
                files={"file": ("solar_receipt.jpg", f, "image/jpeg")},
                data={
                    "sector": "agriculture",
                    "evidence_type": "renewable_energy",
                    "description": "Solar panel installation receipt"
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "confidence_score" in data
        assert "processing_results" in data
```

#### Frontend Testing

##### Component Tests
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { EvidenceUpload } from '@/components/Sme/EvidenceUpload';
import { AuthProvider } from '@/contexts/AuthContext';

const mockUploadEvidence = vi.fn();

vi.mock('@/hooks/useEvidence', () => ({
  useEvidence: () => ({
    uploadEvidence: mockUploadEvidence,
    loading: false,
    error: null
  })
}));

const renderWithAuth = (component: React.ReactElement) => {
  return render(
    <AuthProvider>
      {component}
    </AuthProvider>
  );
};

describe('EvidenceUpload', () => {
  beforeEach(() => {
    mockUploadEvidence.mockClear();
  });

  it('renders upload form correctly', () => {
    renderWithAuth(<EvidenceUpload />);

    expect(screen.getByText('Upload Evidence')).toBeInTheDocument();
    expect(screen.getByLabelText('Evidence Type')).toBeInTheDocument();
    expect(screen.getByLabelText('Upload File')).toBeInTheDocument();
  });

  it('handles file upload successfully', async () => {
    mockUploadEvidence.mockResolvedValue({
      success: true,
      data: { id: '123', status: 'processing' }
    });

    renderWithAuth(<EvidenceUpload />);

    const fileInput = screen.getByLabelText('Upload File');
    const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' });

    fireEvent.change(fileInput, { target: { files: [file] } });
    fireEvent.click(screen.getByText('Submit Evidence'));

    await waitFor(() => {
      expect(mockUploadEvidence).toHaveBeenCalledWith({
        file,
        evidenceType: expect.any(String),
        sector: expect.any(String)
      });
    });
  });

  it('displays error message on upload failure', async () => {
    mockUploadEvidence.mockRejectedValue(new Error('Upload failed'));

    renderWithAuth(<EvidenceUpload />);

    const fileInput = screen.getByLabelText('Upload File');
    const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' });

    fireEvent.change(fileInput, { target: { files: [file] } });
    fireEvent.click(screen.getByText('Submit Evidence'));

    await waitFor(() => {
      expect(screen.getByText('Upload failed')).toBeInTheDocument();
    });
  });
});
```

##### E2E Tests
```typescript
import { test, expect } from '@playwright/test';

test.describe('Evidence Upload Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login as SME user
    await page.goto('/login');
    await page.fill('input[name="phone"]', '+254700000000');
    await page.click('button[type="submit"]');
    await page.fill('input[name="otp"]', '123456');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/dashboard');
  });

  test('complete evidence upload and processing', async ({ page }) => {
    // Navigate to evidence upload
    await page.click('text=Upload Evidence');
    await expect(page).toHaveURL('/evidence/upload');

    // Fill form
    await page.selectOption('select[name="evidenceType"]', 'renewable_energy');
    await page.fill('textarea[name="description"]', 'Solar panel installation');

    // Upload file
    await page.setInputFiles('input[type="file"]', './tests/fixtures/solar_receipt.jpg');

    // Submit form
    await page.click('button[type="submit"]');

    // Wait for processing
    await expect(page.locator('text=Processing...')).toBeVisible();
    await expect(page.locator('text=Processing complete')).toBeVisible({ timeout: 30000 });

    // Verify results
    await expect(page.locator('[data-testid="confidence-score"]')).toContainText(/\d+%/);
    await expect(page.locator('[data-testid="green-score-impact"]')).toContainText(/\+\d+/);
  });

  test('handles upload error gracefully', async ({ page }) => {
    // Mock API to return error
    await page.route('**/api/ai/evidence/process', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Processing failed' })
      });
    });

    await page.click('text=Upload Evidence');
    await page.selectOption('select[name="evidenceType"]', 'renewable_energy');
    await page.setInputFiles('input[type="file"]', './tests/fixtures/solar_receipt.jpg');
    await page.click('button[type="submit"]');

    await expect(page.locator('text=Processing failed')).toBeVisible();
    await expect(page.locator('button:has-text("Try Again")')).toBeVisible();
  });
});
```

### Running Tests

#### Backend Tests
```bash
cd backend

# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=app --cov-report=html

# Run specific test file
python -m pytest tests/test_ai_processing.py

# Run with verbose output
python -m pytest -v

# Run tests in parallel
python -m pytest -n auto
```

#### Frontend Tests
```bash
cd frontend-web

# Run unit tests
npm test

# Run with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e

# Run tests in watch mode
npm run test:watch

# Run specific test file
npm test -- EvidenceUpload.test.tsx
```

## Debugging

### Backend Debugging

#### Local Development
```python
import pdb

def process_evidence(evidence_data):
    pdb.set_trace()  # Debugger breakpoint
    result = ai_service.process(evidence_data)
    return result
```

#### VS Code Debugging
Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI Debug",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/backend/app/main.py",
      "args": ["--reload"],
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend"
      }
    }
  ]
}
```

#### Logging
```python
import logging

logger = logging.getLogger(__name__)

def calculate_green_score(evidence_data):
    logger.info(f"Processing {len(evidence_data)} evidence items")

    try:
        score = compute_score(evidence_data)
        logger.info(f"Calculated score: {score}")
        return score
    except Exception as e:
        logger.error(f"Score calculation failed: {e}", exc_info=True)
        raise
```

### Frontend Debugging

#### Browser DevTools
```typescript
// Debug API calls
const response = await fetch('/api/evidence');
console.log('API Response:', response);
console.log('Data:', await response.json());

// Debug component state
useEffect(() => {
  console.log('Green score updated:', greenScore);
}, [greenScore]);

// Debug performance
console.time('Evidence Processing');
await processEvidence(data);
console.timeEnd('Evidence Processing');
```

#### React DevTools
Install React DevTools browser extension for component inspection and profiling.

## Performance Optimization

### Backend Performance

#### Database Optimization
```python
# Use database indexes
class Evidence(Base):
    __tablename__ = "evidence"

    user_id = Column(UUID, ForeignKey("users.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(Enum(EvidenceStatus), index=True)

# Optimize queries
def get_user_evidence(db: Session, user_id: str, limit: int = 50):
    return db.query(Evidence)\
        .filter(Evidence.user_id == user_id)\
        .order_by(Evidence.created_at.desc())\
        .limit(limit)\
        .all()

# Use eager loading
def get_user_with_profile(db: Session, user_id: str):
    return db.query(User)\
        .options(joinedload(User.profile))\
        .filter(User.id == user_id)\
        .first()
```

#### Caching
```python
from functools import lru_cache
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

@lru_cache(maxsize=128)
def get_sector_baseline(sector: str) -> float:
    """Cache sector baselines in memory."""
    return calculate_sector_baseline(sector)

async def get_green_score(user_id: str) -> dict:
    """Cache green scores in Redis."""
    cache_key = f"green_score:{user_id}"
    cached_score = redis_client.get(cache_key)

    if cached_score:
        return json.loads(cached_score)

    score = calculate_green_score(user_id)
    redis_client.setex(cache_key, 3600, json.dumps(score))  # 1 hour cache
    return score
```

### Frontend Performance

#### Code Splitting
```typescript
import { lazy, Suspense } from 'react';

const EvidenceUpload = lazy(() => import('./components/Sme/EvidenceUpload'));
const LoanOffers = lazy(() => import('./components/Sme/LoanOffers'));

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/evidence/upload" element={
          <Suspense fallback={<div>Loading...</div>}>
            <EvidenceUpload />
          </Suspense>
        } />
      </Routes>
    </BrowserRouter>
  );
}
```

#### Memoization
```typescript
import { memo, useMemo, useCallback } from 'react';

const GreenScoreDisplay = memo(({ score, pillars }) => {
  const scoreColor = useMemo(() => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  }, [score]);

  return (
    <div className={scoreColor}>
      {score}
    </div>
  );
});

const EvidenceList = ({ evidence, onProcess }) => {
  const handleProcess = useCallback((id) => {
    onProcess(id);
  }, [onProcess]);

  const filteredEvidence = useMemo(() => {
    return evidence.filter(item => item.status === 'pending');
  }, [evidence]);

  return (
    <div>
      {filteredEvidence.map(item => (
        <EvidenceItem
          key={item.id}
          evidence={item}
          onProcess={handleProcess}
        />
      ))}
    </div>
  );
};
```

## Contributing Guidelines

### Code Review Process

#### Reviewer Checklist
- [ ] Code follows project coding standards
- [ ] Tests cover new functionality
- [ ] Documentation is updated
- [ ] No security vulnerabilities introduced
- [ ] Performance implications considered
- [ ] Error handling is appropriate
- [ ] API changes are backward compatible

#### Common Review Comments
- **Naming**: Use descriptive variable and function names
- **Error Handling**: Always handle potential errors gracefully
- **Testing**: Include unit tests for new functionality
- **Documentation**: Update docstrings and comments
- **Performance**: Consider caching and optimization opportunities
- **Security**: Validate all inputs and sanitize outputs

### Release Process

#### Version Numbering
Follow semantic versioning (SemVer):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

#### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Version number bumped
- [ ] Changelog updated
- [ ] Security scan completed
- [ ] Performance testing completed
- [ ] Deployment tested in staging

### Support and Communication

#### Getting Help
- **Slack**: #halicred-dev channel for real-time discussion
- **GitHub Issues**: Bug reports and feature requests
- **Wiki**: Internal documentation and architecture decisions
- **Code Reviews**: Learn from senior developers

#### Reporting Issues
1. Search existing issues first
2. Use issue templates
3. Provide minimal reproduction steps
4. Include environment details
5. Add relevant labels

#### Feature Requests
1. Discuss in team meeting first
2. Create RFC (Request for Comments) document
3. Get stakeholder approval
4. Create implementation plan
5. Break down into smaller tasks

---

**Document Version**: 7.0.0
**Last Updated**: September 30, 2025
**Maintained By**: HaliCred Development Team
**Next Review**: December 30, 2025