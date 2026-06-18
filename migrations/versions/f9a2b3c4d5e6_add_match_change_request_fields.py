"""Add match change request fields

Revision ID: f9a2b3c4d5e6
Revises: e8f3a2b71c04
Create Date: 2026-06-17 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f9a2b3c4d5e6"
down_revision: Union[str, None] = "e8f3a2b71c04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("match", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("is_change_request", sa.Boolean(), nullable=False, server_default="0")
        )
        batch_op.add_column(sa.Column("proposed_location_label", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("proposed_location_url", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("match", schema=None) as batch_op:
        batch_op.drop_column("proposed_location_url")
        batch_op.drop_column("proposed_location_label")
        batch_op.drop_column("is_change_request")
