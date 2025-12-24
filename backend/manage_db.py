#!/usr/bin/env python3
"""
Database management script for Alembic operations and seeding
"""
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from database import check_database_connection, create_tables, drop_tables
from seed_data import seed_data, clear_data


def wait_for_db(max_attempts: int = 30, delay: int = 1):
    """Wait for database to be ready"""
    import time
    
    print("⏳ Waiting for database to be ready...")
    
    for attempt in range(max_attempts):
        if check_database_connection():
            print("✅ Database is ready!")
            return True
        
        print(f"   Attempt {attempt + 1}/{max_attempts} - Database not ready, waiting {delay}s...")
        time.sleep(delay)
    
    print("❌ Database connection timeout!")
    return False


def init_db():
    """Initialize database with tables"""
    print("🗄️  Initializing database...")
    
    if not wait_for_db():
        sys.exit(1)
    
    try:
        create_tables()
        print("✅ Database tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        sys.exit(1)


def reset_db():
    """Reset database by dropping and recreating tables"""
    print("🔄 Resetting database...")
    
    if not wait_for_db():
        sys.exit(1)
    
    try:
        drop_tables()
        print("🗑️  Dropped all tables")
        
        create_tables()
        print("🏗️  Recreated all tables")
        
        print("✅ Database reset completed!")
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        sys.exit(1)


def seed_db():
    """Seed database with sample data"""
    print("🌱 Seeding database...")
    
    if not wait_for_db():
        sys.exit(1)
    
    try:
        seed_data()
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        sys.exit(1)


def clear_db():
    """Clear all data from database"""
    print("🧹 Clearing database data...")
    
    if not wait_for_db():
        sys.exit(1)
    
    try:
        clear_data()
    except Exception as e:
        print(f"❌ Error clearing database: {e}")
        sys.exit(1)


def check_db():
    """Check database connection and status"""
    print("🔍 Checking database status...")
    
    # Check connection
    if check_database_connection():
        print("✅ Database connection: OK")
    else:
        print("❌ Database connection: FAILED")
        sys.exit(1)
    
    # Check if tables exist
    try:
        from database import engine
        from sqlalchemy import inspect
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if tables:
            print(f"📊 Found {len(tables)} tables:")
            for table in sorted(tables):
                print(f"   - {table}")
        else:
            print("ℹ️  No tables found in database")
            
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        sys.exit(1)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python manage_db.py <command>")
        print("Commands:")
        print("  init     - Initialize database with tables")
        print("  reset    - Reset database (drop and recreate tables)")
        print("  seed     - Seed database with sample data")
        print("  clear    - Clear all data from database")
        print("  check    - Check database connection and status")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "init":
        init_db()
    elif command == "reset":
        reset_db()
    elif command == "seed":
        seed_db()
    elif command == "clear":
        clear_db()
    elif command == "check":
        check_db()
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()