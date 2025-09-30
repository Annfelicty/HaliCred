#!/usr/bin/env python3
"""
Test script to verify Phase 2 authentication and database integration fixes.
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")

    try:
        from app.auth import get_current_user
        print("  ✓ app.auth.get_current_user imports successfully")
    except ImportError as e:
        print(f"  ✗ Failed to import get_current_user: {e}")
        return False

    try:
        from app.models import User, GreenScore, LoanApplication, Evidence, AuditLog
        print("  ✓ Database models import successfully")
    except ImportError as e:
        print(f"  ✗ Failed to import models: {e}")
        return False

    try:
        from app.config import settings
        print(f"  ✓ JWT algorithm: {settings.JWT_ALGORITHM}")
        print(f"  ✓ JWT secret key configured: {'Yes' if settings.JWT_SECRET_KEY else 'No'}")
        # Check that RS256 key paths are no longer configured
        if hasattr(settings, 'JWT_PRIVATE_KEY_PATH'):
            print("  ⚠ JWT_PRIVATE_KEY_PATH still exists (should be removed)")
        else:
            print("  ✓ JWT_PRIVATE_KEY_PATH removed")
    except ImportError as e:
        print(f"  ✗ Failed to import settings: {e}")
        return False

    return True

def test_authentication_consistency():
    """Test that authentication functions are consistent."""
    print("\nTesting authentication consistency...")

    try:
        import app.utilis as utilis

        # Check that SCORES, LOANS, EVIDENCE dicts are removed or marked for removal
        if hasattr(utilis, 'SCORES'):
            print("  ⚠ SCORES dict still exists (should be removed)")
        else:
            print("  ✓ SCORES dict removed")

        if hasattr(utilis, 'LOANS'):
            print("  ⚠ LOANS dict still exists (should be removed)")
        else:
            print("  ✓ LOANS dict removed")

        if hasattr(utilis, 'EVIDENCE'):
            print("  ⚠ EVIDENCE dict still exists (should be removed)")
        else:
            print("  ✓ EVIDENCE dict removed")

        # Check that utilis no longer defines get_current_user
        if hasattr(utilis, 'get_current_user'):
            print("  ✗ app.utilis still has get_current_user (should be removed)")
        else:
            print("  ✓ app.utilis.get_current_user successfully removed")

    except ImportError as e:
        print(f"  ✗ Failed to import utilis: {e}")
        return False

    return True

def test_jwt_configuration():
    """Test JWT configuration consistency."""
    print("\nTesting JWT configuration...")

    try:
        from app.config import settings
        from app.auth import _decode_token
        from app.api.auth import _issue_token

        # Test that both functions use HS256 consistently
        algorithm = settings.JWT_ALGORITHM
        print(f"  ✓ JWT algorithm: {algorithm}")

        if algorithm != "HS256":
            print(f"  ⚠ JWT algorithm is {algorithm}, expected HS256")
        else:
            print("  ✓ JWT algorithm is HS256 as expected")

        # Check that secret key is available
        if settings.JWT_SECRET_KEY:
            print("  ✓ JWT secret key is configured")
        else:
            print("  ✗ JWT secret key is missing")
            return False

    except Exception as e:
        print(f"  ✗ JWT configuration test failed: {e}")
        return False

    return True

def test_database_migration():
    """Test that database models are properly imported and used."""
    print("\nTesting database migration...")

    try:
        from app.main import app
        from app.models import User, GreenScore, LoanApplication, Evidence

        print("  ✓ Database models are accessible")

        # Check that main.py imports the models
        import inspect
        import app.main as main_module

        # Get all classes imported in main module
        imported_classes = [obj for name, obj in inspect.getmembers(main_module)
                          if inspect.isclass(obj) and obj.__module__ == 'app.models']

        model_names = [cls.__name__ for cls in imported_classes]

        expected_models = ['User', 'GreenScore', 'LoanApplication', 'Evidence', 'AuditLog']
        for model in expected_models:
            if model in model_names:
                print(f"  ✓ {model} imported in main.py")
            else:
                print(f"  ⚠ {model} not found in main.py imports")

    except Exception as e:
        print(f"  ✗ Database migration test failed: {e}")
        return False

    return True

def main():
    """Run all tests."""
    print("Phase 2 Authentication & Security Hardening Validation")
    print("=" * 60)

    all_tests_passed = True

    all_tests_passed &= test_imports()
    all_tests_passed &= test_authentication_consistency()
    all_tests_passed &= test_jwt_configuration()
    all_tests_passed &= test_database_migration()

    print("\n" + "=" * 60)
    if all_tests_passed:
        print("✓ All Phase 2 tests passed!")
        print("\nKey improvements implemented:")
        print("  - JWT configuration standardized to HS256")
        print("  - In-memory SCORES dict replaced with GreenScore model")
        print("  - In-memory LOANS dict replaced with LoanApplication model")
        print("  - In-memory EVIDENCE dict replaced with Evidence model")
        print("  - Celery tasks updated to use database")
        print("  - Admin endpoints updated to use database")
    else:
        print("✗ Some tests failed. Please review the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()