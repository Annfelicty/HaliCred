# Evidence Processing Pydantic Validation Analysis
**Priority**: 2
**Severity**: CRITICAL
**Date**: 2025-10-02

## Problem Statement

Evidence upload fails with Pydantic validation error: `Input should be a valid dictionary or instance of ProcessedEvidence [type=model_type, input_value=EvidenceData(...)`. This prevents users from uploading evidence to build their GreenScore.

## Error Details

**Backend Log**:
```
2025-10-02 09:46:56,147 - app.services.ai_service - ERROR - Error processing evidence request: 1 validation error for AIOrchestrationRequest
evidence
  Input should be a valid dictionary or instance of ProcessedEvidence [type=model_type, input_value=EvidenceData(evidence_id=...alled big solar panel')]

File "C:\Users\USER\Desktop\SCHOOL PROJECTS\HaliCred\backend\app\services\ai_service.py", line 272, in process_evidence_request
    AIOrchestrationRequest(
        evidence=evidence_payload,  # <-- This is EvidenceData, but should be ProcessedEvidence
```

## Investigation Findings

### Data Flow Analysis

**Expected Flow (From Architecture)**:
```
1. User uploads photo/receipt
     ↓
2. Save file → Get file_path
     ↓
3. Create EvidenceData (raw upload metadata)
     ↓
4. Google Vision API → OCR + Computer Vision
     ↓
5. Transform to ProcessedEvidence (with OCR/CV results)
     ↓
6. Pass to AIOrchestrator
     ↓
7. Calculate emissions, scores
     ↓
8. Store GreenScoreResult
```

**Actual Flow (Current Code)**:
```
1. User uploads photo/receipt ✅
     ↓
2. Save file → Get file_path ✅
     ↓
3. Create EvidenceData (raw upload metadata) ✅
     ↓
4. ❌ MISSING: Google Vision processing
     ↓
5. ❌ MISSING: Transform to ProcessedEvidence
     ↓
6. ❌ Pass EvidenceData directly to AIOrchestrator (FAILS!)
```

### Model Structure Analysis

**File**: `backend/app/ai/models.py`

**EvidenceData** (Lines 8-16):
```python
class EvidenceData(BaseModel):
    """Raw evidence data from user upload"""
    evidence_id: str
    user_id: str
    type: Literal["receipt", "photo", "invoice", "meter_reading"]
    file_url: str
    timestamp: datetime
    geo: Optional[Dict[str, float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

**ProcessedEvidence** (Lines 61-71):
```python
class ProcessedEvidence(BaseModel):
    """Processed evidence with OCR and CV results"""
    evidence_id: str
    user_id: str
    type: str
    ocr: OCRResult  # <-- MISSING in EvidenceData
    cv: CVResult    # <-- MISSING in EvidenceData
    features: Optional[EmissionFeatures] = None
    geo: Optional[Dict[str, float]] = None
    timestamp: datetime
    processing_confidence: float = 0.0
```

**Key Difference**:
- `ProcessedEvidence` includes `ocr: OCRResult` and `cv: CVResult`
- These come from Google Vision API processing
- `EvidenceData` is just metadata from the upload

**AIOrchestrationRequest** (Lines 113-118):
```python
class AIOrchestrationRequest(BaseModel):
    """Request for AI orchestration"""
    evidence: ProcessedEvidence  # <-- Expects ProcessedEvidence, not EvidenceData!
    user_profile: Dict[str, Any] = Field(default_factory=dict)
    sector: str
    region: str = "Kenya"
```

### Code Trace

**File**: `backend/app/services/ai_service.py:257-277`

```python
# Create EvidenceData object
evidence_payload = EvidenceData(
    evidence_id=str(evidence.id),
    user_id=user_id,
    type=normalized_type,
    file_url=str(temp_path) if temp_path else file_path,
    timestamp=datetime.utcnow(),
    metadata={
        "file_name": file_name,
        "file_size_mb": file_size_mb,
        "description": description,
    },
)

