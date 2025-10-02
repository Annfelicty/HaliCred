# GreenScore Initialization Analysis
**Priority**: 4 (ROOT DEPENDENCY)
**Severity**: CRITICAL
**Date**: 2025-10-02

## Problem Statement

New users are created without initial GreenScore records in the database, causing cascading failures across the entire platform including loan eligibility failures, dashboard stub data, and broken evidence association.

## Investigation Findings

### Current User Creation Flow

**File**: `backend/app/api/auth.py:330-337`

```python
user = User(
    phone=identifier if contact_type == "phone" else payload.phone,
    email=identifier if contact_type == "email" else payload.email,
    full_name=payload.full_name or "",
    roles=payload.roles or (["borrower"] if contact_type == "phone" else ["underwriter"]),
)
db.add(user)
new_user = True
```

**What's Missing**: NO GreenScore initialization

### Database Schema Analysis

**File**: `backend/app/models.py:75-83`

```python
class GreenScore(Base):
    __tablename__ = "greenscores"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    score = Column(Integer, nullable=False)  # <-- NOT NULL constraint
    subscores = Column(JSON)
    explanation_json = Column(JSON)
    computed_at = Column(TIMESTAMP(timezone=True), server_default=sa.func.now())
    user = relationship("User", back_populates="green_scores")
```

**Key Observations**:
- `score` is NOT NULL - must have a value
- `user_id` is foreign key - one user can have multiple green score records (history)
- No default value specified at database level
- Relationship: `User.green_scores` (one-to-many)

### Impact Analysis

#### 1. Dashboard Shows Stub Data

**File**: `frontend-web/src/Components/SMEApp.tsx:189`

```typescript
greenScore:
  (greenscoreResponse && typeof greenscoreResponse?.greenscore === 'number'
    ? greenscoreResponse.greenscore
    : undefined) ?? cached?.greenScore ?? 0,  // Falls back to 0 (recently fixed from 45)
```

When API returns no green score, frontend defaults to 0 (was 45, causing confusion).

**File**: `frontend-web/src/Components/Sme/SMEDashboard.tsx:218-235`

Category scores use similar fallback logic:
```typescript
ecoCategories = [
  {
    name: 'Energy',
    score: greenScore?.subscores?.energy_efficiency || Math.max(0, user.greenScore - 10),
    // ^^^ Falls back to calculated stub when no subscores exist
  },
  // ... more categories
]
```

#### 2. Loan Eligibility Fails

**File**: `backend/app/services/loan_service.py:231-233, 258-260`

```python
latest_score = db.query(GreenScore).filter(
    GreenScore.user_id == user.id
).order_by(GreenScore.computed_at.desc()).first()

# ...later...
current_score = latest_score.score if latest_score else 0  # <-- Returns 0 for new users
if current_score < sector_profile.min_green_score:
    reasons.append(f"Minimum GreenScore of {sector_profile.min_green_score} required for {sector.value}")
```

**Problem**:
- New user → `latest_score = None` → `current_score = 0`
- Sector profiles require minimum scores (e.g., 30 for farmers)
- Eligibility fails → raises ValueError → HTTP 400

**File**: `backend/app/main.py:536-539`

```python
except ValueError as e:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(e)
    )
```

This converts the eligibility failure into a 400 Bad Request error.

#### 3. Evidence Association Issues

While evidence can be uploaded without a GreenScore, the system expects to UPDATE an existing GreenScore when processing evidence. Without an initial record, the flow is broken.

### User Journey Impact

```
NEW USER REGISTERS
    ↓
NO GREENSCORE IN DATABASE
    ↓
    ├─→ Dashboard API Call → Returns null → Frontend shows stub data
    ├─→ Clicks Loans → API returns 400 "Minimum GreenScore required" → White screen/error
    └─→ Tries to upload evidence → Processes but can't update non-existent score
```

## Root Cause

**The user creation flow does not initialize a GreenScore record for new users.**

This is a **design oversight**, not a code bug. The system was likely designed with the assumption that users would get their first GreenScore through evidence upload, but this creates a chicken-and-egg problem:
- Can't apply for loans without GreenScore
- Can't get GreenScore without uploading evidence
- New users experience is broken from registration

