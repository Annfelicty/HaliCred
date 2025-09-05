"""
Database initialization script.

This script creates all database tables and initializes the database.
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import Base
from app.config import settings
from app import models  # Import core models
from app.db import ai_models  # Import AI models

def init_db():
    """Initialize the database with all tables."""
    try:
        # Create engine
        engine = create_engine(settings.DATABASE_URL)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("Database tables created successfully!")
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Add initial data
        from app.models import User, BusinessProfile
        from app.db.ai_models import SectorBaseline
        from datetime import datetime
        import uuid
        
        # Check if tables are empty and add seed data
        existing_users = db.query(User).first()
        if not existing_users:
            # Create demo user
            demo_user = User(
                phone="+254700000000",
                full_name="Demo User",
                roles=["borrower"]
            )
            db.add(demo_user)
            db.flush()  # Get the user ID
            
            # Create demo business profile
            profile = BusinessProfile(
                user_id=demo_user.id,
                business_type="agriculture",  
                business_name="Green Farm Demo",
                location="Nairobi, Kenya"
            )
            db.add(profile)
            
            # Add sector baseline data
            baselines = [
                {
                    "sector": "agriculture",
                    "region": "Kenya",
                    "baseline_data": {
                        "average_greenscore": 58,
                        "std_greenscore": 18,
                        "energy_efficiency": 45,
                        "water_conservation": 52,
                        "waste_management": 38
                    },
                    "data_source": "Kenya Agriculture Census 2023",
                    "sample_size": 1250
                },
                {
                    "sector": "beauty",
                    "region": "Kenya", 
                    "baseline_data": {
                        "average_greenscore": 48,
                        "std_greenscore": 15,
                        "energy_efficiency": 42,
                        "water_conservation": 35,
                        "waste_management": 55
                    },
                    "data_source": "SME Survey 2023",
                    "sample_size": 890
                }
            ]
            
            for baseline_data in baselines:
                baseline = SectorBaseline(
                    sector=baseline_data["sector"],
                    region=baseline_data["region"],
                    baseline_data=baseline_data["baseline_data"],
                    data_source=baseline_data["data_source"],
                    sample_size=baseline_data["sample_size"]
                )
                db.add(baseline)
            
            db.commit()
            print("Seed data created successfully!")
        
        db.close()
        print("Database initialization completed!")
        
    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise

if __name__ == "__main__":
    init_db()
