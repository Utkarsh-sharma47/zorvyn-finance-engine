from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

from app.api.deps import RequireAccess
from app.db.session import get_session
from app.models.finance import Account
from app.models.user import Department, Role, User
from app.schemas.finance import AccountListData, AccountRead, ResponseModel

router = APIRouter()


def _json_envelope(
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


@router.get("/")
def list_accounts(
    request: Request,
    session: Session = Depends(get_session),
    _authorized: User = Depends(
        RequireAccess(Department.FINANCE, [Role.ADMIN, Role.ANALYST, Role.VIEWER, Role.DEV_ADMIN]),
    ),
):
    stmt = select(Account).order_by(Account.id)
    rows = list(session.exec(stmt).all())
    data = AccountListData(
        items=[AccountRead.model_validate(r) for r in rows],
        total=len(rows),
    )
    return _json_envelope(request, success=True, data=data.model_dump(mode="json"))
