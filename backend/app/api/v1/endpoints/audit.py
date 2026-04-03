from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.api.deps import RequireAccess
from app.db.session import get_session
from app.models.user import Department, Role, User
from app.schemas.audit import AuditLogListData, AuditLogRead
from app.schemas.finance import ResponseModel
from app.services.audit import AuditService

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
def list_audit_logs(
    request: Request,
    session: Session = Depends(get_session),
    _authorized: User = Depends(
        RequireAccess(Department.FINANCE, [Role.ADMIN, Role.DEV_ADMIN]),
    ),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    rows, total = AuditService.list_audit_logs(session, offset=offset, limit=limit)
    data = AuditLogListData(
        items=[AuditLogRead.model_validate(r) for r in rows],
        total=total,
    )
    return _json_envelope(request, success=True, data=data.model_dump(mode="json"))
