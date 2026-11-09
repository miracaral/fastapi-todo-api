import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("DATABASE_URL", "sqlite://")

from database import Base, get_db  # noqa: E402
from main import app  # noqa: E402

# One in-memory database per test, so tests never share state.
@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def register(client, username, password="correct-horse-1", **extra):
    body = {"username": username, "email": f"{username}@example.com", "first_name": "Test",
            "last_name": "User", "password": password, **extra}
    return client.post("/auth/", json=body)


def login(client, username, password="correct-horse-1"):
    r = client.post("/auth/token", data={"username": username, "password": password})
    return r


def auth_header(client, username):
    register(client, username)
    token = login(client, username).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
