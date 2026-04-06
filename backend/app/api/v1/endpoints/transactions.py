from datetime import datetime
from typing import Any, Callable, Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from fastapi_cache.decorator import cache
from sqlmodel import Session
from starlette.responses import Response

from app.api.deps import RequireAccess
from app.db.session import get_session
from app.models.finance import TransactionType
from app.models.user import Department, Role, User
from app.schemas.finance import (
    FinancialSummary,
    ResponseModel,
    TransactionCreate,
    TransactionListData,
    TransactionRead,
    TransferCreate,
    TransferResult,
)
from app.services.finance import TransactionService


router = APIRouter()


def financial_summary_key_builder(
    func: Callable[..., Any],
    namespace: str = "",
    *,
    request: Optional[Request] = None,
    response: Optional[Response] = None,
    args: tuple[Any, ...] = (),
    kwargs: Optional[dict[str, Any]] = None,
) -> str:
    kwargs = kwargs or {}
    user = kwargs.get("_authorized")
    uid = getattr(user, "id", None) if user is not None else "anon"
    dept = getattr(user, "department", None)
    role = getattr(user, "role", None)
    dept_s = dept.value if dept is not None else ""
    role_s = role.value if role is not None else ""
    start_date = kwargs.get("start_date")
    end_date = kwargs.get("end_date")
    start_s = start_date.isoformat() if start_date else ""
    end_s = end_date.isoformat() if end_date else ""
    return (
        f"{namespace}:{func.__module__}:{func.__name__}:"
        f"uid:{uid}:dept:{dept_s}:role:{role_s}:start:{start_s}:end:{end_s}"
    )


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


@router.post("/transfer")
def transfer_funds(
    request: Request,
    payload: TransferCreate,
    session: Session = Depends(get_session),
    user: User = Depends(RequireAccess(Department.FINANCE, [Role.ADMIN])),
):
    expense_tx, income_tx = TransactionService.transfer_funds(
        session,
        payload,
        user_id=user.id or 0,
    )
    data = TransferResult(
        expense_transaction=TransactionRead.model_validate(expense_tx),
        income_transaction=TransactionRead.model_validate(income_tx),
    )
    return _json_envelope(request, success=True, data=data.model_dump(mode="json"))


@router.get("/summary")
@cache(expire=300, key_builder=financial_summary_key_builder)
async def financial_summary(
    request: Request,
    session: Session = Depends(get_session),
    _authorized: User = Depends(
        RequireAccess(Department.FINANCE, [Role.ADMIN, Role.ANALYST, Role.VIEWER, Role.DEV_ADMIN]),
    ),
    start_date: datetime | None = Query(None, description="Inclusive lower bound on created_at (UTC)"),
    end_date: datetime | None = Query(None, description="Inclusive upper bound on created_at (UTC)"),
):
    summary: FinancialSummary = TransactionService.get_financial_summary(
        session,
        start_date=start_date,
        end_date=end_date,
    )
    return _json_envelope(request, success=True, data=summary.model_dump(mode="json"))


@router.get("/")
def list_transactions(
    request: Request,
    session: Session = Depends(get_session),
    _authorized: User = Depends(
        RequireAccess(Department.FINANCE, [Role.ADMIN, Role.ANALYST, Role.VIEWER, Role.DEV_ADMIN]),
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
    """
    Soft-delete a ledger row owned by the current user. Transfer pairs (category `transfer`
    with matching twin within 1s) are soft-deleted together in the service layer.
    """
    TransactionService.soft_delete_transaction(session, transaction_id, deleted_by_user_id=user.id or 0)
    return _json_envelope(request, success=True, data=None)
