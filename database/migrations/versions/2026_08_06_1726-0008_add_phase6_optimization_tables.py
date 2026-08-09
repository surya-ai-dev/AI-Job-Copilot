"""add phase6 optimization tables

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-06 17:26:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create candidate_profiles table
    op.create_table(
        'candidate_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), nullable=False),

        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('linkedin_url', sa.String(length=512), nullable=True),
        sa.Column('github_url', sa.String(length=512), nullable=True),
        sa.Column('professional_summary', sa.String(), nullable=True),

        sa.Column('skills_json', sa.JSON(), nullable=False),
        sa.Column('experience_json', sa.JSON(), nullable=False),
        sa.Column('projects_json', sa.JSON(), nullable=False),
        sa.Column('education_json', sa.JSON(), nullable=False),
        sa.Column('certifications_json', sa.JSON(), nullable=False),

        sa.Column('is_active', sa.Boolean(), nullable=False),

        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),

        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['resume_id'],
            ['resumes.id'],
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(
        op.f('ix_candidate_profiles_id'),
        'candidate_profiles',
        ['id'],
        unique=False
    )

    op.create_index(
        op.f('ix_candidate_profiles_user_id'),
        'candidate_profiles',
        ['user_id'],
        unique=False
    )

    op.create_index(
        op.f('ix_candidate_profiles_resume_id'),
        'candidate_profiles',
        ['resume_id'],
        unique=False
    )

    op.create_index(
        op.f('ix_candidate_profiles_is_active'),
        'candidate_profiles',
        ['is_active'],
        unique=False
    )

       # 2. Create resume_optimization_runs table
    op.create_table(
        'resume_optimization_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('candidate_profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('initial_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('final_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ['candidate_profile_id'],
            ['candidate_profiles.id'],
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['job_profile_id'],
            ['jobs.id'],
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(
        op.f('ix_resume_optimization_runs_id'),
        'resume_optimization_runs',
        ['id'],
        unique=False
    )

    # 3. Create optimization_iterations table
    op.create_table(
        'optimization_iterations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('iteration_number', sa.Integer(), nullable=False),
        sa.Column('pre_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('post_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('planning_tasks', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['run_id'],
            ['resume_optimization_runs.id'],
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(
        op.f('ix_optimization_iterations_id'),
        'optimization_iterations',
        ['id'],
        unique=False
    )

    # 3. Create optimization_changes table
    op.create_table(
        'optimization_changes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('iteration_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('modified_sections', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['iteration_id'], ['optimization_iterations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('iteration_id')
    )
    op.create_index(op.f('ix_optimization_changes_id'), 'optimization_changes', ['id'], unique=False)

    # 4. Create optimization_histories table
    op.create_table(
        'optimization_histories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('total_iterations', sa.Integer(), nullable=False),
        sa.Column('optimization_log', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['run_id'], ['resume_optimization_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('run_id')
    )
    op.create_index(op.f('ix_optimization_histories_id'), 'optimization_histories', ['id'], unique=False)

    # 5. Create critic_feedback table
    op.create_table(
        'critic_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('iteration_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('approved', sa.Boolean(), nullable=False),
        sa.Column('comments', sa.JSON(), nullable=False),
        sa.Column('awkward_phrases', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['iteration_id'], ['optimization_iterations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_critic_feedback_id'), 'critic_feedback', ['id'], unique=False)

    # 6. Create validator_results table
    op.create_table(
        'validator_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('iteration_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('violations', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['iteration_id'], ['optimization_iterations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_validator_results_id'), 'validator_results', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse dependent order
    op.drop_index(op.f('ix_validator_results_id'), table_name='validator_results')
    op.drop_table('validator_results')

    op.drop_index(op.f('ix_critic_feedback_id'), table_name='critic_feedback')
    op.drop_table('critic_feedback')

    op.drop_index(op.f('ix_optimization_histories_id'), table_name='optimization_histories')
    op.drop_table('optimization_histories')

    op.drop_index(op.f('ix_optimization_changes_id'), table_name='optimization_changes')
    op.drop_table('optimization_changes')

    op.drop_index(op.f('ix_optimization_iterations_id'), table_name='optimization_iterations')
    op.drop_table('optimization_iterations')

    op.drop_index(op.f('ix_resume_optimization_runs_id'), table_name='resume_optimization_runs')
    op.drop_table('resume_optimization_runs')


    op.drop_index(
        op.f('ix_candidate_profiles_is_active'),
        table_name='candidate_profiles'
    )
    op.drop_index(
        op.f('ix_candidate_profiles_resume_id'),
        table_name='candidate_profiles'
    )
    op.drop_index(
        op.f('ix_candidate_profiles_user_id'),
        table_name='candidate_profiles'
    )
    op.drop_index(
        op.f('ix_candidate_profiles_id'),
        table_name='candidate_profiles'
    )
    op.drop_table('candidate_profiles')
