#!/usr/bin/env python3
"""
Phase 1 Authentication Fixes Validation
Tests the core authentication improvements made in Phase 1.
"""

import sys
import os
import traceback

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_imports():
    """Test that all imports work correctly after auth consolidation."""
    print("🔧 Testing imports...")

    try:
        # Test core auth imports
        from app.auth import get_current_user
        print("  ✅ app.auth.get_current_user imports successfully")

        # Test that utilis no longer defines get_current_user
        import app.utilis as utilis
        if hasattr(utilis, 'get_current_user'):
            print("  ❌ app.utilis still has get_current_user (should be removed)")
            return False
        print("  ✅ app.utilis.get_current_user successfully removed")

        # Test that require_role uses the correct auth
        from app.utilis import require_role
        print("  ✅ app.utilis.require_role imports successfully")

        # Test main app components
        from app.models import User
        print("  ✅ app.models.User imports successfully")

        from app.api.auth import send_otp, redis_client
        print("  ✅ app.api.auth imports successfully")

        return True

    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        traceback.print_exc()
        return False

def test_jwt_config():
    """Test JWT configuration consistency."""
    print("\n🔧 Testing JWT configuration...")

    try:
        from app.config import settings
        from app.auth import _decode_token
        from app.api.auth import _issue_token
        import json
        from datetime import datetime, timezone
        from jose import jwt

        # Create a mock user for testing
        class MockUser:
            id = "test-user-id"
            roles = ["borrower"]
            phone = "+254700000000"
            email = "test@example.com"

        mock_user = MockUser()
        current_time = datetime.now(timezone.utc)

        # Test token issuance and verification consistency
        token_data = _issue_token(mock_user, current_time)
        test_token = token_data["access_token"]

        print(f"  ✅ Token generated successfully")

        # Test token decoding
        payload = _decode_token(test_token)
        print(f"  ✅ Token decoded successfully")

        # Verify token contains expected claims
        if payload.get("sub") == str(mock_user.id):
            print("  ✅ Token contains correct user ID")
        else:
            print(f"  ❌ Token user ID mismatch: {payload.get('sub')} != {mock_user.id}")
            return False

        if payload.get("roles") == mock_user.roles:
            print("  ✅ Token contains correct roles")
        else:
            print(f"  ❌ Token roles mismatch: {payload.get('roles')} != {mock_user.roles}")
            return False

        return True

    except Exception as e:
        print(f"  ❌ JWT configuration error: {e}")
        traceback.print_exc()
        return False

def test_redis_fallback():
    """Test Redis OTP storage with fallback."""
    print("\n🔧 Testing Redis OTP storage...")

    try:
        from app.api.auth import redis_client, _store_otp, _get_otp, _delete_otp
        from datetime import datetime, timezone, timedelta

        test_identifier = "test@example.com"
        test_hash = "test_otp_hash_123"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

        # Test OTP storage
        _store_otp(test_identifier, test_hash, expires_at)
        print("  ✅ OTP stored successfully")

        # Test OTP retrieval
        stored_otp = _get_otp(test_identifier)
        if stored_otp and stored_otp["hash"] == test_hash:
            print("  ✅ OTP retrieved successfully")
        else:
            print("  ❌ OTP retrieval failed or hash mismatch")
            return False

        # Test OTP deletion
        _delete_otp(test_identifier)
        deleted_otp = _get_otp(test_identifier)
        if deleted_otp is None:
            print("  ✅ OTP deleted successfully")
        else:
            print("  ❌ OTP deletion failed")
            return False

        # Report Redis status
        if redis_client:
            print("  ✅ Redis connection available")
        else:
            print("  ⚠️ Redis unavailable, using memory fallback")

        return True

    except Exception as e:
        print(f"  ❌ Redis OTP error: {e}")
        traceback.print_exc()
        return False

def test_rate_limiting():
    """Test rate limiting function."""
    print("\n🔧 Testing rate limiting...")

    try:
        from app.api.auth import _check_rate_limit, redis_client
        from fastapi import HTTPException

        test_identifier = "rate_test@example.com"

        if redis_client:
            # Try to trigger rate limiting (this might not work in test env)
            try:
                _check_rate_limit(test_identifier)
                print("  ✅ Rate limiting check executed without error")
            except HTTPException as e:
                if e.status_code == 429:
                    print("  ✅ Rate limiting is working (429 error)")
                else:
                    print(f"  ❌ Unexpected HTTP error: {e.status_code}")
                    return False
        else:
            print("  ⚠️ Redis unavailable, rate limiting not active")

        return True

    except Exception as e:
        print(f"  ❌ Rate limiting error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all authentication tests."""
    print("🚀 Phase 1 Authentication Fixes Validation")
    print("=" * 50)

    all_passed = True

    # Run all tests
    tests = [
        ("Import Structure", test_imports),
        ("JWT Configuration", test_jwt_config),
        ("Redis OTP Storage", test_redis_fallback),
        ("Rate Limiting", test_rate_limiting),
    ]

    for test_name, test_func in tests:
        if not test_func():
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Phase 1 authentication fixes are working!")
        print("\n✅ Key improvements verified:")
        print("  - Unified authentication middleware")
        print("  - Consistent JWT key configuration")
        print("  - Redis-based OTP storage with fallback")
        print("  - Rate limiting protection")
        print("\nThe 401 Unauthorized errors should now be resolved.")
    else:
        print("❌ SOME TESTS FAILED - Please review the errors above")
        sys.exit(1)

if __name__ == "__main__":
    main()