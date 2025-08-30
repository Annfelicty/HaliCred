"""
Startup script for HaliScore backend.

This script initializes the database and starts the FastAPI application.
"""

import uvicorn
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

def main():
    """Main function to start the application."""
    try:
        # Initialize database
        from app.init_db import init_db
        init_db()
        
        # Start the application
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
