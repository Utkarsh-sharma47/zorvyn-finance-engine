from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import and_, func
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select
from app.services.audit import AuditService
from app.models.finance import Account, Transaction, TransactionType
from app.schemas.finance import FinancialSummary, TransactionCreate, TransferCreate



class TransactionService:
    @staticmethod
    def _assert_account_owned(session: Session, account_id: int, user_id: int) -> Account:
        """Ensure account exists and belongs to user_id (single round-trip)."""
        stmt = select(Account).where(Account.id == account_id, Account.user_id == user_id)
        account = session.exec(stmt).first()
        if account is None:
            raise HTTPException(
                status_code=404,
                detail="Account not found or access denied",
            )
        return account

    @staticmethod
    def create_transaction(
        session: Session,
        payload: TransactionCreate,
        user_id: int,
    ) -> Transaction:
        try:
            account = TransactionService._assert_account_owned(session, payload.account_id, user_id)

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
            session.flush()
            if tx.id is None:
                raise HTTPException(status_code=400, detail="Failed to persist transaction for audit")
            AuditService.log_action(
                session,
                user_id=user_id,
                action="INSERT",
                table_name="transactions",
                record_id=tx.id,
                changes={
                    "account_id": payload.account_id,
                    "amount": str(payload.amount),
                    "transaction_type": payload.transaction_type.value,
                    "category": payload.category,
                    "description": payload.description,
                    "user_id": user_id,
                },
            )
            session.commit()
            session.refresh(tx)
            session.refresh(account)
            return tx
        except HTTPException:
            session.rollback()
            raise
        except Exception:
            session.rollback()
            raise HTTPException(status_code=400, detail="Unable to complete the transaction")

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

            from_account = TransactionService._assert_account_owned(session, payload.from_account_id, user_id)
            to_account = TransactionService._assert_account_owned(session, payload.to_account_id, user_id)

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
            raise HTTPException(status_code=400, detail="Unable to complete the transfer")

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
    def _find_transfer_counterpart(session: Session, tx: Transaction) -> Transaction | None:
        """
        Transfer pairs are two rows (expense + income) with no FK. When deleting one leg,
        match the twin: category 'transfer', same user, same amount magnitude, created_at
        within 1 second of this row.
        """
        if (tx.category or "").strip().lower() != "transfer":
            return None
        window_start = tx.created_at - timedelta(seconds=1)
        window_end = tx.created_at + timedelta(seconds=1)
        abs_amount = abs(tx.amount)
        stmt = (
            select(Transaction)
            .where(
                Transaction.id != tx.id,
                Transaction.user_id == tx.user_id,
                Transaction.category == tx.category,
                Transaction.is_deleted == False,  # noqa: E712
                Transaction.created_at >= window_start,
                Transaction.created_at <= window_end,
                func.abs(Transaction.amount) == abs_amount,
            )
            .order_by(Transaction.id.asc())
            .limit(1)
        )
        return session.exec(stmt).first()

    @staticmethod
    def soft_delete_transaction(session: Session, transaction_id: int, deleted_by_user_id: int) -> None:
        try:
            tx = session.get(Transaction, transaction_id)
            if tx is None:
                raise HTTPException(status_code=404, detail="Transaction not found")
            if tx.user_id != deleted_by_user_id:
                raise HTTPException(status_code=403, detail="Not allowed to delete this transaction")
            if tx.is_deleted:
                raise HTTPException(status_code=400, detail="Transaction already deleted")

            to_soft_delete: list[Transaction] = [tx]
            counterpart = TransactionService._find_transfer_counterpart(session, tx)
            if counterpart is not None:
                to_soft_delete.append(counterpart)

            for row in to_soft_delete:
                row.is_deleted = True
                row.deleted_by = deleted_by_user_id
                session.add(row)

            session.flush()
            for row in to_soft_delete:
                if row.id is None:
                    raise HTTPException(status_code=400, detail="Failed to persist transaction delete for audit")
                AuditService.log_action(
                    session,
                    user_id=deleted_by_user_id,
                    action="DELETE",
                    table_name="transactions",
                    record_id=row.id,
                    changes={
                        "is_deleted": True,
                        "deleted_by": deleted_by_user_id,
                        "paired_transfer_delete": len(to_soft_delete) > 1,
                    },
                )
            session.commit()
        except HTTPException:
            session.rollback()
            raise
        except SQLAlchemyError as exc:
            session.rollback()
            raise HTTPException(status_code=400, detail="Unable to delete the transaction") from exc
        except Exception:
            session.rollback()
            raise HTTPException(status_code=400, detail="Unable to delete the transaction")
