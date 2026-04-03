from datetime import datetime, timezone

from fastapi import Depends, HTTPException

from app.models.user import Department, Role, User


def get_mock_user() -> User:
    return User(
        id=1,
        email="mock@zorvyn.local",
        hashed_password="",
        department=Department.FINANCE,
        role=Role.ADMIN,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )


class RequireAccess:
    """ABAC-style guard: department must match and role must be in the allow-list."""

    def __init__(self, expected_department: Department, allowed_roles: list[Role]):
        self.expected_department = expected_department
        self.allowed_roles = allowed_roles

    async def __call__(self, user: User = Depends(get_mock_user)) -> User:
        if user.department != self.expected_department:
            raise HTTPException(
                status_code=403,
                detail="Department does not match required access",
            )
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="Role does not match required access",
            )
        return user
