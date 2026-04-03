from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.session import get_session
from app.models.user import User
from app.schemas.auth import UserPublic, UserRegister
from app.schemas.finance import ResponseModel

router = APIRouter()


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
        raise HTTPException(status_code=500, detail="Invalid user state")
    access_token = create_access_token(user_id=user.id)
    return {"access_token": access_token, "token_type": "bearer"}


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
    session.commit()
    session.refresh(user)
    public = UserPublic.model_validate(user)
    return _register_envelope(request, success=True, data=public.model_dump(mode="json"))
