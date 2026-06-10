"""Add match scheduling proposal fields

Revision ID: d4e7b2c91f05
Revises: c3a8f1e20b4d
Create Date: 2026-06-09 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e7b2c91f05"
down_revision: Union[str, None] = "b2f8a1c93e06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("match", schema=None) as batch_op:
        batch_op.add_column(sa.Column("proposed_datetime", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("proposed_by_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("location_label", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("location_url", sa.String(), nullable=True))
        batch_op.create_foreign_key(
            "fk_match_proposed_by_id_user",
            "user",
            ["proposed_by_id"],
            ["id"],
        )

def downgrade() -> None:
    with op.batch_alter_table("match", schema=None) as batch_op:
        batch_op.drop_constraint("fk_match_proposed_by_id_user", type_="foreignkey")
        batch_op.drop_column("location_url")
        batch_op.drop_column("location_label")
        batch_op.drop_column("proposed_by_id")
        batch_op.drop_column("proposed_datetime")
