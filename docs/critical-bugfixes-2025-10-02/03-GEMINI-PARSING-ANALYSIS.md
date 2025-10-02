# Gemini JSON Parsing Analysis
**Priority**: 3
**Severity**: HIGH (Degraded Experience)
**Date**: 2025-10-02

## Problem Statement

Gemini AI recommendations fail to parse, resulting in fallback to static recommendations instead of AI-powered personalized suggestions.

## Error Evidence

**Backend Log**:
```
2025-10-02 09:49:35,349 - app.api.ai_engine - WARNING - Failed to parse Gemini JSON response
2025-10-02 09:49:38,546 - app.monitoring.tracing - INFO - Request completed: GET /ai/carbon-credits/recommendations - 200 (30452.21ms)
```

**Observations**:
- Request completes with 200 OK (not an error to users)
- Takes 30+ seconds (slow but expected for AI)
- Falls back to static recommendations gracefully
- Users see recommendations, just not AI-personalized

## Root Cause

**Gemini returns JSON wrapped in markdown code fences**, but parsing logic expects pure JSON.

**Example Gemini Response**:
```
```json
{
  "recommendations": [
    {"action": "Install solar panels", "priority": "high", ...}
  ]
}
```
```

**Current Parsing Code**:
**File**: `backend/app/api/ai_engine.py:559`

```python
recommendations = json.loads(response.text.strip())
```

**Problem**: `response.text` includes markdown syntax ```json ... ```, which `json.loads()` cannot parse.

**Similar Issue In**:
**File**: `backend/app/ai/orchestrator.py:233`

```python
result_data = json.loads(gemini_response)
```

## Current Behavior (Graceful Degradation)

**File**: `backend/app/api/ai_engine.py:563-571`

```python
try:
    recommendations = json.loads(response.text.strip())
    if isinstance(recommendations, list) and len(recommendations) > 0:
        return recommendations[:4]
except json.JSONDecodeError:
    logger.warning("Failed to parse Gemini JSON response")

# Fallback to sector-specific recommendations
sector = business_profile.business_type if business_profile else "general"
return get_fallback_recommendations(sector, current_score)
```

**Good**: Has fallback, users still get recommendations
**Bad**: Never gets AI-powered recommendations

## Solution

### Strip Markdown Code Fences Before Parsing

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
    # Remove ```json at start
    response_text = re.sub(r'^```(?:json|JSON)?\s*\n?', '', response_text)
    # Remove ``` at end
    response_text = re.sub(r'\n?\s*```\s*$', '', response_text)
    response_text = response_text.strip()

recommendations = json.loads(response_text)
```

**File**: `backend/app/ai/orchestrator.py:233`

**Same fix**:
```python
import re

gemini_response_text = gemini_response.strip()

# Strip markdown code fences
if gemini_response_text.startswith("```"):
    gemini_response_text = re.sub(r'^```(?:json|JSON)?\s*\n?', '', gemini_response_text)
    gemini_response_text = re.sub(r'\n?\s*```\s*$', '', gemini_response_text)
    gemini_response_text = gemini_response_text.strip()

result_data = json.loads(gemini_response_text)
```

### Enhanced Error Handling (Optional)

**Additional safety**:
```python
def parse_gemini_json(response_text: str) -> dict:
    """Safely parse Gemini JSON response with markdown stripping"""
    text = response_text.strip()

    # Strip markdown code fences
    if text.startswith("```"):
        text = re.sub(r'^```(?:json|JSON)?\s*\n?', '', text)
        text = re.sub(r'\n?\s*```\s*$', '', text)
        text = text.strip()

    # Try parsing
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # Log the problematic text for debugging
        logger.error(f"JSON parse error: {e}")
        logger.debug(f"Attempted to parse: {text[:200]}...")  # First 200 chars
        raise

# Use in both files:
recommendations = parse_gemini_json(response.text)
```

## Testing

### Unit Tests

**File**: Create `backend/tests/test_gemini_parsing.py`

```python
import pytest
from backend.app.api.ai_engine import parse_gemini_json  # If we create helper

def test_parse_plain_json():
    """Test parsing plain JSON"""
    text = '{"recommendations": []}'
    result = parse_gemini_json(text)
    assert "recommendations" in result

def test_parse_json_with_markdown():
    """Test parsing JSON wrapped in markdown code fences"""
    text = '''```json
    {
      "recommendations": []
    }
    ```'''
    result = parse_gemini_json(text)
    assert "recommendations" in result

def test_parse_json_with_json_label():
    """Test parsing with ```json label"""
    text = '''```json
{"recommendations": []}
```'''
    result = parse_gemini_json(text)
    assert "recommendations" in result

def test_parse_json_with_newlines():
    """Test parsing with extra newlines"""
    text = '''```json

    {"recommendations": []}

    ```'''
    result = parse_gemini_json(text)
    assert "recommendations" in result
```

### Integration Tests

- [ ] Call recommendations endpoint → Verify AI response parsed
- [ ] Check logs → Should NOT see "Failed to parse"
- [ ] Verify recommendations differ based on user context (AI-powered)
- [ ] Test with multiple users → Different recommendations

### Manual Testing

- [ ] Load dashboard → Check recommendations
- [ ] Compare recommendations for different users
- [ ] Verify they're contextual (not all the same)
- [ ] Check backend logs → No parsing failures

## Performance Impact

**No change**: Same API call, just better parsing

## Dependencies

**None**: Independent fix, can deploy anytime

## Rollback

**If issues arise**:
- Revert regex changes
- System falls back to static recommendations (current behavior)
- No user impact (already working with fallback)

## Success Criteria

- [ ] 0% "Failed to parse Gemini JSON" warnings in logs
- [ ] Recommendations are AI-powered (vary by user)
- [ ] Response time unchanged (~30 seconds)
- [ ] Fallback still works if parsing truly fails

## Why This is Priority 3

**Not Critical Because**:
- Has working fallback
- Users still get recommendations
- Doesn't block any user journey
- Just reduces AI value proposition

**But Still Important**:
- Wastes 30 seconds of AI processing
- Wastes Gemini API quota/costs
- Users don't get personalized experience
- Easy fix with low risk

---

**Estimated Effort**: 1-2 hours
**Risk**: LOW (string manipulation, has fallback)
**Can Deploy**: Independently, anytime