# ❌ PROBLEM: Pass EvidenceData directly to AIOrchestrator
# Should be ProcessedEvidence!
orchestration_result = await orchestrator.process_request(
    AIOrchestrationRequest(
        evidence=evidence_payload,  # <-- Type mismatch!
        sector=sector,
        region=region,
        user_profile={"user_id": user_id},
    )
)
```

## Root Cause

**The code is missing the Google Vision processing step that transforms EvidenceData into ProcessedEvidence.**

The architecture document (docs/architecture.md) describes this flow:

> "EvidenceProcessor downloads the file (local path or HTTP), runs Google Vision OCR/CV, and estimates features."

But this step is not implemented in the current `ai_service.py` code.

## Google Vision Integration Analysis

### Current Google Vision Setup

**File**: `backend/app/ai/api_client.py`

Google Vision client is initialized on startup:
```python
logger.info("[INIT] Initializing Google Vision client")
logger.info(f"[FILE] Google Vision credentials path: keys/google-vision.json")

from google.cloud import vision
vision_client = vision.ImageAnnotatorClient.from_service_account_json(
    "keys/google-vision.json"
)
logger.info("[OK] Google Vision client initialized successfully")
```

**Startup Log Confirmation**:
```
2025-10-02 09:44:39,676 - app.ai.api_client - INFO - [OK] Google Vision client initialized successfully
2025-10-02 09:44:40,064 - app.ai.api_client - INFO - [OK] Google Vision API validation successful - OCR ready (385.68ms)
```

**So Google Vision IS configured and working** - we just need to USE it!

### Missing Components

Looking at the architecture, there should be an `EvidenceProcessor` class:

**Expected File**: `backend/app/ai/evidence_processor.py` (likely missing or incomplete)

**Expected Functionality**:
1. Read image file from `file_url`
2. Call Google Vision API for:
   - OCR (text detection)
   - Label detection (object recognition)
   - Text extraction with bounding boxes
3. Parse Vision API response into `OCRResult` and `CVResult`
4. Extract emission-related features (e.g., "solar panel", "LED bulb", etc.)
5. Return `ProcessedEvidence`

## Solution Design

### Approach: Implement Evidence Processor

We need to create the missing pipeline step that:
1. Takes `EvidenceData` as input
2. Processes the image with Google Vision
3. Returns `ProcessedEvidence`

### Implementation

#### Step 1: Create Evidence Processor Module

**File**: Create `backend/app/ai/evidence_processor.py`

```python
"""
Evidence Processing Module
Handles Google Vision OCR/CV processing of uploaded evidence
"""
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import requests
from google.cloud import vision
from google.cloud.vision_v1 import types

from app.ai.models import (
    EvidenceData,
    ProcessedEvidence,
    OCRResult,
    CVResult,
    OCRLine,
    BoundingBox,
    EmissionFeatures
)
from app.ai.api_client import vision_client

logger = logging.getLogger(__name__)

