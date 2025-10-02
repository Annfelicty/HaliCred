# Phase 2 Bug Fixes - Action Plan
**Date**: 2025-10-02
**Status**: Analysis Complete, Ready for Implementation

---

## **EVIDENCE PROCESSING - 6 Cascading Errors**

### **Error 1: File Path Handling (Windows)**
**Log**: `No connection adapters were found for 'C:\\Users\\USER\\AppData\\Local\\Temp\\...'`

**Root Cause**:
- File: `backend/app/ai/evidence_processor.py:1134`
- Windows paths like `C:\Users\...` are parsed by `urlparse()` with scheme="C"
- Check at line 1134: `if parsed.scheme in ("", "file")` doesn't include "C", "D", etc.
- Falls through to `else` block → tries `requests.get("C:\Users\...")` → FAILS

**Fix**:
```python
# Line 1134 - BEFORE:
if parsed.scheme in ("", "file"):

# Line 1134 - AFTER:
# Check for local file (empty scheme, "file://", or Windows drive letter)
if parsed.scheme in ("", "file") or (len(parsed.scheme) == 1 and parsed.scheme.isalpha()):
```

---

### **Error 2: Duplicate Method Definition**
**Log**: `_google_vision_ocr() takes 2 positional arguments but 3 were given`

**Root Cause**:
- File: `backend/app/ai/evidence_processor.py`
- **Line 266-294**: Full implementation `def _google_vision_ocr(self, pil_image, cv_image)`
- **Line 1433-1437**: Stub `def _google_vision_ocr(self, image)` - **OVERRIDES THE REAL ONE**
- Python uses the LAST definition, so the stub replaces the real implementation
- Caller at line 1174 passes TWO args `await self._google_vision_ocr(pil_image, image)`
- Stub only accepts ONE arg → signature mismatch

**Fix**:
- **DELETE lines 1433-1437** (the stub method)
- The real implementation at line 266 will then be used

---

### **Error 3: Missing _build_context Method**
**Log**: `'AIOrchestrator' object has no attribute '_build_context'`

**Root Cause**:
- File: `backend/app/ai/orchestrator.py`
- Code calls `self._build_context()` but method doesn't exist
- Need to verify if this is needed or if there's a replacement

**Investigation Needed**: Read orchestrator.py to find where `_build_context` is called

---

### **Error 4: EmissionCalculator Signature Mismatch**
**Log**: `EmissionCalculator.calculate_emissions() got an unexpected keyword argument 'ocr_result'`

**Root Cause**:
- Orchestrator calls `calculate_emissions(ocr_result=...)`
- But EmissionCalculator expects different args

**Investigation Needed**: Read emission_calculator.py to see correct signature

---

### **Error 5: Missing Field in AIOrchestrationResult**
**Log**: `"AIOrchestrationResult" object has no field "processing_time_ms"`

**Root Cause**:
- Code tries to access `result.processing_time_ms`
- But model doesn't have this field

**Investigation Needed**: Check AIOrchestrationResult in models.py

---

### **Error 6: Database Type Mismatch**
**Log**: `column "explainers" is of type character varying[] but expression is of type json`

**Root Cause**:
- Database: `explainers VARCHAR[]` (PostgreSQL array)
- Code: Passing `'["Processing error: ..."]'` as JSON string
- PostgreSQL strict typing - can't cast JSON to VARCHAR[]

**Fix**:
- When saving GreenScoreResult, ensure `explainers` is a Python list
- SQLAlchemy will handle conversion to PostgreSQL array

**File**: `backend/app/services/ai_service.py:283-296`
```python
# Ensure explainers and actions are lists, not JSON strings
greenscore_record = GreenScoreResult(
    user_id=user_id,
    evidence_id=evidence.id,
    greenscore=orchestration_result.greenscore,
    subscores=orchestration_result.subscores,
    co2_saved_tonnes=orchestration_result.co2_saved_tonnes,
    confidence=orchestration_result.confidence,
    explainers=orchestration_result.explainers,  # Must be list
    actions=orchestration_result.actions,        # Must be list
    sector=sector,
    region=region,
    calculation_method="ai_live",
)
```

