import os
os.environ["DISABLE_SQLALCHEMY_CEXT"] = "1"
os.environ["LLM_PROVIDER"] = "mock"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
import app.database as database_module
from app.main import app

# StaticPool ensures all connections share the same in-memory SQLite database
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    database_module.SessionLocal = TestingSessionLocal

    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def sample_transcript_segments():
    return [
        {
            "start_time": 0.0,
            "end_time": 14.5,
            "speaker": "Speaker 1",
            "text": "Good morning everyone. Today we are reviewing the Q3 cloud infrastructure deliverables."
        },
        {
            "start_time": 15.0,
            "end_time": 28.0,
            "speaker": "Speaker 2",
            "text": "We finalized the choice of PostgreSQL as our primary transactional database."
        },
        {
            "start_time": 29.0,
            "end_time": 44.0,
            "speaker": "Speaker 1",
            "text": "Excellent. Sarah will prepare the data migration script by Friday."
        },
        {
            "start_time": 45.0,
            "end_time": 58.0,
            "speaker": "Speaker 2",
            "text": "Should we also migrate the legacy audit logs or archive them to S3?"
        }
    ]
