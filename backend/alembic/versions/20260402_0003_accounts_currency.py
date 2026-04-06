"""Add accounts.currency (ISO 4217 code).

Revision ID: 20260402_0003
Revises: 20260402_0002
Create Date: 2026-04-02

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260402_0003"
down_revision: Union[str, None] = "20260402_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("accounts") as batch_op:
        batch_op.add_column(
            sa.Column(
                "currency",
                sa.String(length=3),
                nullable=False,
                server_default=sa.text("'USD'"),
            ),
        )


def downgrade() -> None:
    with op.batch_alter_table("accounts") as batch_op:
        batch_op.drop_column("currency")
