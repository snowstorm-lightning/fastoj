import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from backend.core.database import Base


@pytest.fixture
def db_engine():
    """Create a test database engine using SQLite in-memory."""
    engine = create_engine(
        "sqlite:///:memory:",
        poolclass=NullPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine):
    """Create a test database session."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
    }


@pytest.fixture
def sample_problem_data():
    """Sample problem data for testing."""
    return {
        "title": "Two Sum",
        "slug": "two-sum",
        "description": "Given an array of integers, return indices of the two numbers that add up to target.",
        "difficulty": "EASY",
        "time_limit": 1000,
        "memory_limit": 256,
    }


@pytest.fixture
def sample_submission_data():
    """Sample submission data for testing."""
    return {
        "problem_id": "test-problem-id",
        "code": "print('Hello World')",
        "language": "python",
    }
