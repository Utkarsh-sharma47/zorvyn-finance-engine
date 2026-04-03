from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any

from sqlalchemy import JSON, Column, DateTime, Enum as SAEnum, Numeric
from sqlmodel import Field, SQLModel


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class Account(SQLModel, table=True):
    __tablename__ = "accounts"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, max_length=255)
    balance: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(19, 4), nullable=False),
    )
    version: int = Field(default=1, nullable=False)


class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"

    id: int | None = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    amount: Decimal = Field(sa_column=Column(Numeric(19, 4), nullable=False))
    # Python name avoids shadowing builtin `type`; DB column is `type` (income/expense).
    transaction_type: TransactionType = Field(
        sa_column=Column(
            "type",
            SAEnum(TransactionType, native_enum=False, length=20),
            nullable=False,
        ),
    )
    category: str = Field(index=True, max_length=128)
    description: str | None = Field(default=None, max_length=2000)
    is_deleted: bool = Field(default=False)
    deleted_by: int | None = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    action: str = Field(max_length=64)
    table_name: str = Field(max_length=128)
    record_id: str | None = Field(default=None, max_length=64)
    changes: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
