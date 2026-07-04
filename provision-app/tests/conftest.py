import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models import ExpenseEntry, ScheduledRule

# Use a temporary SQLite file for integration tests
TEST_DATABASE_URL = "sqlite:///test_temp.db"

engine = create_engine(
    TEST_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    # Setup: Create tables in the test database
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        # Teardown: Close the session and destroy all tables
        session.close()
        try:
            Base.metadata.drop_all(bind=engine)
        except Exception:
            pass
        # Dispose engine to release all connection pool file locks
        engine.dispose()
        if os.path.exists("test_temp.db"):
            try:
                os.remove("test_temp.db")
            except Exception:
                pass

@pytest.fixture(scope="function")
def client(db):
    # Override the FastAPI db session dependency to inject our test database session
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose() # Dispose engine to clear test client connections
