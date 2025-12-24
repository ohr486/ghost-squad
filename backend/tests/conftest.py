"""
Pytest configuration and fixtures for database seeding tests
"""
import os

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database.base import Base


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine using SQLite"""
    # Use SQLite in-memory database for testing
    engine = create_engine(
        "sqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False,
    )

    # Enable foreign key constraints for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create all tables
    Base.metadata.create_all(engine)

    yield engine

    # Cleanup
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def test_session(test_engine):
    """Create a test database session"""
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSessionLocal()

    yield session

    # Cleanup after each test
    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def clean_database(test_session):
    """Ensure database is clean before each test"""
    # Clear all tables in correct order (respecting foreign key constraints)
    try:
        # Delete in reverse order of dependencies
        test_session.execute(text("DELETE FROM stories"))
        test_session.execute(text("DELETE FROM inquiries"))
        test_session.execute(text("DELETE FROM story_templates"))

        # Reset SQLite autoincrement sequences
        test_session.execute(
            text(
                "DELETE FROM sqlite_sequence WHERE name IN "
                "('stories', 'inquiries', 'story_templates')"
            )
        )

        test_session.commit()
    except Exception:
        # If direct SQL fails, use ORM approach
        from models.database.inquiry import InquiryModel
        from models.database.story import StoryModel
        from models.database.template import StoryTemplateModel

        test_session.query(StoryModel).delete()
        test_session.query(InquiryModel).delete()
        test_session.query(StoryTemplateModel).delete()
        test_session.commit()

    yield test_session


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing"""
    original_env = os.environ.copy()

    # Set test environment variables
    test_env = {"DATABASE_URL": "sqlite:///:memory:", "ENVIRONMENT": "test"}

    os.environ.update(test_env)

    yield test_env

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
