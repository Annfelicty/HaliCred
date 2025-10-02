# Master Implementation Plan
**Date**: 2025-10-02
**Status**: Ready for Execution

## Executive Summary

This plan provides step-by-step instructions to fix all 4 critical bugs in dependency order. Total estimated effort: 16-24 hours including testing.

## Fix Order (By Dependency)

```
PHASE 1: Foundation (Priority 4) → 4-6 hours
  └─ Initialize GreenScore for all users

PHASE 2: Evidence Pipeline (Priority 2) → 8-12 hours
  └─ Implement Google Vision processing

PHASE 3: Loan UX (Priority 1) → 2-3 hours
  └─ Improve error handling

PHASE 4: AI Enhancement (Priority 3) → 1-2 hours
  └─ Fix Gemini JSON parsing
```

## PHASE 1: GreenScore Initialization

### Step 1.1: Database Migration (Existing Users)

**Create**: `backend/migrations/init_greenscores.py`

Run in production:
```bash
cd backend
python migrations/init_greenscores.py
```

**Verify**:
```sql
SELECT COUNT(*) FROM users u
LEFT JOIN greenscores g ON u.id = g.user_id
WHERE g.id IS NULL;
-- Should return 0
```

### Step 1.2: Modify User Creation

**File**: `backend/app/api/auth.py:337`

**Add after** `db.add(user)`:
```python
db.flush()  # Generate user.id

# Initialize GreenScore
from app.models import GreenScore
from uuid import uuid4
from datetime import datetime

initial_greenscore = GreenScore(
    id=uuid4(),
    user_id=user.id,
    score=0,
    subscores={
        "energy_efficiency": 0,
        "water_conservation": 0,
        "waste_management": 0,
        "sustainable_sourcing": 0,
        "carbon_reduction": 0
    },
    explanation_json={
        "message": "Welcome! Upload evidence to build your GreenScore.",
        "pillars": {k: "No data yet" for k in ["energy_efficiency", "water_conservation", "waste_management", "sustainable_sourcing", "carbon_reduction"]}
    },
    computed_at=datetime.utcnow()
)
db.add(initial_greenscore)
```

### Step 1.3: Test

- [ ] Register new user via API
- [ ] Query database: `SELECT * FROM greenscores WHERE user_id = '<new_user_id>';`
- [ ] Verify GreenScore exists with score=0
- [ ] Load dashboard → should show 0 (not 45)
- [ ] Try loan quote → should get clear error message (not 400)

### Step 1.4: Deploy

1. Run migration in production
2. Deploy code changes
3. Monitor logs for GreenScore creation
4. Verify no 400 errors on loan endpoint

## PHASE 2: Evidence Processing

### Step 2.1: Create Evidence Processor

**Create**: `backend/app/ai/evidence_processor.py`

Copy complete implementation from `02-EVIDENCE-PROCESSING-ANALYSIS.md`

**Key Methods**:
- `process_evidence(EvidenceData) → ProcessedEvidence`
- `_extract_ocr(image_bytes) → OCRResult`
- `_extract_cv(image_bytes) → CVResult`
- `_extract_features(...) → EmissionFeatures`

### Step 2.2: Integrate into ai_service.py

**File**: `backend/app/services/ai_service.py:257-277`

**Replace**:
```python
evidence_payload = EvidenceData(...)
orchestration_result = await orchestrator.process_request(
    AIOrchestrationRequest(evidence=evidence_payload, ...)
)
```

**With**:
```python
evidence_data = EvidenceData(...)

# Process through Google Vision
from app.ai.evidence_processor import evidence_processor
processed_evidence = await evidence_processor.process_evidence(evidence_data)
logger.info(f"Evidence processed: confidence={processed_evidence.processing_confidence:.2f}")

# Pass ProcessedEvidence
orchestration_result = await orchestrator.process_request(
    AIOrchestrationRequest(evidence=processed_evidence, ...)
)
```

### Step 2.3: Test

- [ ] Upload solar panel photo → Check OCR/CV extraction
- [ ] Upload receipt → Check amount extraction
- [ ] Verify Google Vision API calls in logs
- [ ] Verify features extracted
- [ ] Verify GreenScore updates
- [ ] Test with 5-10 different image types

### Step 2.4: Deploy

1. Deploy evidence_processor.py
2. Deploy modified ai_service.py
3. Monitor Google Vision API usage/costs
4. Watch for any Vision API errors

## PHASE 3: Loan Eligibility Improvements

### Step 3.1: Better Error Messages

**File**: `backend/app/services/loan_service.py:258-260`

**Replace**:
```python
if current_score < sector_profile.min_green_score:
    reasons.append(f"Minimum GreenScore of {sector_profile.min_green_score} required for {sector.value}")
```

**With**:
```python
if current_score < sector_profile.min_green_score:
    if current_score == 0:
        reasons.append(
            f"Build your GreenScore by uploading evidence of eco-friendly practices. "
            f"Minimum score of {sector_profile.min_green_score} required for {sector.value} sector loans."
        )
    else:
        reasons.append(
            f"Current GreenScore ({current_score}) below minimum ({sector_profile.min_green_score}) "
            f"for {sector.value} sector. Upload more evidence to improve your score."
        )
```

### Step 3.2: Frontend - Handle Eligibility Errors Gracefully

**File**: `frontend-web/src/Components/Sme/LoanOffers.tsx:87-92`

**Improve error handling**:
```typescript
catch (error) {
  if (error instanceof Error) {
    // Parse eligibility reasons from API
    const message = error.message;
    if (message.includes("GreenScore")) {
      setQuoteError("To access loan offers, please upload evidence of your eco-friendly practices to build your GreenScore.");
    } else {
      setQuoteError(message);
    }
  }
}
```

