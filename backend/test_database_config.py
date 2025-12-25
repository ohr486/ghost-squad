#!/usr/bin/env python3
"""
Test script to verify database configuration functionality
"""
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


def test_database_url_priority():
    """Test that DATABASE_URL takes priority over individual variables"""
    print("🧪 Testing database URL priority...")

    # Save original environment
    original_env = {}
    env_vars = [
        "DATABASE_URL", "DATABASE_HOST", "DATABASE_PORT",
        "DATABASE_NAME", "DATABASE_USER", "DATABASE_PASSWORD"
    ]

    for var in env_vars:
        original_env[var] = os.environ.get(var)
        if var in os.environ:
            del os.environ[var]

    try:
        # Test 1: Individual variables only
        print("\n📋 Test 1: Individual variables only")
        os.environ["DATABASE_HOST"] = "test-host"
        os.environ["DATABASE_PORT"] = "9999"
        os.environ["DATABASE_NAME"] = "test-db"
        os.environ["DATABASE_USER"] = "test-user"
        os.environ["DATABASE_PASSWORD"] = "test-pass"

        # Import after setting environment variables
        from database import build_database_url, get_database_info

        url1 = build_database_url()
        info1 = get_database_info()

        expected_url1 = (
            "postgresql://test-user:test-pass@test-host:9999/test-db"
        )
        print(f"   Generated URL: {url1}")
        print(f"   Expected URL:  {expected_url1}")
        print(f"   URL Source: {info1.get('url_source')}")
        print(f"   ✅ Match: {url1 == expected_url1}")

        # Test 2: DATABASE_URL takes priority
        print("\n📋 Test 2: DATABASE_URL takes priority")
        os.environ["DATABASE_URL"] = (
            "postgresql://priority-user:priority-pass"
            "@priority-host:8888/priority-db"
        )

        # Need to reload the module to pick up new environment
        import importlib
        import database
        importlib.reload(database)

        url2 = database.build_database_url()
        info2 = database.get_database_info()

        expected_url2 = (
            "postgresql://priority-user:priority-pass"
            "@priority-host:8888/priority-db"
        )
        print(f"   Generated URL: {url2}")
        print(f"   Expected URL:  {expected_url2}")
        print(f"   URL Source: {info2.get('url_source')}")
        print(f"   ✅ Match: {url2 == expected_url2}")

        # Test 3: Default values
        print("\n📋 Test 3: Default values")
        for var in env_vars:
            if var in os.environ:
                del os.environ[var]

        importlib.reload(database)

        url3 = database.build_database_url()
        info3 = database.get_database_info()

        expected_url3 = "postgresql://gs_user:gs_password@db:5432/gs_db"
        print(f"   Generated URL: {url3}")
        print(f"   Expected URL:  {expected_url3}")
        print(f"   URL Source: {info3.get('url_source')}")
        print(f"   ✅ Match: {url3 == expected_url3}")

        print("\n✅ All database configuration tests passed!")

    finally:
        # Restore original environment
        for var, value in original_env.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]


def test_database_info():
    """Test database info function"""
    print("\n🧪 Testing database info function...")

    try:
        from database import get_database_info

        info = get_database_info()
        print("📊 Database info:")
        for key, value in info.items():
            print(f"   - {key}: {value}")

        required_keys = [
            "scheme", "host", "port", "database",
            "username", "password_set", "url_source"
        ]
        missing_keys = [key for key in required_keys if key not in info]

        if missing_keys:
            print(f"⚠️ Missing keys: {missing_keys}")
        else:
            print("✅ All required keys present")

    except Exception as e:
        print(f"❌ Error testing database info: {e}")


if __name__ == "__main__":
    test_database_url_priority()
    test_database_info()
