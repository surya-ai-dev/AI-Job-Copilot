# database/migrations/versions/2026_08_04_1650-0006_add_email_tables.py
# Alembic database migration script creating email_drafts, email_histories, & gmail_oauth_tokens tables

"""add email tables

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-04 16:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create email_drafts table
    op.create_table(
        'email_drafts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recipient_email', sa.String(length=255), nullable=False),
        sa.Column('recipient_name', sa.String(length=100), nullable=True),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('attachment_path', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_drafts_id'), 'email_drafts', ['id'], unique=False)

    # 2. Create email_histories table
    op.create_table(
        'email_histories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recipient_email', sa.String(length=255), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('attachment_path', sa.String(length=512), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_histories_id'), 'email_histories', ['id'], unique=False)

    # 3. Create gmail_oauth_tokens table
    op.create_table(
        'gmail_oauth_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('access_token', sa.String(length=1024), nullable=False),
        sa.Column('refresh_token', sa.String(length=1024), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_gmail_oauth_tokens_id'), 'gmail_oauth_tokens', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_gmail_oauth_tokens_id'), table_name='gmail_oauth_tokens')
    op.drop_table('gmail_oauth_tokens')
    
    op.drop_index(op.f('ix_email_histories_id'), table_name='email_histories')
    op.drop_table('email_histories')
    
    op.drop_index(op.f('ix_email_drafts_id'), table_name='email_drafts')
    op.drop_table('email_drafts')
