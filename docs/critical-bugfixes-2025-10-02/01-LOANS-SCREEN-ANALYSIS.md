# Loans Screen 400 Error Analysis
**Priority**: 1
**Severity**: CRITICAL (User-Blocking)
**Date**: 2025-10-02

## Problem Statement

Users experience white screen with error when clicking "Loans". Backend returns 400 Bad Request with message about minimum GreenScore requirements.

## Error Evidence

**Backend Log**:
```
2025-10-02 09:49:08,109 - app.monitoring.tracing - WARNING - Request completed: POST /loan/quote - 400 (387.64ms)
INFO:     127.0.0.1:55242 - "POST /loan/quote HTTP/1.1" 400 Bad Request
```

**Duplicate Requests**:
```
2025-10-02 09:49:07,722 - app.monitoring.tracing - INFO - Request started: POST /loan/quote
2025-10-02 09:49:07,727 - app.monitoring.tracing - INFO - Request started: POST /loan/quote
```

## Root Cause

**Primary Cause**: Missing GreenScore records for new users
**File**: `backend/app/services/loan_service.py:231-260`

```python
# Query for user's GreenScore
latest_score = db.query(GreenScore).filter(
    GreenScore.user_id == user.id
).order_by(GreenScore.computed_at.desc()).first()

# ...later...
current_score = latest_score.score if latest_score else 0  # New users → 0

# Check minimum score requirement
if current_score < sector_profile.min_green_score:
    reasons.append(f"Minimum GreenScore of {sector_profile.min_green_score} required for {sector.value}")

# ...later in generate_loan_quote...
if not eligibility.eligible:
    raise ValueError(f"Loan not eligible: {'; '.join(eligibility.reasons)}")
```

**Error Handling**:
**File**: `backend/app/main.py:536-539`

```python
except ValueError as e:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(e)
    )
```

**Flow**:
1. New user has NO GreenScore record in database
2. `latest_score = None` → `current_score = 0`
3. Loan eligibility requires min score (e.g., 30 for farmers)
4. 0 < 30 → Eligibility fails
5. ValueError raised → Converted to HTTP 400
6. Frontend receives 400 → Shows error screen

## Secondary Issue: Duplicate Requests

**File**: `frontend-web/src/Components/Sme/LoanOffers.tsx:66-106`

```typescript
useEffect(() => {
  const fetchQuotes = async () => {
    // ...API call...
  };
  fetchQuotes();
}, [selectedAmount, selectedTerm]);  // Triggers on component mount
```

**Cause**: React Strict Mode in development double-mounts components, OR state values changing on initial render.

**Impact**: Creates log noise, unnecessary API calls, but not a functional bug.

## Dependencies

**BLOCKED BY**: Priority 4 (GreenScore Initialization)
- Cannot fully fix until all users have GreenScores

## Solution

### Part 1: Fix Root Cause (Priority 4)
See `04-GREENSCORE-INITIALIZATION-ANALYSIS.md`

### Part 2: Improve Error Messages (This Fix)

**File**: `backend/app/services/loan_service.py:258-260`

**Current**:
```python
if current_score < sector_profile.min_green_score:
    reasons.append(f"Minimum GreenScore of {sector_profile.min_green_score} required for {sector.value}")
```

**Improved**:
```python
if current_score < sector_profile.min_green_score:
    if current_score == 0:
        reasons.append(
            f"Build your GreenScore by uploading evidence of eco-friendly practices. "
            f"Minimum score of {sector_profile.min_green_score} required for {sector.value} sector loans."
        )
    else:
        reasons.append(
            f"Current GreenScore ({current_score}) is below minimum ({sector_profile.min_green_score}) "
            f"for {sector.value} sector. Upload more evidence to improve your score."
        )
```

### Part 3: Frontend Error Handling

**File**: `frontend-web/src/Components/Sme/LoanOffers.tsx:87-92`

**Improve**:
```typescript
catch (error) {
  if (error instanceof Error) {
    const message = error.message;
    if (message.includes("GreenScore") || message.includes("evidence")) {
      setQuoteError(
        "To access loans, please upload evidence of your eco-friendly practices to build your GreenScore. " +
        "Examples: solar panel receipts, energy-efficient equipment, recycling initiatives."
      );
    } else {
      setQuoteError(message);
    }
  }
}
```

### Part 4: Optional - Reduce Duplicate Requests

**File**: `frontend-web/src/Components/Sme/LoanOffers.tsx`

**Add debouncing**:
```typescript
import { useEffect, useState, useRef } from 'react';

// ...
const fetchTimeoutRef = useRef<NodeJS.Timeout>();

useEffect(() => {
  // Debounce API calls
  if (fetchTimeoutRef.current) {
    clearTimeout(fetchTimeoutRef.current);
  }

  fetchTimeoutRef.current = setTimeout(() => {
    fetchQuotes();
  }, 300); // 300ms debounce

  return () => {
    if (fetchTimeoutRef.current) {
      clearTimeout(fetchTimeoutRef.current);
    }
  };
}, [selectedAmount, selectedTerm]);
```

**Note**: Duplicate requests in logs are likely React Strict Mode (development only). Not critical to fix.

## Testing

- [ ] New user (GreenScore=0) → Sees helpful message about uploading evidence
- [ ] User with low score → Sees message about current score and how to improve
- [ ] No white screen errors
- [ ] Error messages guide user to next action
- [ ] Loan screen loads (shows eligibility info instead of crashing)

## Success Criteria

- [ ] 0% 400 errors on /loan/quote after P4 fix
- [ ] Error messages are actionable and user-friendly
- [ ] Users understand what to do next (upload evidence)
- [ ] No regression for users with existing GreenScores

---

**Depends On**: Priority 4
**Estimated Effort**: 2-3 hours
**Risk**: LOW
