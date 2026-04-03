from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import and_, func
from sqlmodel import Session, select

from app.models.finance import Account, AuditLog, Transaction, TransactionType
from app.schemas.finance import TransactionCreate


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