class EvidenceProcessor:
    """Processes evidence images using Google Vision API"""

    def __init__(self):
        self.vision_client = vision_client

    async def process_evidence(self, evidence_data: EvidenceData) -> ProcessedEvidence:
        """
        Process evidence through Google Vision API

        Args:
            evidence_data: Raw evidence metadata with file path

        Returns:
            ProcessedEvidence with OCR and CV results
        """
        try:
            logger.info(f"Processing evidence {evidence_data.evidence_id} with Google Vision")

            # Read image file
            image_content = await self._read_image(evidence_data.file_url)

            # Call Google Vision API
            ocr_result = await self._extract_ocr(image_content)
            cv_result = await self._extract_cv(image_content)
            features = await self._extract_features(ocr_result, cv_result, evidence_data.type)

            # Calculate overall processing confidence
            processing_confidence = (ocr_result.confidence + cv_result.confidence) / 2

            # Build ProcessedEvidence
            processed = ProcessedEvidence(
                evidence_id=evidence_data.evidence_id,
                user_id=evidence_data.user_id,
                type=evidence_data.type,
                ocr=ocr_result,
                cv=cv_result,
                features=features,
                geo=evidence_data.geo,
                timestamp=evidence_data.timestamp,
                processing_confidence=processing_confidence
            )

            logger.info(f"Successfully processed evidence {evidence_data.evidence_id} (confidence: {processing_confidence:.2f})")
            return processed

        except Exception as e:
            logger.error(f"Error processing evidence {evidence_data.evidence_id}: {e}")
            # Return minimal processed evidence for graceful degradation
            return self._create_fallback_processed_evidence(evidence_data)

    async def _read_image(self, file_url: str) -> bytes:
        """Read image file from local path or URL"""
        try:
            # Check if it's a local file path
            if Path(file_url).exists():
                with open(file_url, 'rb') as f:
                    return f.read()

            # Otherwise try to fetch from URL
            response = requests.get(file_url, timeout=30)
            response.raise_for_status()
            return response.content

        except Exception as e:
            logger.error(f"Error reading image from {file_url}: {e}")
            raise

    async def _extract_ocr(self, image_content: bytes) -> OCRResult:
        """Extract text using Google Vision OCR"""
        try:
            image = vision.Image(content=image_content)

            # Text detection
            response = self.vision_client.text_detection(image=image)
            texts = response.text_annotations

            if not texts:
                return OCRResult(confidence=0.0, raw_text="")

            # First annotation is the full text
            full_text = texts[0].description if texts else ""

            # Parse individual lines with bounding boxes
            lines = []
            for text in texts[1:]:  # Skip first (full text)
                # Extract bounding box
                vertices = text.bounding_poly.vertices
                bbox = BoundingBox(
                    left=vertices[0].x if vertices else 0,
                    top=vertices[0].y if vertices else 0,
                    width=(vertices[2].x - vertices[0].x) if len(vertices) > 2 else 0,
                    height=(vertices[2].y - vertices[0].y) if len(vertices) > 2 else 0
                )

                lines.append(OCRLine(
                    text=text.description,
                    confidence=0.9,  # Google Vision doesn't provide per-text confidence
                    bounding_box=bbox
                ))

            # Extract structured data (vendor, amount, date, items)
            ocr_result = self._parse_ocr_text(full_text, lines)
            ocr_result.raw_text = full_text
            ocr_result.lines = lines
            ocr_result.confidence = 0.85 if full_text else 0.0

            return ocr_result

        except Exception as e:
            logger.error(f"Error in OCR extraction: {e}")
            return OCRResult(confidence=0.0, raw_text="")

    async def _extract_cv(self, image_content: bytes) -> CVResult:
        """Extract visual features using Google Vision"""
        try:
            image = vision.Image(content=image_content)

            # Label detection
            label_response = self.vision_client.label_detection(image=image)
            labels = [label.description.lower() for label in label_response.label_annotations]

            # Object detection
            object_response = self.vision_client.object_localization(image=image)
            detected_objects = [
                {
                    "name": obj.name,
                    "confidence": obj.score,
                    "bounding_box": {
                        "vertices": [(v.x, v.y) for v in obj.bounding_poly.normalized_vertices]
                    }
                }
                for obj in object_response.localized_object_annotations
            ]

            # Generate caption from labels
            caption = ", ".join(labels[:5]) if labels else "Image analysis"

            # Average confidence
            avg_confidence = (
                sum(label.score for label in label_response.label_annotations) /
                len(label_response.label_annotations)
            ) if label_response.label_annotations else 0.5

            return CVResult(
                labels=labels,
                caption=caption,
                confidence=avg_confidence,
                detected_objects=detected_objects
            )

        except Exception as e:
            logger.error(f"Error in CV extraction: {e}")
            return CVResult(confidence=0.0)

    def _parse_ocr_text(self, full_text: str, lines: list) -> OCRResult:
        """Parse structured data from OCR text"""
        import re
        from datetime import datetime

        ocr_result = OCRResult()

        # Extract vendor (first few lines usually contain vendor name)
        first_lines = full_text.split('\n')[:3]
        ocr_result.vendor = ' '.join(first_lines).strip()[:100] if first_lines else None

        # Extract amount (look for currency patterns)
        amount_patterns = [
            r'KSH?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(?:Total|Amount|Price)[\s:]*KSH?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*KSH?'
        ]

        for pattern in amount_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                ocr_result.amount_ksh = float(amount_str)
                break

        # Extract date
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}-\d{2}-\d{2})'
        ]

        for pattern in date_patterns:
            match = re.search(pattern, full_text)
            if match:
                ocr_result.date = match.group(1)
                break

        # Extract items (lines that look like product names)
        items = []
        for line in lines:
            # Skip lines that are just numbers, dates, or too short
            if len(line.text) > 5 and not re.match(r'^\d+$', line.text.strip()):
                items.append(line.text)

        ocr_result.items = items[:10]  # Limit to 10 items

        return ocr_result

    async def _extract_features(self, ocr: OCRResult, cv: CVResult, evidence_type: str) -> Optional[EmissionFeatures]:
        """Extract emission-related features from OCR and CV results"""
        features = EmissionFeatures()

        combined_text = (ocr.raw_text + " " + " ".join(cv.labels)).lower()

        # Solar panel detection
        if any(keyword in combined_text for keyword in ["solar", "panel", "photovoltaic", "pv"]):
            # Try to extract wattage from OCR
            watt_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:w|watt|kw)', combined_text, re.IGNORECASE)
            if watt_match:
                watts = float(watt_match.group(1))
                if 'kw' in combined_text.lower():
                    watts *= 1000
                # Estimate annual kWh generation (rough: 4 hours/day * 365 days)
                features.solar_kwh_generated = watts * 4 * 365 / 1000
            else:
                # Default estimate for small panel
                features.solar_kwh_generated = 500.0  # 500 kWh/year

        # LED/energy-efficient lighting
        if any(keyword in combined_text for keyword in ["led", "energy saver", "efficient"]):
            # Estimate energy savings (rough: 60W conventional → 10W LED, 8 hours/day)
            features.kwh_saved = 50 * 8 * 365 / 1000  # ~146 kWh/year
            features.appliance_efficiency_gain = 0.8  # 80% efficiency gain

        # Diesel/fuel avoidance
        if any(keyword in combined_text for keyword in ["diesel", "generator", "fuel"]):
            # Try to extract liters from OCR
            liter_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:l|liter|litre)', combined_text, re.IGNORECASE)
            if liter_match:
                features.diesel_liters_avoided = float(liter_match.group(1))

        # Water conservation
        if any(keyword in combined_text for keyword in ["water", "drip", "irrigation", "rainwater"]):
            # Rough estimate
            features.water_m3_saved = 10.0  # 10 m³/year

        # Recycling/waste
        if any(keyword in combined_text for keyword in ["recycle", "compost", "waste"]):
            features.plastic_kg_recycled = 5.0  # 5 kg

        return features if any([
            features.solar_kwh_generated,
            features.kwh_saved,
            features.diesel_liters_avoided,
            features.water_m3_saved,
            features.plastic_kg_recycled
        ]) else None

    def _create_fallback_processed_evidence(self, evidence_data: EvidenceData) -> ProcessedEvidence:
        """Create minimal ProcessedEvidence for graceful degradation"""
        return ProcessedEvidence(
            evidence_id=evidence_data.evidence_id,
            user_id=evidence_data.user_id,
            type=evidence_data.type,
            ocr=OCRResult(confidence=0.0, raw_text="Processing failed"),
            cv=CVResult(confidence=0.0, caption="Processing failed"),
            features=None,
            geo=evidence_data.geo,
            timestamp=evidence_data.timestamp,
            processing_confidence=0.0
        )


