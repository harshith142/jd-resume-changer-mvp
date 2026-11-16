\"\"\"Initial migration

Revision ID: 001
Revises:
Create Date: 2024-11-13

\"\"\"
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    # Use CHAR(36) for UUID to support both SQLite and PostgreSQL
    op.create_table(
        'users',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('oauth_provider', sa.String(20), nullable=True),
        sa.Column('oauth_subject', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1'), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('refresh_token_hash', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('oauth_provider', 'oauth_subject', name='uq_users_oauth'),
    )
    op.create_index('ix_users_oauth_provider_subject', 'users', ['oauth_provider', 'oauth_subject'])

    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('user_id', sa.CHAR(36), nullable=False),
        sa.Column('provider', sa.String(20), nullable=False),
        sa.Column('key_encrypted', sa.LargeBinary(), nullable=True),
        sa.Column('key_nonce', sa.LargeBinary(), nullable=True),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('ollama_host', sa.String(200), nullable=True),
        sa.Column('is_session_only', sa.Boolean(), server_default=sa.text('1'), nullable=False),
        sa.Column('last_tested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_valid', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_api_keys_user_provider', 'api_keys', ['user_id', 'provider'], unique=True)

    # Create master_resumes table
    op.create_table(
        'master_resumes',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('user_id', sa.CHAR(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('latex_source', sa.Text(), nullable=False),
        sa.Column('parsed_profile', postgresql.JSONB(), nullable=True),
        sa.Column('is_default', sa.Boolean(), server_default=sa.text('0'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_master_resumes_user_default', 'master_resumes', ['user_id', 'is_default'])

    # Create job_descriptions table
    op.create_table(
        'job_descriptions',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('user_id', sa.CHAR(36), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=False),
        sa.Column('parsed_profile', postgresql.JSONB(), nullable=True),
        sa.Column('source', sa.String(10), nullable=False, server_default='paste'),
        sa.Column('filename', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_job_descriptions_user_created', 'job_descriptions', ['user_id', 'created_at'])

    # Create generated_resumes table
    op.create_table(
        'generated_resumes',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('user_id', sa.CHAR(36), nullable=False),
        sa.Column('master_resume_id', sa.CHAR(36), nullable=False),
        sa.Column('job_description_id', sa.CHAR(36), nullable=False),
        sa.Column('tailored_latex', sa.Text(), nullable=False),
        sa.Column('pdf_bytes', sa.LargeBinary(), nullable=True),
        sa.Column('ats_score', sa.Float(), nullable=True),
        sa.Column('keyword_match', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('missing_keywords', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('changes', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('ats_notes', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('compile_log', sa.Text(), nullable=True),
        sa.Column('llm_provider_used', sa.String(50), nullable=False),
        sa.Column('llm_model_used', sa.String(100), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('generation_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['master_resume_id'], ['master_resumes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_description_id'], ['job_descriptions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_generated_resumes_user_created', 'generated_resumes', ['user_id', 'created_at'])


def downgrade() -> None:
    op.drop_table('generated_resumes')
    op.drop_table('job_descriptions')
    op.drop_table('master_resumes')
    op.drop_table('api_keys')
    op.drop_table('users')
