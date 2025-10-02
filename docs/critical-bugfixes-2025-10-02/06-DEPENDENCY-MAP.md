# Bug Dependency Map
**Date**: 2025-10-02

## Dependency Visualization

```
┌─────────────────────────────────────────────────────┐
│ ROOT CAUSE: Priority 4                              │
│ No GreenScore Initialization on User Creation       │
│ File: backend/app/api/auth.py:330-337               │
└──────────────────┬──────────────────────────────────┘
                   │
                   ├──► BLOCKS ──────────────────────┐
                   │                                  │
                   ▼                                  ▼
         ┌──────────────────────┐        ┌───────────────────────┐
         │ Priority 1           │        │ Dashboard             │
         │ Loan Screen 400      │        │ Shows Stub Data       │
         │ Cannot apply         │        │ Not real values       │
         └──────────────────────┘        └───────────────────────┘
                   │
                   │ PARTIALLY BLOCKS
                   ▼
         ┌──────────────────────┐
         │ Priority 2           │
         │ Evidence Processing  │
         │ Can't update score   │
         └──────────────────────┘

┌─────────────────────────────────────────────────────┐
│ INDEPENDENT: Priority 2                             │
│ Missing Google Vision Processing                    │
│ File: backend/app/services/ai_service.py:272        │
└──────────────────┬──────────────────────────────────┘
                   │
                   ├──► BLOCKS ──────────────────────┐
                   │                                  │
                   ▼                                  ▼
         ┌──────────────────────┐        ┌───────────────────────┐
         │ Evidence Upload      │        │ GreenScore Building   │
         │ Pydantic Error       │        │ Users can't progress  │
         └──────────────────────┘        └───────────────────────┘

┌─────────────────────────────────────────────────────┐
│ INDEPENDENT: Priority 3                             │
│ Gemini JSON Parsing Failure                         │
│ File: backend/app/api/ai_engine.py:559              │
└──────────────────┬──────────────────────────────────┘
                   │
                   ├──► GRACEFUL DEGRADATION ────────┐
                   │                                  │
                   ▼                                  ▼
         ┌──────────────────────┐        ┌───────────────────────┐
         │ Uses Fallback        │        │ No User Impact        │
         │ Static Recommendations│        │ Just less AI-powered  │
         └──────────────────────┘        └───────────────────────┘
```

## Critical Path Analysis

### Path 1: New User → Loan Application
```
1. User registers
   ↓ [BLOCKED if Priority 4 not fixed]
2. No GreenScore created
   ↓
3. Dashboard loads → Shows stub data
   ↓
4. User clicks "Apply for Loan"
   ↓ [FAILS - 400 error]
5. Loan eligibility check → GreenScore = 0 → Fails min requirement
   ↓
6. WHITE SCREEN / ERROR
   ✗ USER JOURNEY BROKEN
```

**Fix**: Priority 4 must be fixed first

### Path 2: New User → Evidence Upload → Loan
```
1. User registers
   ↓ [BLOCKED if Priority 4 not fixed]
2. No GreenScore created
   ↓
3. User uploads solar panel photo
   ↓ [FAILS - Pydantic error if Priority 2 not fixed]
4. Evidence processing fails
   ↓
5. No GreenScore update
   ↓
6. Still can't apply for loan
   ✗ USER JOURNEY BROKEN
```

**Fix**: Both Priority 4 AND Priority 2 must be fixed

### Path 3: Existing User → Recommendations
```
1. User with GreenScore logs in
   ↓
2. Dashboard loads
   ↓
3. Recommendations API called
   ↓ [DEGRADED if Priority 3 not fixed]
4. Gemini returns JSON in markdown
   ↓
5. Parsing fails
   ↓
6. Falls back to static recommendations
   ✓ USER JOURNEY WORKS (degraded)
```

**Fix**: Priority 3 is LOW priority (has fallback)

## Fix Order by Dependency

### Recommended Order

