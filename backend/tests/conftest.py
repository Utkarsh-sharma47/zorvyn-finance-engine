"""
Pytest configuration: isolated SQLite DB and FastAPI TestClient with session override.

`DATABASE_URL` is set before any `app.db.session` import so the module-level engine
does not try to connect to Postgres during test collection.
"""

from __future__ import annotations

import os

# Must run before importing app.db.session (creates engine at import time).
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-not-for-production")

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401 — register models on SQLModel.metadata (import before main)
from app.db.session import get_session
# Use `fastapi_app`: `import app.models` binds name `app` to the package.
from app.main import app as fastapi_app


@pytest.fixture
def session(tmp_path) -> Session:
    """
    Isolated SQLite DB (file ``test.db`` under pytest's temp dir, same idea as ``./test.db``).
    Creates schema, yields a session, then drops tables.
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
def client(session: Session) -> TestClient:
    """HTTP client with ``get_session`` overridden to use the test SQLite session."""

    def override_get_session():
        yield session

    fastapi_app.dependency_overrides[get_session] = override_get_session
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()
