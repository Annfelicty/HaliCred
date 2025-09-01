#!/usr/bin/env python3
"""
HaliCred Backend Startup Script
Starts the FastAPI server with proper configuration
"""
import uvicorn
import os
from pathlib import Path

if __name__ == "__main__":
    # Set environment variables from .env file
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "true").lower() == "true"
    
    print(f"🚀 Starting HaliCred Backend Server")
    print(f"📍 Host: {host}:{port}")
    print(f"🔧 Debug Mode: {debug}")
    print(f"🌍 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if debug else "warning"
    )
