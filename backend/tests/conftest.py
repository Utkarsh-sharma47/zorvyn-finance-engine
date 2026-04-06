"""
Pytest configuration: isolated SQLite DB and FastAPI TestClient with session override.

``DATABASE_URL`` / ``SECRET_KEY`` are set before any ``app.db.session`` import so the
module-level engine does not connect to Postgres during test collection.
"""

from __future__ import annotations

import os
import uuid

# Must run before importing app.db.session (creates engine at import time).
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-not-for-production")
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:6379/15")

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401 — register models on SQLModel.metadata (import before main)
from app.db.session import get_session
from app.models.user import Department, Role
from app.main import app as fastapi_app


@pytest.fixture
def test_db(tmp_path) -> Session:
    """
    Isolated SQLite database file per test: schema created before the test, dropped after.
    Does not use your development or production Postgres.
    """
    db_file = tmp_path / "test.db"
    url = f"sqlite:///{db_file.resolve().as_posix()}"
    engine = create_engine(url, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as sess:
        yield sess
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(test_db: Session) -> TestClient:
    """HTTP client with ``get_session`` overridden to use the test database session."""

    def override_get_session():
        yield test_db

    fastapi_app.dependency_overrides[get_session] = override_get_session
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def finance_admin(client: TestClient) -> dict:
    """
    Register a Finance/Admin user, log in, return Bearer headers and user id.
    Admin is required for POST /transactions/ and /transactions/transfer.
    """
    email = f"pytest_{uuid.uuid4().hex}@example.com"
    password = "PytestPass1!"

    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "department": Department.FINANCE.value,
            "role": Role.ADMIN.value,
        },
    )
    assert reg.status_code == 200
    reg_body = reg.json()
    assert reg_body["success"] is True
    user_id = reg_body["data"]["id"]

    login = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    return {
        "headers": {"Authorization": f"Bearer {token}"},
        "user_id": user_id,
    }


@pytest.fixture
def normal_user_token_headers(finance_admin: dict) -> dict[str, str]:
    """Backward-compatible alias: Bearer headers only."""
    return finance_admin["headers"]