## Solution Design

### Approach 1: Initialize GreenScore on User Creation (RECOMMENDED)

**When**: Immediately after creating User record
**Where**: `backend/app/api/auth.py:337` (after `db.add(user)`)
**What**: Create initial GreenScore(user_id=user.id, score=0, subscores={})

**Pros**:
- Guarantees every user has a GreenScore
- Simplifies all queries (no null checks needed)
- Matches user expectations (see their starting score)
- Enables loan eligibility logic to work correctly

**Cons**:
- Adds ~50ms to registration (database write)
- Requires database migration for existing users

### Approach 2: Handle Null GreenScores Throughout Application

**When**: Everywhere GreenScore is queried
**Where**: Multiple files (loan_service.py, ai_engine.py, dashboard, etc.)
**What**: Add null checks and default handling

**Pros**:
- No database migration needed
- More flexible

**Cons**:
- Complex - requires changes in many files
- Error-prone - easy to miss a null check
- Doesn't match business logic (every user should have a score)
- Doesn't fix the root problem

**Recommendation**: Approach 1 is superior in every way.

## Detailed Fix Implementation

### Step 1: Database Migration for Existing Users

**Purpose**: Ensure all existing users without GreenScore records get initialized

**File**: Create `backend/migrations/init_greenscores_for_existing_users.py`

```python
"""
Migration: Initialize GreenScores for existing users
Date: 2025-10-02
Description: Backfill GreenScore records for users created before this fix
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.database import get_db_engine
from app.models import User, GreenScore
from uuid import uuid4
from datetime import datetime

def run_migration():
    """Create initial GreenScore records for users without them"""
    engine = get_db_engine()
    db = Session(bind=engine)

    try:
        # Find all users without GreenScore records
        users_without_scores = db.query(User).outerjoin(
            GreenScore, User.id == GreenScore.user_id
        ).filter(GreenScore.id == None).all()

        print(f"[INFO] Found {len(users_without_scores)} users without GreenScore records")

        for user in users_without_scores:
            initial_score = GreenScore(
                id=uuid4(),
                user_id=user.id,
                score=0,  # Start at 0 for all users
                subscores={
                    "energy_efficiency": 0,
                    "water_conservation": 0,
                    "waste_management": 0,
                    "sustainable_sourcing": 0,
                    "carbon_reduction": 0
                },
                explanation_json={
                    "message": "Initial score - upload evidence to increase your GreenScore",
                    "created_by": "system_migration"
                },
                computed_at=datetime.utcnow()
            )
            db.add(initial_score)
            print(f"[OK] Initialized GreenScore for user {user.id}")

        db.commit()
        print(f"[SUCCESS] Migration complete. {len(users_without_scores)} users initialized.")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Migration failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
```

**How to Run**:
```bash
cd backend
python migrations/init_greenscores_for_existing_users.py
```

**Rollback Plan**:
- Delete GreenScore records created by this migration (identified by `explanation_json.created_by = "system_migration"`)

### Step 2: Modify User Creation to Initialize GreenScore

**File**: `backend/app/api/auth.py`
**Line**: After line 337 (`new_user = True`)

**Current Code**:
```python
if not user:
    user = User(
        phone=identifier if contact_type == "phone" else payload.phone,
        email=identifier if contact_type == "email" else payload.email,
        full_name=payload.full_name or "",
        roles=payload.roles or (["borrower"] if contact_type == "phone" else ["underwriter"]),
    )
    db.add(user)
    new_user = True
```

