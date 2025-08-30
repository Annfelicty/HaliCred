"""
Sector Baseline Service
Provides sector-specific baseline statistics for relative scoring
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json

from .models import SectorBaseline

logger = logging.getLogger(__name__)

class SectorBaselineService:
    """Manages sector baseline statistics for relative GreenScore computation"""
    
    def __init__(self):
        # Kenya sector baselines (from national surveys and industry data)
        self.baselines = {
            "salon": {
                "region": "Kenya",
                "baseline": {
                    "avg_kwh_month": 150.0,
                    "std_kwh_month": 45.0,
                    "avg_co2_ann_kg": 810.0,  # 150 * 12 * 0.45
                    "std_co2_ann_kg": 243.0,
                    "avg_water_m3_month": 5.0,
                    "avg_waste_kg_month": 15.0,
                    "renewable_adoption_pct": 0.12,  # 12% have solar
                    "led_adoption_pct": 0.35,  # 35% use LED
                    "sample_size": 1200
                },
                "data_source": "Kenya Bureau of Statistics 2024 + Industry Survey",
                "last_updated": datetime(2024, 8, 1)
            },
            
            "farmer": {
                "region": "Kenya", 
                "baseline": {
                    "avg_kwh_month": 80.0,  # Lower grid usage, more diesel
                    "std_kwh_month": 35.0,
                    "avg_co2_ann_kg": 1200.0,  # Includes diesel generator usage
                    "std_co2_ann_kg": 400.0,
                    "avg_water_m3_season": 2000.0,  # Per growing season
                    "avg_diesel_liters_month": 25.0,
                    "drip_adoption_pct": 0.08,  # 8% use drip irrigation
                    "solar_pump_adoption_pct": 0.15,  # 15% have solar pumps
                    "sample_size": 2800
                },
                "data_source": "Ministry of Agriculture 2024 + KALRO Survey",
                "last_updated": datetime(2024, 7, 15)
            },
            
            "welding": {
                "region": "Kenya",
                "baseline": {
                    "avg_kwh_month": 800.0,  # High energy usage
                    "std_kwh_month": 250.0,
                    "avg_co2_ann_kg": 4320.0,  # 800 * 12 * 0.45
                    "std_co2_ann_kg": 1350.0,
                    "avg_diesel_liters_month": 40.0,  # Backup generators
                    "efficient_equipment_pct": 0.25,  # 25% have inverter welders
                    "solar_adoption_pct": 0.18,  # 18% have solar
                    "sample_size": 450
                },
                "data_source": "Kenya Association of Manufacturers 2024",
                "last_updated": datetime(2024, 6, 30)
            },
            
            "other": {
                "region": "Kenya",
                "baseline": {
                    "avg_kwh_month": 200.0,
                    "std_kwh_month": 80.0,
                    "avg_co2_ann_kg": 1080.0,
                    "std_co2_ann_kg": 432.0,
                    "renewable_adoption_pct": 0.15,
                    "sample_size": 800
                },
                "data_source": "General SME Survey 2024",
                "last_updated": datetime(2024, 8, 1)
            }
        }

    async def get_baseline(self, sector: str, region: str = "Kenya") -> SectorBaseline:
        """Get baseline statistics for a sector"""
        try:
            sector_key = sector.lower()
            if sector_key not in self.baselines:
                sector_key = "other"  # Fallback to general baseline
            
            baseline_data = self.baselines[sector_key]
            
            return SectorBaseline(
                sector=sector,
                region=region,
                baseline=baseline_data["baseline"],
                data_source=baseline_data["data_source"],
                last_updated=baseline_data["last_updated"]
            )
            
        except Exception as e:
            logger.error(f"Error getting baseline for sector {sector}: {str(e)}")
            # Return minimal baseline on error
            return SectorBaseline(
                sector=sector,
                region=region,
                baseline={"avg_kwh_month": 100.0, "avg_co2_ann_kg": 540.0},
                data_source="error_fallback"
            )

    def calculate_percentile(self, value: float, mean: float, std: float) -> float:
        """Calculate percentile of value within normal distribution"""
        try:
            if std <= 0:
                return 0.5  # Default to median if no variance
            
            # Simple z-score to percentile approximation
            z_score = (value - mean) / std
            
            # Clamp z-score to reasonable range
            z_score = max(-3.0, min(3.0, z_score))
            
            # Convert z-score to percentile (approximation)
            # Using cumulative distribution function approximation
            if z_score >= 0:
                percentile = 0.5 + 0.5 * (1 - (1 / (1 + 0.196854 * z_score + 0.115194 * z_score**2 + 0.000344 * z_score**3 + 0.019527 * z_score**4)))
            else:
                percentile = 0.5 - 0.5 * (1 - (1 / (1 + 0.196854 * abs(z_score) + 0.115194 * z_score**2 + 0.000344 * abs(z_score)**3 + 0.019527 * z_score**4)))
            
            return max(0.01, min(0.99, percentile))
            
        except Exception as e:
            logger.error(f"Error calculating percentile: {str(e)}")
            return 0.5  # Default to median

    async def get_sector_comparison(
        self, 
        sector: str, 
        user_metrics: Dict[str, float],
        region: str = "Kenya"
    ) -> Dict[str, float]:
        """Compare user metrics against sector baseline and return percentiles"""
        try:
            baseline = await self.get_baseline(sector, region)
            
            comparisons = {}
            
            # Compare each metric where we have both user data and baseline
            metric_mappings = {
                "kwh_month": ("avg_kwh_month", "std_kwh_month"),
                "co2_ann_kg": ("avg_co2_ann_kg", "std_co2_ann_kg"),
                "water_m3": ("avg_water_m3_season", "std_water_m3_season"),
                "diesel_liters": ("avg_diesel_liters_month", "std_diesel_liters_month")
            }
            
            for user_metric, (baseline_mean_key, baseline_std_key) in metric_mappings.items():
                if user_metric in user_metrics and baseline_mean_key in baseline.baseline:
                    user_value = user_metrics[user_metric]
                    baseline_mean = baseline.baseline[baseline_mean_key]
                    baseline_std = baseline.baseline.get(baseline_std_key, baseline_mean * 0.3)  # 30% std if not available
                    
                    percentile = self.calculate_percentile(user_value, baseline_mean, baseline_std)
                    comparisons[user_metric + "_percentile"] = percentile
            
            return comparisons
            
        except Exception as e:
            logger.error(f"Error in sector comparison: {str(e)}")
            return {}

    def get_sector_weights(self, sector: str) -> Dict[str, float]:
        """Get sector-specific weights for different impact categories"""
        weights = {
            "salon": {
                "energy": 0.35,    # High energy usage
                "water": 0.15,     # Moderate water usage
                "waste": 0.25,     # Significant waste (chemicals, packaging)
                "carbon": 0.20,    # Carbon from energy
                "community": 0.05  # Lower community impact
            },
            
            "farmer": {
                "energy": 0.25,    # Moderate energy (pumps, processing)
                "water": 0.40,     # Very high water usage
                "waste": 0.10,     # Lower waste generation
                "carbon": 0.20,    # Carbon from fuel and energy
                "community": 0.05  # Community impact through food production
            },
            
            "welding": {
                "energy": 0.45,    # Very high energy usage
                "water": 0.05,     # Low water usage
                "waste": 0.15,     # Metal waste, consumables
                "carbon": 0.30,    # High carbon from energy and processes
                "community": 0.05  # Lower direct community impact
            },
            
            "other": {
                "energy": 0.30,
                "water": 0.20,
                "waste": 0.20,
                "carbon": 0.25,
                "community": 0.05
            }
        }
        
        return weights.get(sector.lower(), weights["other"])

    async def update_baseline(
        self, 
        sector: str, 
        new_data: Dict[str, float],
        region: str = "Kenya"
    ) -> bool:
        """Update baseline with new data point (for continuous learning)"""
        try:
            # In a real system, this would update the baseline statistics
            # For now, we'll just log the update
            logger.info(f"Baseline update for {sector}: {new_data}")
            
            # TODO: Implement incremental baseline updates
            # This would involve:
            # 1. Storing individual data points
            # 2. Recalculating running statistics
            # 3. Detecting significant shifts in baseline
            # 4. Updating the baseline dictionary
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating baseline: {str(e)}")
            return False

    def get_improvement_suggestions(
        self, 
        sector: str, 
        current_percentiles: Dict[str, float]
    ) -> List[str]:
        """Get sector-specific improvement suggestions based on percentiles"""
        suggestions = []
        
        try:
            if sector.lower() == "salon":
                if current_percentiles.get("kwh_month_percentile", 0.5) < 0.3:
                    suggestions.append("Consider LED lighting upgrade to reduce energy consumption")
                if current_percentiles.get("water_m3_percentile", 0.5) < 0.4:
                    suggestions.append("Install water-efficient fixtures and recycling systems")
                suggestions.append("Switch to eco-friendly hair products and packaging")
                
            elif sector.lower() == "farmer":
                if current_percentiles.get("water_m3_percentile", 0.5) < 0.3:
                    suggestions.append("Implement drip irrigation to reduce water usage by 30-50%")
                if current_percentiles.get("diesel_liters_percentile", 0.5) < 0.4:
                    suggestions.append("Install solar water pump to eliminate diesel dependency")
                suggestions.append("Use organic fertilizers and integrated pest management")
                
            elif sector.lower() == "welding":
                if current_percentiles.get("kwh_month_percentile", 0.5) < 0.3:
                    suggestions.append("Upgrade to inverter welding machines for 30% energy savings")
                suggestions.append("Install solar panels to offset high energy consumption")
                suggestions.append("Implement metal recycling and waste reduction practices")
                
            else:
                suggestions.append("Consider renewable energy solutions for your business")
                suggestions.append("Implement energy-efficient equipment and practices")
                suggestions.append("Explore waste reduction and recycling opportunities")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {str(e)}")
            return ["Focus on energy efficiency and renewable energy adoption"]
