"""Add email_configurations table

Revision ID: e1m2a3i4l5c6
Revises: 002c3ae3c373
Create Date: 2026-07-03 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1m2a3i4l5c6'
down_revision: Union[str, Sequence[str], None] = '002c3ae3c373'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the email_configurations table."""
    op.create_table(
        'email_configurations',
        sa.Column('id', sa.String(), primary_key=True),
        # Sender identity
        sa.Column('sender_email', sa.String(320), nullable=False),
        sa.Column('sender_name', sa.String(200), nullable=False),
        # SMTP connection
        sa.Column('smtp_host', sa.String(255), nullable=False),
        sa.Column('smtp_port', sa.Integer(), nullable=False, server_default='587'),
        sa.Column('smtp_username', sa.String(320), nullable=True),
        sa.Column('smtp_password_encrypted', sa.Text(), nullable=True),
        sa.Column('encryption_type', sa.String(10), nullable=False, server_default='TLS'),
        # Operational flags
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        # Test / status tracking
        sa.Column('last_tested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_test_status', sa.String(20), nullable=True),
        sa.Column('last_test_error', sa.String(500), nullable=True),
        # Audit — who configured this
        sa.Column('configured_by_id', sa.String(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        # SoftDeleteMixin columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index('idx_email_config_active', 'email_configurations', ['is_active'])
    # NOTE: idx_email_configurations_deleted_at is auto-created by SoftDeleteMixin event listener


def downgrade() -> None:
    """Drop the email_configurations table."""
    op.drop_index('idx_email_config_active', table_name='email_configurations')
    op.drop_table('email_configurations')
