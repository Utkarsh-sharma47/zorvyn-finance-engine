from datetime import datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.finance import TransactionType

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    """Universal API envelope: success, correlation id, payload, optional error string."""

    success: bool
    request_id: str
    data: T | None = None
    error: str | None = None


class TransactionCreate(BaseModel):
    account_id: int = Field(..., gt=0)
    amount: Decimal = Field(
        ...,
        gt=0,
        max_digits=19,
        decimal_places=4,
        description="Strictly positive amount; sign applied via transaction type.",
    )
    transaction_type: TransactionType
    category: str = Field(..., min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=2000)


class TransactionUpdate(BaseModel):
    amount: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=19,
        decimal_places=4,
    )
    transaction_type: TransactionType | None = None
    category: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=2000)


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    user_id: int
    amount: Decimal
    transaction_type: TransactionType
    category: str
    description: str | None
    is_deleted: bool
    created_at: datetime


class TransactionListData(BaseModel):
    items: list[TransactionRead]
    total: int


class TransferCreate(BaseModel):
    from_account_id: int = Field(..., gt=0)
    to_account_id: int = Field(..., gt=0)
    amount: Decimal = Field(
        ...,
        gt=0,
        max_digits=19,
        decimal_places=4,
    )
    description: str = Field(..., min_length=1, max_length=2000)


class TransferResult(BaseModel):
    """Both ledger rows from a single fund transfer (expense on sender, income on receiver)."""

    expense_transaction: TransactionRead
    income_transaction: TransactionRead


class FinancialSummary(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    net_revenue: Decimal


class AccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    initial_balance: Decimal = Field(
        default=Decimal("0"),
        ge=Decimal("0"),
        max_digits=19,
        decimal_places=4,
    )

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("name must not be empty")
        return s

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, v: str) -> str:
        c = v.strip().upper()
        if len(c) != 3:
            raise ValueError("currency must be a 3-letter ISO 4217 code")
        return c


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None = None
    name: str
    currency: str
    balance: Decimal


class AccountListData(BaseModel):
    items: list[AccountRead]
    total: int
