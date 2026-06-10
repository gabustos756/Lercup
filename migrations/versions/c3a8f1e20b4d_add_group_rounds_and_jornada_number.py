"""Add group rounds and jornada_number to matches

Revision ID: c3a8f1e20b4d
Revises: b8c4e2a1f903
Create Date: 2026-06-09 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3a8f1e20b4d"
down_revision: Union[str, None] = "b8c4e2a1f903"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "groupround",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tournament_id", sa.Integer(), nullable=False),
        sa.Column("group_label", sa.String(), nullable=False),
        sa.Column("jornada_number", sa.Integer(), nullable=False),
        sa.Column("bye_player_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["bye_player_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournament.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tournament_id", "group_label", "jornada_number",
            name="uq_tournament_group_jornada",
        ),
    )
    with op.batch_alter_table("groupround", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_groupround_group_label"), ["group_label"], unique=False)

    with op.batch_alter_table("match", schema=None) as batch_op:
        batch_op.add_column(sa.Column("jornada_number", sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("match", schema=None) as batch_op:
        batch_op.drop_column("jornada_number")

    with op.batch_alter_table("groupround", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_groupround_group_label"))

    op.drop_table("groupround")
