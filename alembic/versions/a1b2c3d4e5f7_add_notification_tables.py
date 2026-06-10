"""Add notification preferences and notification log tables

Revision ID: a1b2c3d4e5f7
Revises: a3b4c5d6e7f8
Create Date: 2026-06-03 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f7'
down_revision: Union[str, None] = 'a3b4c5d6e7f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the enum type for notification event types
    notification_event_type = sa.Enum(
        'TASK_CREATED',
        'TASK_STATUS_CHANGED',
        'TASK_ASSIGNED',
        'TASK_REASSIGNED',
        'TASK_DETAILS_UPDATED',
        'TASK_DELETED',
        'TASK_PRIORITY_CHANGED',
        'TASK_DUE_DATE_CHANGED',
        'TASK_SPRINT_CHANGED',
        'TASK_COMMENT_ADDED',
        'TASK_COMMENT_MENTION',
        'SPRINT_STARTED',
        'SPRINT_COMPLETED',
        'PROJECT_STATUS_CHANGED',
        name='notification_event_type_enum',
    )

    # ── notification_preferences table ───────────────────────────
    op.create_table(
        'notification_preferences',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', notification_event_type, nullable=False),
        sa.Column('email_enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index('idx_notif_pref_user', 'notification_preferences', ['user_id'])
    op.create_unique_constraint('uq_user_event_type', 'notification_preferences', ['user_id', 'event_type'])

    # ── notification_log table ───────────────────────────────────
    op.create_table(
        'notification_log',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('email_to', sa.String(), nullable=False),
        sa.Column('email_subject', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('idempotency_key', sa.String(), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_index('idx_notif_log_user_created', 'notification_log', ['user_id', 'created_at'])
    op.create_index('idx_notif_log_idemp', 'notification_log', ['idempotency_key'])


def downgrade() -> None:
    op.drop_table('notification_log')
    op.drop_table('notification_preferences')
    op.execute('DROP TYPE IF EXISTS notification_event_type_enum')
