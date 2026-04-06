from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.session import get_session
from app.models.user import User
from app.schemas.auth import UserPublic, UserRegister
from app.schemas.finance import ResponseModel

router = APIRouter()


def _register_envelope(
    request: Request,
    *,
    success: bool,
    data: Any = None,
    error: str | None = None,
    status_code: int = 200,
) -> JSONResponse:
    body = ResponseModel[Any](
        success=success,
        request_id=request.state.request_id,
        data=data,
        error=error,
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(mode="json"),
    )


@router.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Session = Depends(get_session),
):
    """
    OAuth2 password flow (form field `username` holds the email).
    Response is the standard OAuth2 shape so Swagger UI "Authorize" works.
    """
    statement = select(User).where(User.email == form_data.username)
    user = session.exec(statement).first()
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user account")
    if not settings.secret_key.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authentication service is not configured",
        )
    access_token = create_access_token(user_id=user.id)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register")
def register(
    request: Request,
    body: UserRegister,
    session: Session = Depends(get_session),
):
    existing = session.exec(select(User).where(User.email == body.email)).first()
    if existing is not None:
        return _register_envelope(
            request,
            success=False,
            error="Email already registered",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    user = User(
        email=body.email,
        hashed_password=get_password_hash(body.password),
        department=body.department,
        role=body.role,
        is_active=True,
    )
    session.add(user)
    try:
        session.commit()
        session.refresh(user)
    except SQLAlchemyError:
        session.rollback()
        return _register_envelope(
            request,
            success=False,
            error="Registration could not be completed",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    public = UserPublic.model_validate(user)
    return _register_envelope(request, success=True, data=public.model_dump(mode="json"))


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """
    Current user (JWT). Visible in Swagger after Authorize.
    """
    return {
        "success": True,
        "data": {
            "id": current_user.id,
            "email": current_user.email,
            "role": current_user.role,
        },
    }
