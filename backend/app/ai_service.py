"""
AI Service module for HaliScore.

This module provides AI-powered scoring and analysis for sustainable practices.
It includes OCR processing, climate-smart practice detection, and Green Score calculation.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta

# Import ML libraries
try:
    import cv2
    import pytesseract
    from PIL import Image
    import requests
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.feature_extraction.text import TfidfVectorizer
except ImportError:
    logging.warning("Some ML libraries not available. Install with: pip install opencv-python pytesseract pillow scikit-learn")

logger = logging.getLogger(__name__)

class GreenScoreAI:
    """AI service for calculating Green Scores based on sustainable practices."""
    
    def __init__(self):
        self.sustainable_keywords = {
            'solar': ['solar', 'photovoltaic', 'renewable energy', 'clean energy'],
            'organic': ['organic', 'natural', 'pesticide-free', 'chemical-free'],
            'recycling': ['recycled', 'recycling', 'reuse', 'upcycle'],
            'water_conservation': ['water saving', 'drip irrigation', 'rainwater harvesting'],
            'energy_efficient': ['led', 'energy efficient', 'low power', 'eco-friendly'],
            'sustainable_farming': ['crop rotation', 'cover crops', 'no-till', 'permaculture']
        }
        
        self.practice_scores = {
            'solar': 25,
            'organic': 20,
            'recycling': 15,
            'water_conservation': 15,
            'energy_efficient': 10,
            'sustainable_farming': 20
        }
        
    def analyze_receipt_ocr(self, image_path: str) -> Dict:
        """Analyze receipt using OCR to detect sustainable purchases."""
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                return {"error": "Could not read image"}
            
            # Preprocess image
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            # Extract text
            text = pytesseract.image_to_string(thresh)
            
            # Analyze for sustainable practices
            analysis = self._analyze_text_for_sustainability(text)
            
            return {
                "text": text,
                "sustainable_practices": analysis,
                "confidence": 0.85
            }
            
        except Exception as e:
            logger.error(f"OCR analysis failed: {e}")
            return {"error": str(e)}
    
    def _analyze_text_for_sustainability(self, text: str) -> Dict:
        """Analyze text for sustainable practices."""
        text_lower = text.lower()
        detected_practices = {}
        
        for practice, keywords in self.sustainable_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected_practices[practice] = {
                        "detected": True,
                        "keyword": keyword,
                        "score": self.practice_scores[practice]
                    }
                    break
        
        return detected_practices
    
    def calculate_green_score(self, user_data: Dict) -> Dict:
        """Calculate comprehensive Green Score based on user data."""
        base_score = 50
        subscores = {}
        explanations = []
        
        # Analyze evidence
        if 'evidence' in user_data:
            for evidence in user_data['evidence']:
                if evidence.get('type') == 'receipt':
                    analysis = self.analyze_receipt_ocr(evidence.get('path', ''))
                    if 'sustainable_practices' in analysis:
                        for practice, details in analysis['sustainable_practices'].items():
                            if details['detected']:
                                subscores[practice] = details['score']
                                explanations.append(f"+{details['score']} {practice} practice detected")
        
        # Analyze business type
        business_type = user_data.get('business_type', '')
        if business_type == 'agriculture':
            base_score += 10
            explanations.append("+10 agriculture business (sustainable potential)")
        
        # Analyze location (if available)
        if 'location' in user_data:
            # Could integrate with climate data APIs here
            base_score += 5
            explanations.append("+5 location data available")
        
        # Calculate final score
        total_score = base_score + sum(subscores.values())
        final_score = min(100, max(0, total_score))
        
        return {
            "score_raw": final_score,
            "score_0_100": final_score,
            "subscores": subscores,
            "explanations": explanations,
            "computed_at": datetime.now().isoformat(),
            "confidence": 0.9
        }
    
    def detect_climate_smart_practices(self, image_path: str) -> Dict:
        """Detect climate-smart practices from images."""
        try:
            # This would integrate with computer vision models
            # For now, return a placeholder
            return {
                "practices_detected": ["solar_panels", "organic_farming"],
                "confidence": 0.75,
                "metadata": {
                    "image_quality": "good",
                    "processing_time": 2.3
                }
            }
        except Exception as e:
            logger.error(f"Climate practice detection failed: {e}")
            return {"error": str(e)}

# Global instance
ai_service = GreenScoreAI()
