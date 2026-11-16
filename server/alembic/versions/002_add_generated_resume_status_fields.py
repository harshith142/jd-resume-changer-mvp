"""add_generated_resume_status_fields

Revision ID: 002
Revises: 001
Create Date: 2024-11-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to generated_resumes table
    op.add_column('generated_resumes', sa.Column('status', sa.String(20), nullable=False, server_default='completed'))
    op.add_column('generated_resumes', sa.Column('error_message', sa.Text(), nullable=True))
    op.add_column('generated_resumes', sa.Column('generation_time_ms', sa.Integer(), nullable=True))
    op.add_column('generated_resumes', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))


def downgrade() -> None:
    op.drop_column('generated_resumes', 'updated_at')
    op.drop_column('generated_resumes', 'generation_time_ms')
    op.drop_column('generated_resumes', 'error_message')
    op.drop_column('generated_resumes', 'status')