---

## **LOAN SCREEN - 400 Error**

**Log**: `400 Bad Request` at `/loan/quote`

**Root Cause**:
- User has GreenScore = 0
- Agriculture sector minimum = 30
- Loan eligibility correctly fails
- **BUT**: Frontend shows white screen instead of error message

**Backend Status**: ✅ Working correctly (helpful error message in response)

**Frontend Issue**: No loading state, error not displayed

**Fix Required**: Frontend (not backend)
- Add loading skeleton while quote loads
- Display error message from API response
- Show guidance: "Upload evidence to build GreenScore"

---

## **AI RECOMMENDATIONS - Performance & UX**

### **Issue 1: No Caching**
**Log**: Every request takes 24-30 seconds

**Root Cause**:
- File: `backend/app/api/ai_engine.py` - `get_carbon_credit_recommendations()`
- Every request calls Gemini API (30 seconds)
- No caching layer

**Fix**: Implement Redis cache with 1-hour TTL
```python
import redis
from datetime import timedelta

# Cache key: f"recommendations:{user_id}:{greenscore}"
# TTL: 3600 seconds (1 hour)
```

### **Issue 2: Weak Prompt**
**Root Cause**: Current prompt doesn't use:
- User's current GreenScore
- Business sector
- Specific evidence uploaded
- Regional context

**Fix**: Enhance prompt with:
```
You are HaliCred's AI sustainability advisor. Based on:
- Current GreenScore: {score}/100
- Business Sector: {sector}
- Region: Kenya
- Evidence Uploaded: {evidence_summary}

Recommend 4 specific, actionable carbon credit opportunities that:
1. Match their current capability level
2. Have clear ROI for {sector} businesses
3. Are feasible in Kenya
4. Will increase their GreenScore

For each recommendation, provide:
- Specific action (not generic)
- Estimated CO2 reduction (tonnes/year)
- Estimated carbon credit value (USD)
- Payback period (months)
- GreenScore impact (+points)
```

---

## **CARBON CREDIT IMPORT ERROR**

**Log**: `name 'CarbonCredit' is not defined`

**Root Cause**:
- File: `backend/app/services/ai_service.py`
- Uses `CarbonCredit` but doesn't import it

**Fix**:
```python
# Add to imports at top of file
from app.ai.models import CarbonCredit
```

---

## **IMPLEMENTATION ORDER**

### **Priority 1: Evidence Processing** (Blocks user uploads)
1. Fix file path handling (Error 1)
2. Remove duplicate method (Error 2)
3. Investigate & fix orchestrator issues (Errors 3, 4, 5)
4. Fix database type mismatch (Error 6)

### **Priority 2: AI Recommendations Caching** (UX degradation)
1. Implement Redis cache
2. Improve prompt

### **Priority 3: Carbon Credit Import** (Non-blocking error)
1. Add missing import

### **Priority 4: Loan Screen** (Frontend issue - user aware)
1. Add loading skeleton (frontend)
2. Display error messages (frontend)

---

## **TESTING CHECKLIST**

### Evidence Processing:
- [ ] Upload image from Windows local path
- [ ] Google Vision OCR called successfully
- [ ] ProcessedEvidence created with confidence > 0.1
- [ ] GreenScore updated in database
- [ ] No database type errors

### AI Recommendations:
- [ ] First load takes ~30 seconds
- [ ] Second load (within 1 hour) returns cached result instantly
- [ ] Recommendations are user-specific
- [ ] Cache expires after 1 hour

### Loan Screen:
- [ ] Shows loading skeleton while quote loads
- [ ] Error message displayed when GreenScore too low
- [ ] Guidance shown: "Upload evidence..."

---

**Next Step**: Begin implementation starting with Evidence Processing fixes
