"""
FastAPI router for satellite verification endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from .analyzer import SatelliteAnalyzer

router = APIRouter(prefix="/satellite", tags=["satellite"])

class LocationRequest(BaseModel):
    latitude: float
    longitude: float
    radius: Optional[int] = 100

class VerificationResponse(BaseModel):
    success: bool
    has_solar_panels: bool
    confidence: float
    ndvi: Optional[float] = None
    flood_risk_score: Optional[float] = None
    error: Optional[str] = None

@router.post("/verify", response_model=VerificationResponse)
async def verify_location(request: LocationRequest):
    """
    Verify a location using satellite imagery
    - Detects solar panels
    - Calculates NDVI (vegetation health)
    - Assesses flood risk
    """
    analyzer = SatelliteAnalyzer()
    
    try:
        # Run all analyses
        solar_result = analyzer.detect_solar_panels(
            request.latitude, 
            request.longitude, 
            request.radius
        )
        
        ndvi_result = analyzer.calculate_ndvi(
            request.latitude, 
            request.longitude, 
            request.radius
        )
        
        flood_result = analyzer.assess_flood_risk(
            request.latitude, 
            request.longitude, 
            request.radius
        )
        
        # Combine results
        return VerificationResponse(
            success=True,
            has_solar_panels=solar_result["has_solar_panels"],
            confidence=solar_result["confidence"],
            ndvi=ndvi_result["ndvi"],
            flood_risk_score=flood_result["flood_risk_score"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Satellite verification failed: {str(e)}"
        )
