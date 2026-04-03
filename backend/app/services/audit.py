from datetime import datetime, timezone

from sqlalchemy import func
from sqlmodel import Session, select

from app.models.finance import AuditLog


class AuditService:
    @staticmethod
    def log_action(
        session: Session,
        user_id: int,
        action: str,
        table_name: str,
        record_id: int,
        changes: dict,
    ) -> AuditLog:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            table_name=table_name,
            record_id=str(record_id),
            changes=changes,
            timestamp=datetime.now(timezone.utc),
        )
        session.add(entry)
        return entry

    @staticmethod
    def list_audit_logs(
        session: Session,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[AuditLog], int]:
        count_stmt = select(func.count()).select_from(AuditLog)
        total = session.exec(count_stmt).one()

        list_stmt = (
            select(AuditLog).order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit)
        )
        rows = session.exec(list_stmt).all()
        return list(rows), int(total)
