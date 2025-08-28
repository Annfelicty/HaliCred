"""
Irrigation analysis module for detecting and verifying irrigation methods
"""
from typing import Dict, List, Optional
import ee
from datetime import datetime, timedelta
import numpy as np

from .config import (
    SENTINEL_2_COLLECTION,
    MOISTURE_THRESHOLD,
    IRRIGATION_PATTERNS
)

class IrrigationAnalyzer:
    def __init__(self):
        """Initialize the irrigation analyzer"""
        self.initialized = False
        try:
            ee.Initialize()
            self.initialized = True
        except Exception as e:
            print(f"Earth Engine initialization failed: {e}")

    def detect_irrigation_method(
        self,
        latitude: float,
        longitude: float,
        claimed_method: str,
        radius: int = 100
    ) -> Dict[str, any]:
        """
        Detect and verify irrigation method using satellite imagery

        Args:
            latitude: Location latitude
            longitude: Location longitude
            claimed_method: The irrigation method claimed by the farmer
            radius: Analysis radius in meters

        Returns:
            Dict containing irrigation analysis results
        """
        try:
            point = ee.Geometry.Point([longitude, latitude])
            region = point.buffer(radius)

            # Get recent Sentinel-2 imagery time series
            end_date = ee.Date(datetime.now())
            start_date = end_date.advance(-3, 'month')  # Analysis over 3 months

            image_collection = (ee.ImageCollection(SENTINEL_2_COLLECTION)
                             .filterBounds(region)
                             .filterDate(start_date, end_date)
                             .sort('CLOUD_COVERAGE_ASSESSMENT'))

            if image_collection.size().getInfo() == 0:
                return {
                    "success": False,
                    "error": "No recent imagery available",
                    "verified": False
                }

            # Calculate moisture index time series
            moisture_series = self._calculate_moisture_series(image_collection, region)
            
            # Detect irrigation patterns
            detected_method = self._analyze_irrigation_pattern(moisture_series)
            
            # Compare with claimed method
            verified = self._verify_irrigation_method(detected_method, claimed_method)

            return {
                "success": True,
                "verified": verified,
                "detected_method": detected_method,
                "claimed_method": claimed_method,
                "confidence_score": self._calculate_confidence_score(moisture_series, claimed_method),
                "moisture_pattern": moisture_series
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "verified": False
            }

    def _calculate_moisture_series(
        self,
        image_collection: ee.ImageCollection,
        region: ee.Geometry
    ) -> List[float]:
        """Calculate moisture index time series from image collection"""
        def calculate_moisture(image):
            # Using NDMI (Normalized Difference Moisture Index)
            nir = image.select('B8')
            swir = image.select('B11')
            ndmi = nir.subtract(swir).divide(nir.add(swir))
            
            return ndmi.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region,
                scale=10
            ).get('B8')

        moisture_values = image_collection.map(calculate_moisture).aggregate_array('B8')
        return moisture_values.getInfo()

    def _analyze_irrigation_pattern(self, moisture_series: List[float]) -> str:
        """Analyze moisture patterns to determine irrigation method"""
        if not moisture_series:
            return "unknown"

        # Convert to numpy array for analysis
        moisture_array = np.array(moisture_series)
        
        # Calculate pattern features
        variability = np.std(moisture_array)
        regularity = self._calculate_regularity(moisture_array)
        spatial_uniformity = self._estimate_spatial_uniformity(moisture_array)

        # Pattern matching
        if variability < 0.1 and regularity > 0.8:
            return "drip"  # Consistent moisture levels indicate drip irrigation
        elif variability > 0.2 and regularity < 0.5:
            return "sprinkler"  # More variable pattern indicates sprinkler
        elif spatial_uniformity < 0.6:
            return "flood"  # Less uniform distribution suggests flood irrigation
        else:
            return "unknown"

    def _calculate_regularity(self, moisture_array: np.ndarray) -> float:
        """Calculate temporal regularity of moisture patterns"""
        # Using autocorrelation as a measure of regularity
        if len(moisture_array) < 2:
            return 0.0
        
        autocorr = np.correlate(moisture_array, moisture_array, mode='full')
        autocorr = autocorr[len(autocorr)//2:]
        return float(autocorr[1] / autocorr[0])

    def _estimate_spatial_uniformity(self, moisture_array: np.ndarray) -> float:
        """Estimate spatial uniformity from temporal patterns"""
        if len(moisture_array) < 2:
            return 0.0
        
        # Using coefficient of variation as inverse measure of uniformity
        cv = np.std(moisture_array) / np.mean(moisture_array)
        return float(1.0 - min(cv, 1.0))

    def _verify_irrigation_method(self, detected: str, claimed: str) -> bool:
        """Verify if detected irrigation method matches claimed method"""
        if detected == "unknown":
            return False
            
        # Allow for some flexibility in verification
        method_groups = {
            "drip": ["drip", "micro-irrigation", "trickle"],
            "sprinkler": ["sprinkler", "spray", "center-pivot"],
            "flood": ["flood", "surface", "furrow", "basin"]
        }
        
        detected_group = next((group for group, methods in method_groups.items() 
                             if detected in methods), "unknown")
        claimed_group = next((group for group, methods in method_groups.items() 
                            if claimed.lower() in methods), "unknown")
        
        return detected_group == claimed_group

    def _calculate_confidence_score(
        self,
        moisture_series: List[float],
        claimed_method: str
    ) -> float:
        """Calculate confidence score for the irrigation method verification"""
        if not moisture_series:
            return 0.0

        moisture_array = np.array(moisture_series)
        
        # Calculate basic statistics
        variability = np.std(moisture_array)
        regularity = self._calculate_regularity(moisture_array)
        uniformity = self._estimate_spatial_uniformity(moisture_array)
        
        # Method-specific confidence calculations
        method_confidence = {
            "drip": 0.8 * regularity + 0.2 * uniformity,
            "sprinkler": 0.6 * uniformity + 0.4 * (1 - variability),
            "flood": 0.7 * (1 - uniformity) + 0.3 * variability
        }
        
        # Get confidence for claimed method
        base_confidence = method_confidence.get(claimed_method.lower(), 0.5)
        
        # Adjust confidence based on data quality
        data_quality = min(1.0, len(moisture_series) / 10)  # Normalize by expected samples
        
        return float(base_confidence * data_quality)
