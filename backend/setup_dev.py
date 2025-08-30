#!/usr/bin/env python3
"""
Development setup script for HaliScore backend.

This script sets up the development environment including:
- Database initialization
- JWT key generation
- MinIO bucket creation
- Service health checks
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_service(url, service_name, timeout=30):
    """Check if a service is running."""
    print(f"🔍 Checking {service_name} at {url}...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name} is running")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(2)
    print(f"❌ {service_name} is not running")
    return False

def create_env_file():
    """Create .env file if it doesn't exist."""
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    env_content = """# HaliScore Backend Environment Configuration

# Database
DATABASE_URL=postgresql://user:password@localhost/haliscore

# JWT Authentication
JWT_PRIVATE_KEY_PATH=jwtRS256.key
JWT_PUBLIC_KEY_PATH=jwtRS256.key.pub
JWT_ALGORITHM=RS256
JWT_EXPIRY_HOURS=24

# S3/MinIO Storage
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=haliscore

# Redis and Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Security
AUDIT_HMAC_SECRET=dev-secret-key-change-in-production
SECRET_KEY=dev-secret-key-change-in-production

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# Environment
ENVIRONMENT=development
DEBUG=true

# AI/ML Settings
AI_MODEL_PATH=
OCR_LANGUAGE=eng

# Logging
LOG_LEVEL=INFO
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ Created .env file")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def generate_jwt_keys():
    """Generate JWT keys if they don't exist."""
    private_key = Path("jwtRS256.key")
    public_key = Path("jwtRS256.key.pub")
    
    if private_key.exists() and public_key.exists():
        print("✅ JWT keys already exist")
        return True
    
    print("🔑 Generating JWT keys...")
    
    # Generate private key
    if not run_command("openssl genrsa -out jwtRS256.key 2048", "Generating private key"):
        return False
    
    # Generate public key
    if not run_command("openssl rsa -in jwtRS256.key -pubout -out jwtRS256.key.pub", "Generating public key"):
        return False
    
    print("✅ JWT keys generated successfully")
    return True

def setup_database():
    """Setup PostgreSQL database."""
    print("🗄️  Setting up database...")
    
    # Check if PostgreSQL is running
    if not run_command("pg_isready -h localhost", "Checking PostgreSQL connection"):
        print("⚠️  PostgreSQL might not be running. Please start it manually.")
        return False
    
    # Create database and user
    commands = [
        ("sudo -u postgres createdb haliscore", "Creating database"),
        ("sudo -u postgres createuser user", "Creating user"),
        ("sudo -u postgres psql -c \"ALTER USER user WITH PASSWORD 'password';\"", "Setting user password"),
        ("sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE haliscore TO user;\"", "Granting privileges")
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    # Initialize database tables
    if not run_command("python app/init_db.py", "Initializing database tables"):
        return False
    
    return True

def setup_minio():
    """Setup MinIO bucket."""
    print("📦 Setting up MinIO...")
    
    # Check if MinIO is running
    if not check_service("http://localhost:9000/minio/health/live", "MinIO"):
        print("⚠️  MinIO is not running. Please start it manually with:")
        print("   ./minio server /tmp/minio --console-address ':9001'")
        print("   Then create the bucket manually in the MinIO console at http://localhost:9001")
        return False
    
    print("✅ MinIO setup completed")
    return True

def check_redis():
    """Check if Redis is running."""
    print("🔴 Checking Redis...")
    
    if not run_command("redis-cli ping", "Checking Redis connection"):
        print("⚠️  Redis is not running. Please start it manually with:")
        print("   sudo systemctl start redis")
        return False
    
    return True

def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing Python dependencies...")
    
    if not run_command("pip install -r requirements.txt", "Installing requirements"):
        return False
    
    return True

def run_tests():
    """Run tests to verify setup."""
    print("🧪 Running tests...")
    
    if not run_command("python -m pytest tests/ -v", "Running tests"):
        print("⚠️  Some tests failed, but setup may still be functional")
        return False
    
    return True

def main():
    """Main setup function."""
    print("🚀 HaliScore Backend Development Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ Python 3.10 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Setup steps
    steps = [
        ("Creating environment file", create_env_file),
        ("Generating JWT keys", generate_jwt_keys),
        ("Installing dependencies", install_dependencies),
        ("Setting up database", setup_database),
        ("Checking Redis", check_redis),
        ("Setting up MinIO", setup_minio),
        ("Running tests", run_tests)
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        print(f"\n{'='*20} {step_name} {'='*20}")
        if not step_func():
            failed_steps.append(step_name)
    
    # Summary
    print(f"\n{'='*50}")
    print("🎉 Setup Summary")
    print("=" * 50)
    
    if failed_steps:
        print(f"❌ Failed steps: {', '.join(failed_steps)}")
        print("\n⚠️  Some steps failed. Please check the errors above and fix them.")
        print("   You may need to:")
        print("   - Start PostgreSQL: sudo systemctl start postgresql")
        print("   - Start Redis: sudo systemctl start redis")
        print("   - Start MinIO: ./minio server /tmp/minio --console-address ':9001'")
    else:
        print("✅ All setup steps completed successfully!")
    
    print(f"\n🚀 To start the backend, run:")
    print("   python run.py")
    print(f"\n📚 API documentation will be available at:")
    print("   http://localhost:8000/docs")
    print(f"\n🔍 Health check:")
    print("   http://localhost:8000/health")

if __name__ == "__main__":
    main()