**Modified Code**:
```python
if not user:
    user = User(
        phone=identifier if contact_type == "phone" else payload.phone,
        email=identifier if contact_type == "email" else payload.email,
        full_name=payload.full_name or "",
        roles=payload.roles or (["borrower"] if contact_type == "phone" else ["underwriter"]),
    )
    db.add(user)
    db.flush()  # <-- Ensure user.id is generated before creating GreenScore

    # Initialize GreenScore for new user
    from app.models import GreenScore
    from uuid import uuid4
    from datetime import datetime

    initial_greenscore = GreenScore(
        id=uuid4(),
        user_id=user.id,
        score=0,  # New users start at 0
        subscores={
            "energy_efficiency": 0,
            "water_conservation": 0,
            "waste_management": 0,
            "sustainable_sourcing": 0,
            "carbon_reduction": 0
        },
        explanation_json={
            "message": "Welcome! Upload evidence of your eco-friendly practices to build your GreenScore.",
            "pillars": {
                "energy_efficiency": "No data yet",
                "water_conservation": "No data yet",
                "waste_management": "No data yet",
                "sustainable_sourcing": "No data yet",
                "carbon_reduction": "No data yet"
            }
        },
        computed_at=datetime.utcnow()
    )
    db.add(initial_greenscore)

    new_user = True
```

**Important**: Add `db.flush()` to ensure `user.id` is generated before creating the GreenScore record (since it references `user.id` as foreign key).

### Step 3: Update Loan Eligibility Error Handling

**File**: `backend/app/services/loan_service.py:258-260`

**Current Code**:
```python
current_score = latest_score.score if latest_score else 0
if current_score < sector_profile.min_green_score:
    reasons.append(f"Minimum GreenScore of {sector_profile.min_green_score} required for {sector.value}")
```

**Improved Code** (defensive programming):
```python
current_score = latest_score.score if latest_score else 0

# Better error message for new users
if current_score < sector_profile.min_green_score:
    if current_score == 0 and not latest_score:
        reasons.append(f"Please upload evidence of eco-friendly practices to build your GreenScore. Minimum score of {sector_profile.min_green_score} required for loans.")
    else:
        reasons.append(f"Current GreenScore ({current_score}) is below minimum requirement ({sector_profile.min_green_score}) for {sector.value} sector")
```

**Note**: After implementing Step 2, the `not latest_score` condition should never be true, but keeping it for defensive programming.

### Step 4: Frontend Updates

**File**: `frontend-web/src/Components/SMEApp.tsx:189`

**Current Code** (already fixed in previous session):
```typescript
greenScore: ... ?? 0,
```

**No changes needed** - the fix to use 0 instead of 45 is already correct.

**File**: `frontend-web/src/Components/Sme/SMEDashboard.tsx`

**Current Code** (already has fallback logic):
```typescript
const ecoCategories = [
  {
    name: 'Energy',
    score: greenScore?.subscores?.energy_efficiency || Math.max(0, user.greenScore - 10),
    // ...
  }
]
```

**Better Approach** (use actual subscores from database):
```typescript
const ecoCategories = [
  {
    name: 'Energy',
    score: greenScore?.subscores?.energy_efficiency ?? 0,  // Use 0 if no data
    color: 'text-yellow-600'
  },
  {
    name: 'Water',
    score: greenScore?.subscores?.water_conservation ?? 0,
    color: 'text-blue-600'
  },
  {
    name: 'Waste',
    score: greenScore?.subscores?.waste_management ?? 0,
    color: 'text-green-600'
  },
  {
    name: 'Sourcing',
    score: greenScore?.subscores?.sustainable_sourcing ?? 0,
    color: 'text-purple-600'
  },
  {
    name: 'Carbon',
    score: greenScore?.subscores?.carbon_reduction ?? 0,
    color: 'text-emerald-600'
  }
];
```

**Why**: Now that every user has a GreenScore with subscores, we can confidently use the actual values instead of calculated fallbacks.

## Testing Strategy

### Unit Tests