# Singleton instance
evidence_processor = EvidenceProcessor()
```

#### Step 2: Modify ai_service.py to Use Evidence Processor

**File**: `backend/app/services/ai_service.py`

**Line**: Replace lines 257-277

**Current Code**:
```python
evidence_payload = EvidenceData(...)
orchestration_result = await orchestrator.process_request(
    AIOrchestrationRequest(evidence=evidence_payload, ...)
)
```

**Modified Code**:
```python
# Create EvidenceData
evidence_data = EvidenceData(
    evidence_id=str(evidence.id),
    user_id=user_id,
    type=normalized_type,
    file_url=str(temp_path) if temp_path else file_path,
    timestamp=datetime.utcnow(),
    metadata={
        "file_name": file_name,
        "file_size_mb": file_size_mb,
        "description": description,
    },
)

# ✅ NEW: Process evidence through Google Vision
from app.ai.evidence_processor import evidence_processor
processed_evidence = await evidence_processor.process_evidence(evidence_data)

logger.info(f"Evidence processed with confidence: {processed_evidence.processing_confidence:.2f}")

# ✅ Now pass ProcessedEvidence (not EvidenceData)
orchestration_result = await orchestrator.process_request(
    AIOrchestrationRequest(
        evidence=processed_evidence,  # <-- Correct type!
        sector=sector,
        region=region,
        user_profile={"user_id": user_id},
    )
)
```

## Testing Strategy

### Unit Tests

**File**: `backend/tests/test_evidence_processor.py` (create)

```python
import pytest
from app.ai.evidence_processor import EvidenceProcessor
from app.ai.models import EvidenceData
from datetime import datetime

