from fastapi import APIRouter

from app.api.v1.endpoints.audit import router as audit_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.transactions import router as transactions_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(audit_router, prefix="/audit", tags=["audit"])
api_router.include_router(
    transactions_router,
    prefix="/transactions",
    tags=["transactions"],
)
