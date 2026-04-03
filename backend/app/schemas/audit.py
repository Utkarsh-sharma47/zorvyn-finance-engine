from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    action: str
    table_name: str
    record_id: str | None
    changes: dict[str, Any] | None
    timestamp: datetime


class AuditLogListData(BaseModel):
    items: list[AuditLogRead]
    total: int