**File**: `backend/tests/test_user_creation.py` (create if doesn't exist)

```python
def test_new_user_gets_initial_greenscore(db_session):
    """Test that new user creation initializes a GreenScore"""
    # Create new user
    user = User(
        phone="+254712345678",
        email="test@example.com",
        full_name="Test User",
        roles=["borrower"]
    )
    db_session.add(user)
    db_session.flush()

    # Initialize GreenScore (mimicking the fix)
    from app.models import GreenScore
    initial_score = GreenScore(
        user_id=user.id,
        score=0,
        subscores={"energy_efficiency": 0, ...},
        explanation_json={"message": "Initial score"}
    )
    db_session.add(initial_score)
    db_session.commit()

    # Verify GreenScore exists
    score = db_session.query(GreenScore).filter(
        GreenScore.user_id == user.id
    ).first()

    assert score is not None
    assert score.score == 0
    assert "energy_efficiency" in score.subscores
    assert score.subscores["energy_efficiency"] == 0
```

### Integration Tests

**Test Scenario 1**: New User Registration Flow
```
1. POST /auth/register with new user data
2. Verify response includes user_id
3. GET /ai/greenscore/current with new user token
4. Verify response has greenscore=0 and all subscores=0
```

**Test Scenario 2**: Loan Eligibility for New User
```
1. Create new user (gets GreenScore=0)
2. POST /loan/quote with amount=50000, tenor=12
3. Verify response is eligibility error (not 400), with clear message about uploading evidence
```

### Manual Testing Checklist

- [ ] Register new user via frontend
- [ ] Check database: `SELECT * FROM greenscores WHERE user_id = '<new_user_id>';`
- [ ] Verify GreenScore record exists with score=0
- [ ] Load dashboard - should show 0 scores (not stub data)
- [ ] Navigate to Loans - should show eligibility requirements (not 400 error)
- [ ] Upload evidence - should update GreenScore from 0 to calculated value

### Database Audit

**Before Deployment**:
```sql
-- Count users without GreenScores
SELECT COUNT(*) FROM users u
LEFT JOIN greenscores g ON u.id = g.user_id
WHERE g.id IS NULL;

-- List users without GreenScores
SELECT u.id, u.full_name, u.email, u.phone, u.created_at
FROM users u
LEFT JOIN greenscores g ON u.id = g.user_id
WHERE g.id IS NULL
ORDER BY u.created_at DESC;
```

**After Migration**:
```sql
-- Verify all users have GreenScores
SELECT COUNT(*) FROM users u
LEFT JOIN greenscores g ON u.id = g.user_id
WHERE g.id IS NULL;
-- Should return 0

-- Verify initial scores
SELECT u.full_name, g.score, g.subscores, g.explanation_json
FROM users u
JOIN greenscores g ON u.id = g.user_id
WHERE g.explanation_json::text LIKE '%system_migration%'
ORDER BY g.computed_at DESC
LIMIT 10;
```

## Rollback Procedure

If the fix causes issues:

### Step 1: Disable GreenScore Initialization in New User Creation
- Comment out the GreenScore creation code in `auth.py`
- Deploy this change immediately

### Step 2: Optionally Rollback Migration
```sql
-- Delete GreenScores created by migration
DELETE FROM greenscores
WHERE explanation_json::jsonb @> '{"created_by": "system_migration"}';
```

### Step 3: Restore Previous Behavior
- Revert code changes in `auth.py`
- Keep null-check logic in `loan_service.py` if added

## Dependencies

**Blocks**:
- Priority 1 (Loans Screen) - cannot be fully fixed without this
- Dashboard data quality
- Evidence processing (partially)

**Blocked By**:
- None - this is the root dependency

## Success Criteria

- [ ] All existing users have GreenScore records
- [ ] All new users get GreenScore = 0 on registration
- [ ] Dashboard shows real data (0 for new users, actual scores for existing)
- [ ] Loan eligibility returns meaningful error instead of 400
- [ ] No regression for users with existing GreenScores
- [ ] Database audit shows zero users without GreenScores

## Performance Impact

- **User Creation**: +50-100ms (one additional database write)
- **Dashboard Load**: No change (query already happens)
- **Loan Quote**: Slightly faster (no null checks needed)

**Overall Impact**: Negligible

## Questions for Product Team

1. **Initial Score Value**: Should new users start at 0 or a different value (e.g., 30 as a "trust score")?
2. **Subscores Structure**: Are the 5 categories (energy, water, waste, sourcing, carbon) finalized?
3. **Welcome Message**: What should the initial `explanation_json` message say to new users?
4. **Loan Access**: Should users with GreenScore = 0 be allowed to view loan offers (at higher rates) or should evidence be mandatory first?

---

**Status**: Ready for implementation
**Estimated Effort**: 4-6 hours (including testing)
**Risk Level**: LOW
