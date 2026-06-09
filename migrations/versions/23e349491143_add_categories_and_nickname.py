"""add categories and nickname

Revision ID: 23e349491143
Revises: f695e97cf8fd
Create Date: 2026-06-09 13:47:29.119461

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '23e349491143'
down_revision: Union[str, None] = 'f695e97cf8fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add category and nickname to playerprofile
    op.add_column('playerprofile', sa.Column('category', sa.String(), nullable=True))
    op.add_column('playerprofile', sa.Column('nickname', sa.String(), nullable=True))
    
    # Populate category from skill_level
    # First set default value B2
    op.execute("UPDATE playerprofile SET category = 'B2'")
    # Map old skill levels to new categories
    op.execute("UPDATE playerprofile SET category = 'D' WHERE skill_level = 'beginner'")
    op.execute("UPDATE playerprofile SET category = 'Primera' WHERE skill_level = 'advanced'")
    
    # Drop skill_level column from playerprofile
    with op.batch_alter_table('playerprofile') as batch_op:
        batch_op.drop_column('skill_level')
        
    # Add category to tournament
    op.add_column('tournament', sa.Column('category', sa.String(), nullable=True))
    op.execute("UPDATE tournament SET category = 'flexible'")


def downgrade() -> None:
    # Drop category column from tournament
    op.drop_column('tournament', 'category')
    
    # Add skill_level back to playerprofile
    op.add_column('playerprofile', sa.Column('skill_level', sa.String(), nullable=True))
    
    # Populate skill_level from category
    op.execute("UPDATE playerprofile SET skill_level = 'intermediate'")
    op.execute("UPDATE playerprofile SET skill_level = 'beginner' WHERE category = 'D'")
    op.execute("UPDATE playerprofile SET skill_level = 'advanced' WHERE category = 'Primera'")
    
    # Drop category and nickname from playerprofile
    with op.batch_alter_table('playerprofile') as batch_op:
        batch_op.drop_column('category')
        batch_op.drop_column('nickname')
