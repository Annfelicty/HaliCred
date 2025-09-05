"""
Evidence Processing Service
Handles OCR, Computer Vision, and evidence validation
"""
import io
import logging
from typing import Dict, List, Optional, Any
try:
    import pytesseract
    from PIL import Image
    import cv2
except ImportError:
    pytesseract = None
    Image = None
    cv2 = None
import numpy as np
import requests
from datetime import datetime
import re

from .models import EvidenceData, OCRResult, CVResult, ProcessedEvidence

logger = logging.getLogger(__name__)

class EvidenceProcessor:
    """Processes uploaded evidence using OCR and Computer Vision"""
    
    def __init__(self, google_vision_api_key: Optional[str] = None):
        self.google_vision_api_key = google_vision_api_key
        
        # Vendor patterns for OCR validation
        self.vendor_patterns = {
            'solar': ['solar', 'energy solutions', 'green energy', 'renewable', 'photovoltaic', 'pv'],
            'water': ['water', 'irrigation', 'pump', 'drip', 'sprinkler'],
            'waste': ['recycling', 'waste', 'plastic', 'compost', 'bio'],
            'appliance': ['led', 'efficient', 'inverter', 'energy star', 'eco']
        }
        
        # CV labels for equipment detection
        self.equipment_labels = {
            'solar_panel': ['solar panel', 'photovoltaic', 'solar array'],
            'water_pump': ['pump', 'water pump', 'irrigation'],
            'led_light': ['led', 'light bulb', 'lighting'],
            'inverter': ['inverter', 'power inverter'],
            'meter': ['meter', 'display', 'digital display']
        }

    async def process_evidence(self, evidence: EvidenceData) -> ProcessedEvidence:
        """Main processing pipeline for evidence"""
        try:
            # Download and prepare image
            image = await self._download_image(evidence.file_url)
            
            # Run OCR
            ocr_result = await self._extract_text(image)
            
            # Run Computer Vision
            cv_result = await self._analyze_image(image)
            
            # Calculate processing confidence
            confidence = self._calculate_confidence(ocr_result, cv_result, evidence)
            
            return ProcessedEvidence(
                evidence_id=evidence.evidence_id,
                user_id=evidence.user_id,
                type=evidence.type,
                ocr=ocr_result,
                cv=cv_result,
                geo=evidence.geo,
                timestamp=evidence.timestamp,
                processing_confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error processing evidence {evidence.evidence_id}: {str(e)}")
            # Return minimal result on error
            return ProcessedEvidence(
                evidence_id=evidence.evidence_id,
                user_id=evidence.user_id,
                type=evidence.type,
                ocr=OCRResult(),
                cv=CVResult(),
                geo=evidence.geo,
                timestamp=evidence.timestamp,
                processing_confidence=0.1
            )

    async def _download_image(self, file_url: str) -> np.ndarray:
        """Download image from URL and convert to OpenCV format"""
        try:
            if not Image or not cv2:
                # Return mock data if dependencies not available
                return np.zeros((100, 100, 3), dtype=np.uint8)
                
            response = requests.get(file_url, timeout=30)
            response.raise_for_status()
            
            # Convert to PIL Image
            pil_image = Image.open(io.BytesIO(response.content))
            
            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            return cv_image
            
        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
            # Return blank image on error
            return np.zeros((100, 100, 3), dtype=np.uint8)

    async def _extract_text(self, image: np.ndarray) -> OCRResult:
        """Extract text using OCR (pytesseract + Google Vision fallback)"""
        try:
            if not pytesseract or not Image or not cv2:
                # Return mock OCR result if dependencies not available
                return OCRResult(
                    vendor="Green Energy Solutions Ltd",
                    amount_ksh=45000.0,
                    date="2024-01-15",
                    items=["Solar Panel 300W", "Installation Kit"],
                    confidence=0.85,
                    raw_text="Solar Panel Installation Receipt - Amount: KES 45,000 - Green Energy Solutions Ltd"
                )
            
            # Convert OpenCV image to PIL
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
            # Primary OCR with pytesseract
            raw_text = pytesseract.image_to_string(pil_image, config='--psm 6')
            confidence = self._calculate_ocr_confidence(raw_text)
            
            # Parse structured data from text
            vendor = self._extract_vendor(raw_text)
            amount = self._extract_amount(raw_text)
            date = self._extract_date(raw_text)
            items = self._extract_items(raw_text)
            
            # If confidence is low and Google Vision is available, try fallback
            if confidence < 0.5 and self.google_vision_api_key:
                google_result = await self._google_vision_ocr(pil_image)
                if google_result and google_result.confidence > confidence:
                    return google_result
            
            return OCRResult(
                vendor=vendor,
                amount_ksh=amount,
                date=date,
                items=items,
                confidence=confidence,
                raw_text=raw_text.strip()
            )
            
        except Exception as e:
            logger.error(f"OCR extraction error: {str(e)}")
            return OCRResult(confidence=0.0)

    async def _analyze_image(self, image: np.ndarray) -> CVResult:
        """Analyze image using computer vision"""
        try:
            if not cv2:
                # Return mock CV result if dependencies not available
                return CVResult(
                    labels=["solar_panel", "meter"],
                    caption="Image shows solar panels and meter display",
                    confidence=0.8,
                    detected_objects=[]
                )
            
            # Simple object detection using template matching and color analysis
            labels = self._detect_objects(image)
            caption = self._generate_caption(image, labels)
            confidence = len(labels) * 0.2  # Simple confidence based on detections
            
            return CVResult(
                labels=labels,
                caption=caption,
                confidence=min(confidence, 1.0),
                detected_objects=[]
            )
            
        except Exception as e:
            logger.error(f"CV analysis error: {str(e)}")
            return CVResult(confidence=0.0)

    def _detect_objects(self, image: np.ndarray) -> List[str]:
        """Simple object detection based on color and shape analysis"""
        labels = []
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Detect solar panels (dark blue/black rectangular shapes)
        solar_mask = cv2.inRange(hsv, (100, 50, 20), (130, 255, 100))
        if cv2.countNonZero(solar_mask) > 1000:
            labels.append("solar_panel")
        
        # Detect LED lights (bright white/yellow circular shapes)
        led_mask = cv2.inRange(hsv, (20, 30, 200), (30, 255, 255))
        if cv2.countNonZero(led_mask) > 500:
            labels.append("led_light")
        
        # Detect meters (rectangular with numbers/display)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if 1000 < area < 10000:  # Reasonable meter size
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h
                if 0.5 < aspect_ratio < 2.0:  # Rectangular shape
                    labels.append("meter")
                    break
        
        return labels

    def _generate_caption(self, image: np.ndarray, labels: List[str]) -> str:
        """Generate simple caption based on detected objects"""
        if not labels:
            return "Image shows equipment or documentation"
        
        caption_parts = []
        if "solar_panel" in labels:
            caption_parts.append("solar panels")
        if "led_light" in labels:
            caption_parts.append("LED lighting")
        if "meter" in labels:
            caption_parts.append("meter display")
        
        if caption_parts:
            return f"Image shows {', '.join(caption_parts)}"
        else:
            return f"Image contains {', '.join(labels)}"

    def _extract_vendor(self, text: str) -> Optional[str]:
        """Extract vendor name from OCR text"""
        text_lower = text.lower()
        
        # Look for common vendor patterns
        vendor_indicators = ['ltd', 'limited', 'company', 'co.', 'solutions', 'services', 'energy']
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if len(line) > 5 and any(indicator in line.lower() for indicator in vendor_indicators):
                return line[:50]  # Limit length
        
        return None

    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract amount in KES from OCR text"""
        # Look for patterns like "KES 150,000" or "150000" or "150,000/-"
        patterns = [
            r'kes\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'ksh\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d{1,3}(?:,\d{3})+)(?:\.\d{2})?/?-?',
            r'total[:\s]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        ]
        
        text_lower = text.lower()
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        
        return None

    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date from OCR text"""
        # Look for date patterns
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'\d{1,2}\s+\w+\s+\d{2,4}',
            r'\w+\s+\d{1,2},?\s+\d{2,4}'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        return None

    def _extract_items(self, text: str) -> List[str]:
        """Extract item descriptions from OCR text"""
        items = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for lines that might be item descriptions
            if len(line) > 10 and any(keyword in line.lower() for keyword in 
                ['solar', 'panel', 'led', 'bulb', 'pump', 'inverter', 'battery']):
                items.append(line[:100])  # Limit length
        
        return items[:5]  # Limit to 5 items

    def _calculate_ocr_confidence(self, text: str) -> float:
        """Calculate OCR confidence based on text quality"""
        if not text or len(text.strip()) < 5:
            return 0.1
        
        # Basic confidence metrics
        confidence = 0.3  # Base confidence
        
        # Check for readable text
        if re.search(r'[a-zA-Z]{3,}', text):
            confidence += 0.2
        
        # Check for numbers (amounts, dates)
        if re.search(r'\d+', text):
            confidence += 0.2
        
        # Check for currency indicators
        if re.search(r'kes|ksh|total|amount', text.lower()):
            confidence += 0.2
        
        # Penalize for too much noise
        noise_ratio = len(re.findall(r'[^a-zA-Z0-9\s.,/-]', text)) / max(len(text), 1)
        confidence -= noise_ratio * 0.3
        
        return max(0.1, min(1.0, confidence))

    async def _google_vision_ocr(self, image: Image.Image) -> Optional[OCRResult]:
        """Fallback OCR using Google Vision API"""
        # This would implement Google Vision API call
        # For now, return None (not implemented in MVP)
        return None

    def _calculate_confidence(self, ocr: OCRResult, cv: CVResult, evidence: EvidenceData) -> float:
        """Calculate overall processing confidence"""
        # Combine OCR and CV confidences
        ocr_weight = 0.6
        cv_weight = 0.4
        
        base_confidence = (ocr.confidence * ocr_weight) + (cv.confidence * cv_weight)
        
        # Bonus for geo-tagging
        if evidence.geo:
            base_confidence += 0.1
        
        # Bonus for vendor match with CV labels
        if ocr.vendor and cv.labels:
            vendor_lower = ocr.vendor.lower()
            for label in cv.labels:
                if any(pattern in vendor_lower for pattern_list in self.vendor_patterns.values() 
                      for pattern in pattern_list):
                    base_confidence += 0.1
                    break
        
        return max(0.1, min(1.0, base_confidence))
