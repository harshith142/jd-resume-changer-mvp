"""Add last_tested_at and is_valid to APIKey

Revision ID: 003
Revises: 002
Create Date: 2024-11-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add last_tested_at column
    op.add_column('api_keys', sa.Column('last_tested_at', sa.DateTime(timezone=True), nullable=True))
    # Add is_valid column
    op.add_column('api_keys', sa.Column('is_valid', sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column('api_keys', 'is_valid')
    op.drop_column('api_keys', 'last_tested_at')