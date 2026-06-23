"""Add password reset tokens table

Revision ID: a1c4e8f92b10
Revises: f9a2b3c4d5e6
Create Date: 2026-06-18 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1c4e8f92b10"
down_revision: Union[str, None] = "f9a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "passwordresettoken",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_passwordresettoken_token_hash"),
        "passwordresettoken",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        op.f("ix_passwordresettoken_user_id"),
        "passwordresettoken",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_passwordresettoken_user_id"), table_name="passwordresettoken")
    op.drop_index(op.f("ix_passwordresettoken_token_hash"), table_name="passwordresettoken")
    op.drop_table("passwordresettoken")
