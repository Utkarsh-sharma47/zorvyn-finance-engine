from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import and_, func
from sqlmodel import Session, select

from app.models.finance import Account, AuditLog, Transaction, TransactionType
from app.schemas.finance import FinancialSummary, TransactionCreate, TransferCreate


class TransactionService:
    @staticmethod
    def create_transaction(
        session: Session,
        payload: TransactionCreate,
        user_id: int,
    ) -> Transaction:
        try:
            account = session.get(Account, payload.account_id)
            if account is None:
                raise HTTPException(status_code=404, detail="Account not found")

            delta = payload.amount
            if payload.transaction_type == TransactionType.EXPENSE:
                delta = -payload.amount

            new_balance = account.balance + delta
            account.balance = new_balance
            account.version = account.version + 1

            tx = Transaction(
                account_id=payload.account_id,
                user_id=user_id,
                amount=payload.amount,
                transaction_type=payload.transaction_type,
                category=payload.category,
                description=payload.description,
                is_deleted=False,
            )
            session.add(tx)
            session.commit()
            session.refresh(tx)
            session.refresh(account)
            return tx
        except HTTPException:
            session.rollback()
            raise
        except Exception:
            session.rollback()
            raise

    @staticmethod
    def transfer_funds(
        session: Session,
        payload: TransferCreate,
        user_id: int,
    ) -> tuple[Transaction, Transaction]:
        """
        Move funds between accounts in one ACID unit of work: balance updates + two ledger rows,
        single commit. Any failure rolls back the whole operation.
        """
        try:
            if payload.from_account_id == payload.to_account_id:
                raise HTTPException(status_code=400, detail="Cannot transfer to the same account")

            from_account = session.get(Account, payload.from_account_id)
            to_account = session.get(Account, payload.to_account_id)
            if from_account is None or to_account is None:
                raise HTTPException(status_code=404, detail="Account not found")

            if from_account.balance < payload.amount:
                raise HTTPException(status_code=400, detail="Insufficient funds")

            from_account.balance = from_account.balance - payload.amount
            from_account.version = from_account.version + 1
            to_account.balance = to_account.balance + payload.amount
            to_account.version = to_account.version + 1

            category = "transfer"
            tx_expense = Transaction(
                account_id=payload.from_account_id,
                user_id=user_id,
                amount=payload.amount,
                transaction_type=TransactionType.EXPENSE,
                category=category,
                description=payload.description,
                is_deleted=False,
            )
            tx_income = Transaction(
                account_id=payload.to_account_id,
                user_id=user_id,
                amount=payload.amount,
                transaction_type=TransactionType.INCOME,
                category=category,
                description=payload.description,
                is_deleted=False,
            )
            session.add(tx_expense)
            session.add(tx_income)

            session.commit()
            session.refresh(tx_expense)
            session.refresh(tx_income)
            session.refresh(from_account)
            session.refresh(to_account)
            return tx_expense, tx_income
        except HTTPException:
            session.rollback()
            raise
        except Exception:
            session.rollback()
            raise

    @staticmethod
    def get_transactions(
        session: Session,
        *,
        offset: int = 0,
        limit: int = 20,
        category: str | None = None,
        transaction_type: TransactionType | None = None,
    ) -> tuple[list[Transaction], int]:
        conditions: list = [Transaction.is_deleted == False]  # noqa: E712

        if category is not None:
            conditions.append(Transaction.category == category)
        if transaction_type is not None:
            conditions.append(Transaction.transaction_type == transaction_type)

        where = and_(*conditions)

        count_stmt = select(func.count()).select_from(Transaction).where(where)
        total = session.exec(count_stmt).one()

        list_stmt = (
            select(Transaction).where(where).order_by(Transaction.created_at.desc()).offset(offset).limit(limit)
        )
        rows = session.exec(list_stmt).all()
        return list(rows), int(total)

    @staticmethod
    def get_financial_summary(
        session: Session,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> FinancialSummary:
        conditions: list = [Transaction.is_deleted == False]  # noqa: E712
        if start_date is not None:
            conditions.append(Transaction.created_at >= start_date)
        if end_date is not None:
            conditions.append(Transaction.created_at <= end_date)
        base_where = and_(*conditions)

        sum_income_stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            and_(base_where, Transaction.transaction_type == TransactionType.INCOME),
        )
        sum_expense_stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            and_(base_where, Transaction.transaction_type == TransactionType.EXPENSE),
        )

        raw_income = session.exec(sum_income_stmt).one()
        raw_expense = session.exec(sum_expense_stmt).one()

        total_income = Decimal(str(raw_income)) if raw_income is not None else Decimal("0")
        total_expense = Decimal(str(raw_expense)) if raw_expense is not None else Decimal("0")
        net_revenue = total_income - total_expense

        return FinancialSummary(
            total_income=total_income,
            total_expense=total_expense,
            net_revenue=net_revenue,
        )

    @staticmethod
    def soft_delete_transaction(session: Session, transaction_id: int, deleted_by_user_id: int) -> None:
        try:
            tx = session.get(Transaction, transaction_id)
            if tx is None:
                raise HTTPException(status_code=404, detail="Transaction not found")
            if tx.is_deleted:
                raise HTTPException(status_code=400, detail="Transaction already deleted")

            tx.is_deleted = True
            tx.deleted_by = deleted_by_user_id
            session.add(tx)

            audit = AuditLog(
                user_id=deleted_by_user_id,
                action="DELETE",
                table_name="transactions",
                record_id=str(transaction_id),
                changes={"is_deleted": True, "deleted_by": deleted_by_user_id},
                timestamp=datetime.now(timezone.utc),
            )
            session.add(audit)
            session.commit()
        except HTTPException:
            session.rollback()
            raise
        except Exception:
            session.rollback()
            raise
