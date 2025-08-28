"""
Setup script for installing dependencies and setting up the environment
"""
import os
import subprocess
import sys

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("Python 3.8 or higher is required")
        sys.exit(1)

def install_requirements():
    """Install requirements in the correct order"""
    try:
        # Upgrade pip first
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Install base requirements first
        print("Installing base requirements...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements-base.txt"])
        
        # Try to install geo-mapping requirements
        print("Installing geo-mapping requirements...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "-r", "app/geo-mapping/requirements.txt"
            ])
        except subprocess.CalledProcessError:
            print("""
Warning: Some geo-mapping dependencies could not be installed.
This might be because you don't have C++ build tools installed.
You can still use the basic functionality, but some features will be limited.

To install all features:
1. Install Microsoft C++ Build Tools from:
   https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Run this script again
""")
        
        print("\nSetup completed successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"Error during installation: {e}")
        sys.exit(1)

def setup_development_environment():
    """Setup development environment"""
    try:
        # Create necessary directories if they don't exist
        os.makedirs("app/geo-mapping", exist_ok=True)
        
        # Initialize environment variables if needed
        if not os.path.exists(".env"):
            with open(".env", "w") as f:
                f.write("""# Add your environment variables here
GOOGLE_CLOUD_PROJECT_ID=
GOOGLE_EARTH_ENGINE_PRIVATE_KEY=
GOOGLE_EARTH_ENGINE_CLIENT_EMAIL=
""")
            print("Created .env file - please add your credentials")
        
    except Exception as e:
        print(f"Error setting up development environment: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("Setting up HaliCred development environment...")
    check_python_version()
    setup_development_environment()
    install_requirements()
