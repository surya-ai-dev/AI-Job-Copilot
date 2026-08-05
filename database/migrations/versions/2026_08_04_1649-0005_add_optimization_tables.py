# database/migrations/versions/2026_08_04_1649-0005_add_optimization_tables.py
# Alembic database migration script creating resume_optimizations table

"""add optimization tables

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-04 16:49:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create resume_optimizations table
    op.create_table(
        'resume_optimizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_analysis_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('match_score', sa.Integer(), nullable=False),
        sa.Column('ats_score', sa.Integer(), nullable=False),
        sa.Column('optimized_file_path', sa.String(length=512), nullable=False),
        sa.Column('match_details_json', sa.JSON(), nullable=False),
        sa.Column('ats_evaluation_json', sa.JSON(), nullable=False),
        sa.Column('recommendations_json', sa.JSON(), nullable=False),
        sa.Column('optimized_summary', sa.String(length=1000), nullable=False),
        sa.Column('optimized_skills_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_analysis_id'], ['job_analyses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resume_optimizations_id'), 'resume_optimizations', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_resume_optimizations_id'), table_name='resume_optimizations')
    op.drop_table('resume_optimizations')
