"""
Database connection and session management
"""
import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from models.database.base import Base


def build_database_url() -> str:
    """
    Build database URL from environment variables.
    
    Priority:
    1. DATABASE_URL (if provided, use as-is)
    2. Individual DATABASE_* variables (build connection string)
    3. Default development values
    
    Returns:
        str: Database connection URL
    """
    # First priority: Use DATABASE_URL if provided
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    
    # Second priority: Build from individual environment variables
    host = os.getenv("DATABASE_HOST", "db")
    port = os.getenv("DATABASE_PORT", "5432")
    name = os.getenv("DATABASE_NAME", "gs_db")
    user = os.getenv("DATABASE_USER", "gs_user")
    password = os.getenv("DATABASE_PASSWORD", "gs_password")
    
    # Build PostgreSQL connection string
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


# Database URL from environment variables
DATABASE_URL = build_database_url()

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,    # Recycle connections every 5 minutes
    echo=os.getenv("DATABASE_ECHO", "false").lower() == "true"  # Log SQL queries if enabled
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    Used with FastAPI dependency injection.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Create all tables in the database.
    This is used for initial setup and testing.
    """
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """
    Drop all tables in the database.
    This is used for testing and database reset.
    """
    Base.metadata.drop_all(bind=engine)


def check_database_connection() -> bool:
    """
    Check if database connection is working.
    Returns True if connection is successful, False otherwise.
    """
    try:
        with engine.connect() as connection:
            from sqlalchemy import text
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def get_database_info() -> dict:
    """
    Get database connection information for debugging.
    
    Returns:
        dict: Database connection details (without sensitive information)
    """
    # Parse the DATABASE_URL to extract components
    import urllib.parse
    
    try:
        parsed = urllib.parse.urlparse(DATABASE_URL)
        return {
            "scheme": parsed.scheme,
            "host": parsed.hostname,
            "port": parsed.port,
            "database": parsed.path.lstrip('/') if parsed.path else None,
            "username": parsed.username,
            "password_set": bool(parsed.password),  # Don't expose actual password
            "url_source": "DATABASE_URL" if os.getenv("DATABASE_URL") else "individual_variables"
        }
    except Exception as e:
        return {"error": str(e), "raw_url_length": len(DATABASE_URL)}