import sys
import os
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database import Base, get_db

# Separate SQLite file just for tests - never touches your real consentx.db
TEST_DB_URL = "sqlite:///./test_consentx.db"
engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # keeps one connection alive for the whole run, avoids Windows file-lock issues
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Creates all tables once before the test session, drops the file after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()  # closes all connections so Windows will let us delete the file
    if os.path.exists("test_consentx.db"):
        os.remove("test_consentx.db")


@pytest.fixture
def client():
    return TestClient(app)


def register_and_login(client, role, password="test123"):
    """Registers a user with a unique email + given role, returns (user_id, auth_headers)."""
    unique_email = f"{role}_{uuid.uuid4().hex[:8]}@example.com"
    reg = client.post("/auth/register", json={
        "name": "Test User",
        "email": unique_email,
        "password": password,
        "role": role,
    })
    assert reg.status_code == 200, reg.text
    user_id = reg.json()["user_id"]

    login = client.post("/auth/login", json={"email": unique_email, "password": password})
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]

    return user_id, {"Authorization": f"Bearer {token}"}


@pytest.fixture
def principal(client):
    user_id, headers = register_and_login(client, "data_principal")
    return {"user_id": user_id, "headers": headers}


@pytest.fixture
def fiduciary(client):
    user_id, headers = register_and_login(client, "data_fiduciary")
    return {"user_id": user_id, "headers": headers}