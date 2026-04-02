import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class ResponseEnvelope(BaseModel):
    success: bool
    request_id: str = Field(..., examples=["req_8f7d9a1b2c3d4e5f"])
    data: dict[str, Any] | None = None
    error: dict[str, Any] | None = None


app = FastAPI(title="Zorvyn Finance Engine API", version="0.1.0")


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    header_rid = request.headers.get("x-request-id")
    request_id = header_rid if header_rid else f"req_{uuid.uuid4().hex[:16]}"
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response


@app.get("/health", response_model=ResponseEnvelope)
async def health(request: Request) -> JSONResponse:
    body = ResponseEnvelope(
        success=True,
        request_id=request.state.request_id,
        data={"status": "healthy"},
        error=None,
    )
    return JSONResponse(
        status_code=200,
        content=body.model_dump(mode="json"),
    )
