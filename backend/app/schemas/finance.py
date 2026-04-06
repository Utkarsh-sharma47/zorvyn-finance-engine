from datetime import datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

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


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None = None
    name: str
    balance: Decimal


class AccountListData(BaseModel):
    items: list[AccountRead]
    total: int
