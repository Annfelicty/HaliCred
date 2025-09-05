"""
Database configuration module.

This module sets up the database connection using SQLAlchemy.
It provides a session factory and a dependency for database access.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost/haliscore")

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base - shared across all models
Base = declarative_base()

# Import all models to ensure they're registered with Base
def register_models():
    """Import all model files to register them with Base metadata"""
    try:
        from app import models  # Core models
        from app.db import ai_models  # AI models
    except ImportError as e:
        print(f"Warning: Could not import models: {e}")

register_models()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
