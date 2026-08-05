# database/migrations/versions/2026_08_04_1647-0004_add_analysis_tables.py
# Alembic database migration script creating job_analyses table

"""add analysis tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-04 16:47:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create job_analyses table
    op.create_table(
        'job_analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('llm_provider', sa.String(length=50), nullable=False),
        sa.Column('prompt_version', sa.String(length=20), nullable=False),
        sa.Column('processing_time_ms', sa.Integer(), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('skills_json', sa.JSON(), nullable=False),
        sa.Column('ats_keywords_json', sa.JSON(), nullable=False),
        sa.Column('responsibilities_json', sa.JSON(), nullable=False),
        sa.Column('qualifications_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_job_analyses_id'), 'job_analyses', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_job_analyses_id'), table_name='job_analyses')
    op.drop_table('job_analyses')