@pytest.fixture
def evidence_processor():
    return EvidenceProcessor()

@pytest.fixture
def sample_evidence_data():
    return EvidenceData(
        evidence_id="test-123",
        user_id="user-456",
        type="photo",
        file_url="test_images/solar_panel.jpg",
        timestamp=datetime.utcnow(),
        metadata={"description": "Solar panel installation"}
    )

@pytest.mark.asyncio
async def test_process_evidence_returns_processed_evidence(evidence_processor, sample_evidence_data):
    """Test that evidence processing returns ProcessedEvidence"""
    result = await evidence_processor.process_evidence(sample_evidence_data)

    assert result.evidence_id == sample_evidence_data.evidence_id
    assert result.ocr is not None
    assert result.cv is not None
    assert hasattr(result.ocr, 'raw_text')
    assert hasattr(result.cv, 'labels')
    assert 0 <= result.processing_confidence <= 1

@pytest.mark.asyncio
async def test_solar_panel_feature_extraction(evidence_processor, sample_evidence_data):
    """Test that solar panel is detected and features extracted"""
    result = await evidence_processor.process_evidence(sample_evidence_data)

    if "solar" in result.cv.labels or "solar" in result.ocr.raw_text.lower():
        assert result.features is not None
        assert result.features.solar_kwh_generated is not None
        assert result.features.solar_kwh_generated > 0
```

### Integration Tests

**Test Scenario**: Full Evidence Upload Flow
```
1. Create test image with solar panel
2. POST /ai/evidence/process with image
3. Verify response includes greenscore
4. Check database: ProcessedEvidence saved
5. Check database: GreenScore updated
```

### Manual Testing

- [ ] Upload photo of solar panel → Check OCR extracts text
- [ ] Upload receipt → Check amount/vendor extraction
- [ ] Upload image with no text → Check graceful handling
- [ ] Upload corrupted image → Check error handling
- [ ] Verify Google Vision API calls in logs
- [ ] Verify features extraction (solar_kwh_generated, etc.)

## Performance Considerations

- **Google Vision API**: ~1-3 seconds per image
- **Total Processing Time**: 5-10 seconds (Vision + Gemini + Climatiq)
- **Cost**: $1.50 per 1000 Vision API calls (Text + Label detection)

**Optimization**:
- Consider caching Vision results by image hash
- Batch processing for multiple evidence uploads
- Async processing with job queue (Celery)

## Dependencies

**Requires**:
- Google Vision API credentials (already configured ✅)
- File storage access (already working ✅)
- Priority 4 fix (GreenScore initialization) for proper score updates

**Blocks**:
- Users building their GreenScore
- Evidence-based loan eligibility

## Success Criteria

- [ ] Evidence upload completes without Pydantic validation error
- [ ] Google Vision API called for each upload
- [ ] OCR text extracted from receipts/documents
- [ ] Computer Vision labels extracted from photos
- [ ] Features (solar_kwh_generated, etc.) extracted when relevant
- [ ] ProcessedEvidence passed to AIOrchestrator successfully
- [ ] GreenScore calculated and stored

## Rollback Procedure

If issues arise:
1. Revert `ai_service.py` to pass `EvidenceData` (accept the validation error)
2. Return fallback response to frontend
3. Fix evidence_processor.py and redeploy

---

**Status**: Ready for implementation
**Estimated Effort**: 8-12 hours (including testing)
**Risk Level**: MEDIUM (external API integration)
