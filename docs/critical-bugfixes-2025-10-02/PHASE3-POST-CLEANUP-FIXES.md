# Phase 3: Post-Database Cleanup Fixes
**Date**: 2025-10-02
**Status**: ✅ COMPLETED

---

## **SUMMARY**

After database cleanup and fresh onboarding, identified and fixed **3 critical errors** preventing evidence processing and AI recommendations.

---

## **ERRORS FROM LOGS**

### **Error 1: Evidence.uploaded_at AttributeError**
**Log**: `type object 'Evidence' has no attribute 'uploaded_at'`

**Impact**: AI recommendations endpoint failing with 200 but returning fallback data

**Occurrences**: Every AI recommendations request

---

### **Error 2: review_required Field Name**
**Log**: `"AIOrchestrationResult" object has no field "review_required"`

**Impact**: Evidence processing failing when setting review flag

**Occurrences**: During evidence processing in orchestrator

---

### **Error 3: Database Type Mismatch (explainers/actions)**
**Log**:
```
column "explainers" is of type character varying[] but expression is of type json
HINT: You will need to rewrite or cast the expression.
```

**Impact**: Evidence processing completely fails with 500 error, database insert fails

**Occurrences**: When saving GreenScoreResult after evidence processing

---

## **ROOT CAUSES**

### **Cause 1: Incorrect Field Name in Evidence Query**
**File**: `backend/app/api/ai_engine.py:305`

**Problem**:
```python
# WRONG - Evidence model doesn't have uploaded_at
evidence_list = db.query(Evidence).filter(
    Evidence.user_id == user.id
).order_by(Evidence.uploaded_at.desc()).limit(10).all()
```

**Evidence Model** (`backend/app/models.py:86-93`):
```python
class Evidence(Base):
    __tablename__ = "evidence"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    s3_key = Column(String, nullable=False)
    status = Column(Enum("pending", "processing", "verified", "rejected", name="evidence_status"), index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=sa.func.now())  # ← THIS is the timestamp
```

**The field is `created_at`, not `uploaded_at`**

---

### **Cause 2: Wrong Field Name in AIOrchestrationResult**
**File**: `backend/app/ai/orchestrator.py:156`

**Problem**:
```python
# WRONG field name
result.review_required = self._requires_human_review(result)
```

**AIOrchestrationResult Model** (`backend/app/ai/models.py:120-134`):
```python
class AIOrchestrationResult(BaseModel):
    # ... other fields ...
    requires_human_review: bool = False  # ← Correct field name
    # NOT review_required
```

---

### **Cause 3: Schema Mismatch (Model vs Database)**
**File**: `backend/app/db/ai_models.py:154-155`

**Model Definition** (BEFORE):
```python
explainers = Column(JSON)  # Model says JSON
actions = Column(JSON)     # Model says JSON
```

**Actual Database Schema**:
```sql
explainers VARCHAR[]  -- Database has array, not JSON
actions VARCHAR[]     -- Database has array, not JSON
```

**Why Mismatch Occurred**:
- Database was created with `VARCHAR[]` (PostgreSQL array)
- Model was updated to `JSON` at some point
- No migration was run to sync them
- When inserting, SQLAlchemy tries to cast to JSON (per model), but database rejects it

**Error Flow**:
1. Python list created: `["Processing error: ..."]`
2. Model says column type is `JSON`
3. SQLAlchemy generates SQL: `%(explainers)s::JSON`
4. PostgreSQL sees: "You're passing JSON to VARCHAR[], that's wrong!"
5. Insert fails with type mismatch error

---

## **FIXES IMPLEMENTED**

### **Fix 1: Correct Evidence Timestamp Field**
**File**: `backend/app/api/ai_engine.py:305`

**Change**:
```python
# BEFORE
.order_by(Evidence.uploaded_at.desc())

# AFTER
.order_by(Evidence.created_at.desc())
```

**Impact**: AI recommendations now load evidence history correctly

---

### **Fix 2: Correct AIOrchestrationResult Field Name**
**File**: `backend/app/ai/orchestrator.py:156`

**Change**:
```python
# BEFORE
result.review_required = self._requires_human_review(result)

# AFTER
result.requires_human_review = self._requires_human_review(result)
```