### Step 3.3: Test

- [ ] New user (GreenScore=0) → Gets helpful message about uploading evidence
- [ ] User with low score → Gets message about improving score
- [ ] No more 400 white screen errors
- [ ] Error messages are user-friendly

## PHASE 4: Gemini JSON Parsing

### Step 4.1: Strip Markdown Code Fences

**File**: `backend/app/api/ai_engine.py:559`

**Replace**:
```python
recommendations = json.loads(response.text.strip())
```

**With**:
```python
import re

response_text = response.text.strip()

# Strip markdown code fences if present
if response_text.startswith("```"):
    # Remove ```json at start and ``` at end
    response_text = re.sub(r'^```(?:json)?\n?', '', response_text)
    response_text = re.sub(r'\n?```$', '', response_text)
    response_text = response_text.strip()

recommendations = json.loads(response_text)
```

**File**: `backend/app/ai/orchestrator.py:233`

**Same fix**:
```python
gemini_response_text = gemini_response.strip()

# Strip markdown code fences
if gemini_response_text.startswith("```"):
    gemini_response_text = re.sub(r'^```(?:json)?\n?', '', gemini_response_text)
    gemini_response_text = re.sub(r'\n?```$', '', gemini_response_text)
    gemini_response_text = gemini_response_text.strip()

result_data = json.loads(gemini_response_text)
```

### Step 4.2: Test

- [ ] Get recommendations → Should parse AI response (not fallback)
- [ ] Check logs → Should NOT see "Failed to parse Gemini JSON"
- [ ] Verify recommendations are AI-powered (change with user context)

## Deployment Checklist

### Pre-Deployment
- [ ] Code review completed
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Staging environment tested
- [ ] Database migration tested in staging
- [ ] Rollback plan documented

### Deployment Sequence

**Step 1**: Database Migration
```bash
# Backup database first
pg_dump halicred_db > backup_$(date +%Y%m%d).sql

# Run migration
cd backend
python migrations/init_greenscores.py
```

**Step 2**: Deploy Backend Changes
```bash
# Pull latest code
git pull origin main

# Restart backend
# (use your deployment method)
```

**Step 3**: Deploy Frontend Changes
```bash
cd frontend-web
npm run build
# Deploy build
```

### Post-Deployment Monitoring

**First 30 minutes**:
- [ ] Check logs for errors
- [ ] Monitor new user registrations → Verify GreenScore creation
- [ ] Monitor evidence uploads → Verify Google Vision calls
- [ ] Monitor loan quotes → Verify no 400 errors
- [ ] Check Google Vision API quota/usage

**First 24 hours**:
- [ ] Monitor error rates
- [ ] Check database: All new users have GreenScores
- [ ] Verify no regression for existing users
- [ ] Monitor API latencies
- [ ] Check Google Vision costs

### Rollback Procedures

**If GreenScore initialization fails**:
```python
# Comment out GreenScore creation in auth.py
# Deploy immediately
```

**If Evidence processing fails**:
```python
# Revert ai_service.py to pass EvidenceData
# Return 500 error gracefully
# Fix evidence_processor.py offline
```

**If database migration corrupts data**:
```sql
-- Restore from backup
psql halicred_db < backup_YYYYMMDD.sql

-- Or delete migration-created records
DELETE FROM greenscores
WHERE explanation_json::jsonb @> '{"created_by": "system_migration"}';
```

## Success Metrics

### Functional
- [ ] 0 users without GreenScore records
- [ ] 0% increase in 400 errors on /loan/quote
- [ ] Evidence upload success rate > 95%
- [ ] Gemini parsing success rate > 90%

### Performance
- [ ] User registration < 200ms (was <150ms)
- [ ] Evidence processing < 30 seconds
- [ ] Dashboard load time unchanged
- [ ] API error rate < 0.1%

### Business
- [ ] User can complete full journey: Register → Upload Evidence → Apply for Loan
- [ ] Dashboard shows real data
- [ ] Recommendations are AI-powered

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Migration fails | Test in staging, backup production, rollback SQL ready |
| Google Vision API limit | Monitor usage, implement rate limiting |
| Performance degradation | Load test staging, monitor latencies |
| Existing user regression | Comprehensive regression test suite |
| Cost overrun (Vision API) | Set budget alerts, monitor per-call costs |

## Communication Plan

### Internal Team
- Notify before deployment window
- Share rollback procedures
- Real-time monitoring dashboard
- Post-deployment report

### Users (if needed)
- "We're improving evidence processing" (no specifics)
- Expected brief downtime (if any)
- Contact support if issues

## Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1 | 4-6 hours | None |
| Phase 2 | 8-12 hours | Phase 1 complete |
| Phase 3 | 2-3 hours | Phase 1 complete |
| Phase 4 | 1-2 hours | None (independent) |
| **Total** | **15-23 hours** | Sequential execution |

**Recommended Schedule**:
- **Day 1 Morning**: Phase 1 (GreenScore)
- **Day 1 Afternoon**: Test & Deploy Phase 1
- **Day 2 Morning**: Phase 2 (Evidence Processing)
- **Day 2 Afternoon**: Test Phase 2
- **Day 3 Morning**: Deploy Phase 2, Phase 3, Phase 4
- **Day 3 Afternoon**: Final testing & monitoring

---

**Ready to Execute**: YES
**All Prerequisites Met**: YES (Google Vision configured, database accessible, code reviewed)
**Risk Level**: LOW (with proper testing and rollback plans)
