"""Add accounts.user_id for ownership checks.

Revision ID: 20260402_0002
Revises: 20260402_0001
Create Date: 2026-04-02

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260402_0002"
down_revision: Union[str, None] = "20260402_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("accounts") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_accounts_user_id_users",
            "users",
            ["user_id"],
            ["id"],
        )
    op.create_index(op.f("ix_accounts_user_id"), "accounts", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_accounts_user_id"), table_name="accounts")
    with op.batch_alter_table("accounts") as batch_op:
        batch_op.drop_constraint("fk_accounts_user_id_users", type_="foreignkey")
        batch_op.drop_column("user_id")
