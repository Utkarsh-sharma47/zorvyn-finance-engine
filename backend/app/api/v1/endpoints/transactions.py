from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.api.deps import RequireAccess
from app.db.session import get_session
from app.models.finance import TransactionType
from app.models.user import Department, Role, User
from app.schemas.finance import (
    ResponseModel,
    TransactionCreate,
    TransactionListData,
    TransactionRead,
)
from app.services.finance import TransactionService


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


@router.post("/")
def create_transaction(
    request: Request,
    payload: TransactionCreate,
    session: Session = Depends(get_session),
    user: User = Depends(RequireAccess(Department.FINANCE, [Role.ADMIN])),
):
    tx = TransactionService.create_transaction(session, payload, user_id=user.id or 0)
    read = TransactionRead.model_validate(tx)
    return _json_envelope(request, success=True, data=read)


@router.get("/")
def list_transactions(
    request: Request,
    session: Session = Depends(get_session),
    _authorized: User = Depends(
        RequireAccess(Department.FINANCE, [Role.ADMIN, Role.ANALYST, Role.VIEWER]),
    ),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    category: str | None = Query(None),
    transaction_type: TransactionType | None = Query(None),
):
    rows, total = TransactionService.get_transactions(
        session,
        offset=offset,
        limit=limit,
        category=category,
        transaction_type=transaction_type,
    )
    data = TransactionListData(
        items=[TransactionRead.model_validate(r) for r in rows],
        total=total,
    )
    return _json_envelope(request, success=True, data=data)


@router.delete("/{transaction_id}")
def delete_transaction(
    request: Request,
    transaction_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(RequireAccess(Department.FINANCE, [Role.ADMIN])),
):
    TransactionService.soft_delete_transaction(session, transaction_id, deleted_by_user_id=user.id or 0)
    return _json_envelope(request, success=True, data=None)
