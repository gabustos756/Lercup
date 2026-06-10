"""Add match_status to match

Revision ID: b2f8a1c93e06
Revises: c3a8f1e20b4d
Create Date: 2026-06-10 14:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2f8a1c93e06"
down_revision: Union[str, None] = "c3a8f1e20b4d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("match", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("match_status", sa.String(), nullable=False, server_default="pending")
        )

    op.execute('UPDATE "match" SET match_status = \'played\' WHERE winner_id IS NOT NULL')
    op.execute('UPDATE "match" SET match_status = \'pending\' WHERE winner_id IS NULL')


def downgrade() -> None:
    with op.batch_alter_table("match", schema=None) as batch_op:
        batch_op.drop_column("match_status")
