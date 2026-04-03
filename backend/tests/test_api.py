"""API smoke tests and patterns for future auth / ABAC."""

from datetime import datetime, timezone

from app.api.deps import get_current_user
from app.main import app
from app.models.user import Department, Role, User


def test_health_returns_envelope_200(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["error"] is None
    assert "request_id" in body and body["request_id"].startswith("req_")
    assert body["data"] == {"status": "healthy"}


def test_require_access_override_placeholder():
    """
    Example: override ``get_current_user`` (JWT dependency) with a fake user for tests
    that hit protected routes without a real token.
    """

    def viewer_from_token() -> User:
        return User(
            id=99,
            email="viewer+token@example.com",
            hashed_password="not-checked-in-tests",
            department=Department.FINANCE,
            role=Role.VIEWER,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )

    app.dependency_overrides[get_current_user] = viewer_from_token
    try:
        user = viewer_from_token()
        assert user.role is Role.VIEWER
        assert user.department is Department.FINANCE
    finally:
        app.dependency_overrides.pop(get_current_user, None)
