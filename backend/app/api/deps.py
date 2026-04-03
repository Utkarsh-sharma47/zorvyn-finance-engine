from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.core.security import decode_access_token
from app.db.session import get_session
from app.models.user import Department, Role, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Session = Depends(get_session),
) -> User:
    payload = decode_access_token(token)
    if payload is None:
        raise _credentials_exception()
    sub = payload.get("sub")
    if sub is None:
        raise _credentials_exception()
    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        raise _credentials_exception()

    user = session.get(User, user_id)
    if user is None:
        raise _credentials_exception()
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


class RequireAccess:
    """ABAC-style guard: valid JWT user must match department and allowed roles."""

    def __init__(self, expected_department: Department, allowed_roles: list[Role]):
        self.expected_department = expected_department
        self.allowed_roles = allowed_roles

    async def __call__(self, user: User = Depends(get_current_user)) -> User:
        if user.department != self.expected_department:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Department does not match required access",
            )
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Role does not match required access",
            )
        return user
