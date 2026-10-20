import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Room

# Isolated SQLite in-memory database with StaticPool to share connection across threads
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


@pytest.fixture(scope="function")
def db_session():
    """Create fresh database tables for each test function and yield a session."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    # Pre-seed test rooms
    room1 = Room(room_number="101", category="Standard Single", rate_per_night=85.0, max_capacity=1)
    room2 = Room(room_number="201", category="Deluxe Double", rate_per_night=140.0, max_capacity=2)
    session.add_all([room1, room2])
    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session):
    """Yield a FastAPI TestClient configured to use the isolated test database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