**1st: Priority 4** (GreenScore Initialization)
- **Why First**: Root dependency, blocks everything
- **Unblocks**: Priority 1 (Loan), Dashboard, Evidence updates
- **Risk**: LOW (additive change)
- **Effort**: 4-6 hours

**2nd: Priority 2** (Evidence Processing)
- **Why Second**: Enables core value proposition
- **Depends On**: Priority 4 (needs GreenScore to update)
- **Unblocks**: Evidence upload, GreenScore building
- **Risk**: MEDIUM (external API)
- **Effort**: 8-12 hours

**3rd: Priority 1** (Loan UX)
- **Why Third**: Improves errors after P4 fix
- **Depends On**: Priority 4 (GreenScores exist)
- **Unblocks**: Better user experience
- **Risk**: LOW (UI/messaging)
- **Effort**: 2-3 hours

**4th: Priority 3** (Gemini Parsing)
- **Why Last**: Independent, has working fallback
- **Depends On**: None
- **Unblocks**: AI-powered recommendations
- **Risk**: LOW (string manipulation)
- **Effort**: 1-2 hours

### Why This Order?

1. **Foundation First**: Fix the root cause (P4) so everything else works
2. **Value Second**: Enable evidence upload (P2) so users can build scores
3. **Polish Third**: Improve loan error messages (P1) for better UX
4. **Enhancement Last**: Fix AI parsing (P3) for optimal experience

## Dependency Matrix

| Bug | Depends On | Blocks | Can Deploy Independently? |
|-----|------------|--------|---------------------------|
| P4 GreenScore | None | P1, P2 (partially), Dashboard | YES |
| P1 Loans | P4 | User loans | NO (needs P4) |
| P2 Evidence | P4 (for updates) | Evidence upload, score building | PARTIALLY (technical fix works, but score updates need P4) |
| P3 Gemini | None | None (has fallback) | YES |

## Risk Analysis

### Cascading Failure Risk

**If we fix P2 before P4**:
- Evidence processing works technically ✓
- But GreenScore updates fail (no initial record) ✗
- Users still can't apply for loans ✗
- **Result**: Partial fix, user confusion

**If we fix P1 before P4**:
- Better error messages ✓
- But users still have no GreenScore ✗
- Still can't get loans ✗
- **Result**: Lipstick on a pig

**If we fix P4 first**:
- All users have GreenScores ✓
- Loans work (with improved messages if P1 also fixed) ✓
- Evidence can update scores (if P2 also fixed) ✓
- **Result**: Solid foundation for other fixes

### Recommended Deployment Strategy

**Option A: Atomic Deployment (SAFEST)**
```
Day 1: Deploy P4 only
       Monitor, validate
Day 2: Deploy P2 only
       Monitor, validate
Day 3: Deploy P1 + P3
       Final testing
```

**Option B: Bundled Deployment**
```
Deploy P4 + P1 together
       → Users immediately get better experience
Deploy P2 separately
       → Complex change, needs isolation
Deploy P3 anytime
       → Independent enhancement
```

**Recommendation**: Option A for production, Option B acceptable for staging

## Testing Dependencies

### Integration Test Order

1. **Test P4 in isolation**:
   - New user gets GreenScore ✓
   - Existing users backfilled ✓

2. **Test P4 + P1 together**:
   - New user → Loan error message helpful ✓
   - New user → No 400 errors ✓

3. **Test P4 + P2 together**:
   - Evidence upload → GreenScore update ✓
   - Multiple evidence → Score increases ✓

4. **Test all together**:
   - Full user journey works ✓
   - No regressions ✓

## Summary

**Root Dependency**: Priority 4
**Fix Order**: 4 → 2 → 1 → 3
**Can be Parallelized**: P3 only (independent)
**Deployment Risk**: LOW if done in order, HIGH if done out of order
**Total Dependencies**: 3 bugs depend on 1 root cause

---

**See `07-IMPLEMENTATION-PLAN.md` for detailed fix instructions.**
