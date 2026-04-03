from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SAEnum
from sqlmodel import Field, SQLModel


class Department(str, Enum):
    FINANCE = "Finance"
    ENGINEERING = "Engineering"


class Role(str, Enum):
    ADMIN = "Admin"
    ANALYST = "Analyst"
    VIEWER = "Viewer"
    DEV_ADMIN = "Dev_Admin"
    DEV_EMPLOYEE = "Dev_Employee"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=320)
    hashed_password: str = Field(max_length=255)
    department: Department = Field(
        sa_column=Column(SAEnum(Department, native_enum=False, length=50), nullable=False),
    )
    role: Role = Field(
        sa_column=Column(SAEnum(Role, native_enum=False, length=50), nullable=False),
    )
    is_active: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
