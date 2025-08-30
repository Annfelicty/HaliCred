"""
Emission Calculator Service
Deterministic CO2 emission calculations using real-world factors
"""
import logging
from typing import Dict, Optional, Any
import requests
from datetime import datetime
import json

from .models import EmissionFeatures, EmissionResult

logger = logging.getLogger(__name__)

class EmissionCalculator:
    """Deterministic CO2 emission calculator using climate APIs and local factors"""
    
    def __init__(self, climatiq_api_key: Optional[str] = None):
        self.climatiq_api_key = climatiq_api_key
        self.climatiq_base_url = "https://api.climatiq.io/data/v1"
        
        # Kenya-specific emission factors (fallback values)
        self.kenya_factors = {
            "grid_ef_kg_co2_kwh": 0.45,  # Kenya grid emission factor
            "diesel_kg_co2_liter": 2.68,  # IPCC standard
            "plastic_kg_co2_kg": 6.0,     # Plastic recycling avoided emissions
            "water_pump_kwh_m3": 0.5,     # Energy per m3 water pumped
            "last_updated": "2024-08-30"
        }
        
        # Global fallback factors
        self.global_factors = {
            "grid_ef_kg_co2_kwh": 0.52,  # Global average
            "diesel_kg_co2_liter": 2.68,
            "plastic_kg_co2_kg": 6.0,
            "water_pump_kwh_m3": 0.4
        }

    async def calculate_emissions(
        self, 
        evidence_id: str,
        sector: str,
        features: EmissionFeatures,
        region: str = "Kenya"
    ) -> EmissionResult:
        """Calculate CO2 emissions from evidence features"""
        try:
            # Get current emission factors
            emission_factors = await self._get_emission_factors(region)
            
            # Calculate emissions by component
            co2_components = {}
            
            # Energy savings (grid replacement)
            if features.kwh_saved:
                co2_components["energy_grid_kwh"] = (
                    features.kwh_saved * emission_factors["grid_ef_kg_co2_kwh"]
                )
            
            # Solar generation (grid offset)
            if features.solar_kwh_generated:
                co2_components["solar_generation"] = (
                    features.solar_kwh_generated * emission_factors["grid_ef_kg_co2_kwh"]
                )
            
            # Diesel replacement
            if features.diesel_liters_avoided:
                co2_components["diesel"] = (
                    features.diesel_liters_avoided * emission_factors["diesel_kg_co2_liter"]
                )
            
            # Plastic recycling
            if features.plastic_kg_recycled:
                co2_components["plastic"] = (
                    features.plastic_kg_recycled * emission_factors["plastic_kg_co2_kg"]
                )
            
            # Water savings (indirect energy)
            if features.water_m3_saved:
                water_energy_kwh = features.water_m3_saved * emission_factors["water_pump_kwh_m3"]
                co2_components["water"] = (
                    water_energy_kwh * emission_factors["grid_ef_kg_co2_kwh"]
                )
            
            # Appliance efficiency gains
            if features.appliance_efficiency_gain:
                co2_components["appliance_efficiency"] = (
                    features.appliance_efficiency_gain * emission_factors["grid_ef_kg_co2_kwh"]
                )
            
            # Total CO2 saved
            total_co2_kg = sum(co2_components.values())
            
            # Calculate confidence based on data sources
            confidence = self._calculate_emission_confidence(features, emission_factors)
            
            return EmissionResult(
                evidence_id=evidence_id,
                co2_kg_components=co2_components,
                co2_kg_total=total_co2_kg,
                method=f"Kenya EF {emission_factors['grid_ef_kg_co2_kwh']} kgCO2/kWh + IPCC factors",
                provenance={
                    "ef_source": emission_factors.get("source", "local_fallback"),
                    "ef_value": emission_factors["grid_ef_kg_co2_kwh"],
                    "calculation_date": datetime.now().isoformat(),
                    "region": region,
                    "sector": sector
                },
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error calculating emissions for {evidence_id}: {str(e)}")
            return EmissionResult(
                evidence_id=evidence_id,
                co2_kg_total=0.0,
                method="error_fallback",
                confidence=0.1
            )

    async def _get_emission_factors(self, region: str) -> Dict[str, Any]:
        """Get emission factors from APIs or fallback to local values"""
        try:
            # Try to get Kenya-specific factors from Climatiq API
            if self.climatiq_api_key and region.lower() == "kenya":
                climatiq_factors = await self._fetch_climatiq_factors("KE")
                if climatiq_factors:
                    return {**self.kenya_factors, **climatiq_factors, "source": "climatiq"}
            
            # Fallback to local Kenya factors
            if region.lower() == "kenya":
                return {**self.kenya_factors, "source": "local_kenya"}
            
            # Global fallback
            return {**self.global_factors, "source": "global_fallback"}
            
        except Exception as e:
            logger.error(f"Error fetching emission factors: {str(e)}")
            return {**self.kenya_factors, "source": "error_fallback"}

    async def _fetch_climatiq_factors(self, country_code: str) -> Optional[Dict[str, float]]:
        """Fetch emission factors from Climatiq API"""
        if not self.climatiq_api_key:
            return None
            
        try:
            headers = {
                "Authorization": f"Bearer {self.climatiq_api_key}",
                "Content-Type": "application/json"
            }
            
            # Get electricity emission factor for Kenya
            url = f"{self.climatiq_base_url}/emission-factors"
            params = {
                "category": "electricity",
                "region": country_code,
                "unit_type": "energy",
                "data_version": "latest"
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("results"):
                    # Get the most recent electricity factor
                    factor = data["results"][0]
                    grid_ef = factor.get("factor", self.kenya_factors["grid_ef_kg_co2_kwh"])
                    
                    return {
                        "grid_ef_kg_co2_kwh": grid_ef,
                        "climatiq_factor_id": factor.get("factor_id"),
                        "climatiq_updated": factor.get("valid_from")
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching Climatiq factors: {str(e)}")
            return None

    def _calculate_emission_confidence(
        self, 
        features: EmissionFeatures, 
        emission_factors: Dict[str, Any]
    ) -> float:
        """Calculate confidence in emission calculation"""
        confidence = 0.5  # Base confidence
        
        # Higher confidence for more data points
        feature_count = sum(1 for field in features.__fields__ 
                          if getattr(features, field) is not None)
        confidence += min(feature_count * 0.1, 0.3)
        
        # Higher confidence for API-sourced factors
        if emission_factors.get("source") == "climatiq":
            confidence += 0.2
        elif emission_factors.get("source") == "local_kenya":
            confidence += 0.1
        
        # Lower confidence for very high or very low values (potential outliers)
        total_features = sum(getattr(features, field) or 0 for field in features.__fields__)
        if total_features > 10000:  # Very high values
            confidence -= 0.2
        elif total_features < 1:  # Very low values
            confidence -= 0.1
        
        return max(0.1, min(1.0, confidence))

    def estimate_features_from_amount(
        self, 
        amount_ksh: float, 
        sector: str, 
        action_type: str
    ) -> EmissionFeatures:
        """Estimate emission features from monetary amount and context"""
        features = EmissionFeatures()
        
        try:
            # Sector-specific estimation rules
            if sector == "salon":
                if "led" in action_type.lower() or "light" in action_type.lower():
                    # LED lighting: ~KES 400 per bulb, ~10W saving per bulb
                    bulbs = max(1, amount_ksh / 400)
                    features.kwh_saved = bulbs * 0.01 * 8 * 30  # 10W * 8hrs * 30days
                
                elif "solar" in action_type.lower():
                    # Small solar system: ~KES 50,000 per kW
                    kw_capacity = amount_ksh / 50000
                    features.solar_kwh_generated = kw_capacity * 4 * 30  # 4 sun hours * 30 days
            
            elif sector == "farmer":
                if "solar" in action_type.lower() and "pump" in action_type.lower():
                    # Solar pump: ~KES 80,000 per system
                    pump_size_kw = amount_ksh / 80000
                    features.solar_kwh_generated = pump_size_kw * 6 * 30  # 6 hours * 30 days
                    features.water_m3_saved = pump_size_kw * 100  # Estimated water savings
                
                elif "drip" in action_type.lower():
                    # Drip irrigation: water savings based on area
                    area_hectares = amount_ksh / 15000  # ~KES 15k per hectare
                    features.water_m3_saved = area_hectares * 500  # 500 m3 saved per hectare
            
            elif sector == "welding":
                if "solar" in action_type.lower():
                    # Solar system for welding shop
                    kw_capacity = amount_ksh / 60000  # ~KES 60k per kW
                    features.solar_kwh_generated = kw_capacity * 5 * 25  # 5 hours * 25 days
                
                elif "inverter" in action_type.lower():
                    # Inverter welder efficiency gain
                    power_rating_kw = amount_ksh / 100000  # ~KES 100k per kW
                    features.appliance_efficiency_gain = power_rating_kw * 2 * 8 * 25  # 2kW saving * 8hrs * 25 days
            
            return features
            
        except Exception as e:
            logger.error(f"Error estimating features: {str(e)}")
            return EmissionFeatures()

    async def get_sector_emission_baseline(self, sector: str, region: str = "Kenya") -> Dict[str, float]:
        """Get baseline emission statistics for sector"""
        baselines = {
            "salon": {
                "avg_kwh_month": 150,
                "avg_co2_kg_month": 67.5,  # 150 * 0.45
                "typical_solar_kwh": 60,
                "typical_led_savings": 30
            },
            "farmer": {
                "avg_kwh_month": 200,
                "avg_co2_kg_month": 90,
                "typical_solar_kwh": 120,
                "typical_water_m3": 1000
            },
            "welding": {
                "avg_kwh_month": 800,
                "avg_co2_kg_month": 360,
                "typical_solar_kwh": 400,
                "typical_efficiency_gain": 200
            }
        }
        
        return baselines.get(sector, baselines["salon"])
