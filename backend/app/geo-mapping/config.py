"""
Configuration for Earth Engine and other geospatial services
"""
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from google.oauth2 import service_account
import ee

# Load environment variables
load_dotenv()

def initialize_earth_engine() -> None:
    """Initialize the Earth Engine API with service account credentials"""
    try:
        credentials = service_account.Credentials.from_service_account_info({
            "type": "service_account",
            "project_id": os.getenv("GOOGLE_CLOUD_PROJECT_ID"),
            "private_key": os.getenv("GOOGLE_EARTH_ENGINE_PRIVATE_KEY").replace('\\n', '\n'),
            "client_email": os.getenv("GOOGLE_EARTH_ENGINE_CLIENT_EMAIL"),
            "token_uri": "https://oauth2.googleapis.com/token",
        })
        
        ee.Initialize(credentials)
    except Exception as e:
        print(f"Failed to initialize Earth Engine: {str(e)}")
        # Fallback to Sentinel Hub if available
        if os.getenv("SENTINEL_HUB_API_KEY"):
            print("Falling back to Sentinel Hub")
        else:
            raise e

# Constants for analysis
SOLAR_PANEL_DETECTION_THRESHOLD = 0.8  # Confidence threshold for solar panel detection
NDVI_THRESHOLD = 0.3  # Threshold for healthy vegetation
FLOOD_RISK_THRESHOLD = 0.5  # Threshold for flood risk assessment

# Image collection IDs
SENTINEL_2_COLLECTION = 'COPERNICUS/S2_SR'  # Sentinel-2 surface reflectance
LANDSAT_8_COLLECTION = 'LANDSAT/LC08/C02/T1_L2'  # Landsat 8 surface reflectance