**Impact**: No more "object has no field" errors during evidence processing

---

### **Fix 3: Match Model to Database Schema**
**File**: `backend/app/db/ai_models.py:154-155`

**Change**:
```python
# BEFORE
explainers = Column(JSON)
actions = Column(JSON)

# AFTER
explainers = Column(ARRAY(String))  # Database has VARCHAR[], not JSON
actions = Column(ARRAY(String))     # Database has VARCHAR[], not JSON
```

**Why This Fix (Not Database Migration)**:
- Safer: No schema change, just model correction
- Faster: No migration to run
- Correct: Database schema is fine, model was wrong
- Works: Python lists → PostgreSQL arrays automatically

**How It Works**:
- Python: `explainers = ["Solar installation saves CO2"]` (list)
- SQLAlchemy with `ARRAY(String)`: Knows to map list → PostgreSQL array
- PostgreSQL: Receives `{"Solar installation saves CO2"}` (PostgreSQL array notation)
- ✅ Success!

---

## **VERIFICATION**

### **Evidence Processing Flow** (Now Fixed):
1. ✅ User uploads image
2. ✅ Evidence model saved with `created_at` timestamp
3. ✅ Evidence processor runs Google Vision
4. ✅ AIOrchestrator processes with `requires_human_review` field
5. ✅ GreenScoreResult saved with `explainers` as list → database array
6. ✅ No errors, processing completes successfully

### **AI Recommendations Flow** (Now Fixed):
1. ✅ Query Evidence using `created_at` field
2. ✅ Extract evidence summary from recent uploads
3. ✅ Generate personalized recommendations
4. ✅ Return to frontend without errors

---

## **REMAINING ISSUES (Not Backend)**

### **Loan Screen - Frontend Issue**
**Symptom**: White screen for a while, then error screen

**Backend Status**: ✅ Working correctly
- Returns 400 with helpful message: "Build your GreenScore by uploading evidence..."
- Error is **correct** (user has GreenScore=0, minimum=30 for agriculture)

**Frontend Issue**:
- No loading skeleton while waiting for response
- Error message not displayed to user
- Needs React component update (not backend fix)

**What Frontend Needs**:
```typescript
// Add loading state
const [isLoading, setIsLoading] = useState(false);

// Show skeleton while loading
{isLoading && <LoadingSkeleton />}

// Display API error message
{error && <ErrorMessage text={error} />}
```

---

## **FILES MODIFIED**

1. `backend/app/api/ai_engine.py` - Line 305 (Evidence query)
2. `backend/app/ai/orchestrator.py` - Line 156 (Field name)
3. `backend/app/db/ai_models.py` - Lines 154-155 (Column types)

**Total Changes**: 3 files, 5 lines

---

## **TESTING CHECKLIST**

- [x] Evidence upload works end-to-end
- [x] No AttributeError on Evidence queries
- [x] No "field doesn't exist" errors in orchestrator
- [x] No database type mismatch errors
- [x] AI recommendations load successfully
- [x] Evidence history tracked correctly
- [x] GreenScoreResult inserts succeed
- [ ] **TODO**: Frontend loading state for loans (not backend)
- [ ] **TODO**: Frontend error display for loans (not backend)

---

## **SUCCESS CRITERIA**

✅ Evidence processing completes without 500 errors
✅ AI recommendations return real data (not just fallback)
✅ Database inserts succeed for GreenScoreResult
✅ No AttributeErrors in logs
✅ No field name errors
✅ No type mismatch errors

**All backend issues resolved!** 🎉

---

## **NOTES**

### **Why Database Cleanup Was Needed**
- Previous migrations had created GreenScore records manually
- Evidence table had old test data
- Fresh start ensures all fixes work with clean state

### **Why These Errors Only Appeared After Cleanup**
1. **Evidence.uploaded_at**: Old code path wasn't hit (no evidence to query)
2. **review_required**: Error only triggers on processing (no processing before)
3. **explainers type**: Insert only attempted when processing succeeds

### **Tesseract Note**
User installed tesseract - OCR will now work better, but graceful fallback still in place if it fails.

---

**Ready for production testing with real evidence uploads!** ✅
