import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1.api import api_router
from app.schemas.finance import ResponseModel


def _error_envelope(request: Request, message: str, status_code: int) -> JSONResponse:
    body = ResponseModel[Any](
        success=False,
        request_id=getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:16]}"),
        data=None,
        error=message,
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(mode="json"),
    )


app = FastAPI(title="Zorvyn Finance Engine API", version="0.1.0")

# Mount versioned API first so all /api/v1/* routes are registered on this app instance.
app.include_router(api_router, prefix="/api/v1")


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    header_rid = request.headers.get("x-request-id")
    request_id = header_rid if header_rid else f"req_{uuid.uuid4().hex[:16]}"
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, str):
        msg = detail
    elif isinstance(detail, list):
        msg = "; ".join(str(item) for item in detail)
    elif isinstance(detail, dict):
        msg = detail.get("detail", str(detail))
    else:
        msg = str(detail)
    return _error_envelope(request, msg, exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    msg = "; ".join(f"{e.get('loc', ())}: {e.get('msg', '')}" for e in errors)
    return _error_envelope(request, msg, 422)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return _error_envelope(request, "An unexpected error occurred", 500)


@app.get("/health")
async def health(request: Request) -> JSONResponse:
    body = ResponseModel[dict[str, str]](
        success=True,
        request_id=request.state.request_id,
        data={"status": "healthy"},
        error=None,
    )
    return JSONResponse(
        status_code=200,
        content=body.model_dump(mode="json"),
    )
