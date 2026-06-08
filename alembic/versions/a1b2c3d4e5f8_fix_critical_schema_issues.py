"""Fix critical schema issues found during production audit

Corrective migration addressing four critical findings:

  C1 – Add missing audit/soft-delete columns to 'clients' table.
       The Client model inherits SoftDeleteMixin but the original
       audit migration (a3b4c5d6e7f8) omitted this table.

  C3 – Drop the redundant non-unique index 'idx_notif_log_idemp'
       on notification_log.idempotency_key.  The column already
       has a UNIQUE constraint which creates its own B-tree index.

  C4 – Add a CHECK constraint on notification_preferences.event_type
       so the database rejects invalid enum values.  The column was
       stored as VARCHAR(22) instead of a native PostgreSQL ENUM,
       leaving it unvalidated.

  C5 – Tighten VARCHAR columns on notification_log with explicit
       length limits to prevent unbounded storage on a high-write
       audit table.

Revision ID: a1b2c3d4e5f8
Revises: a1b2c3d4e5f7
Create Date: 2026-06-04 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f8'
down_revision: Union[str, None] = 'a1b2c3d4e5f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Valid event types for the CHECK constraint (C4)
VALID_EVENT_TYPES = [
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
]


def upgrade() -> None:
    # ── C1: Add audit columns to 'clients' table ────────────────
    op.add_column('clients', sa.Column(
        'created_at',
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=True,
    ))
    op.add_column('clients', sa.Column(
        'updated_at',
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=True,
    ))
    op.add_column('clients', sa.Column(
        'deleted_at',
        sa.DateTime(timezone=True),
        nullable=True,
    ))
    op.create_index('idx_clients_deleted_at', 'clients', ['deleted_at'])

    # ── C3: Drop redundant index on notification_log.idempotency_key
    op.drop_index('idx_notif_log_idemp', table_name='notification_log')

    # ── C4: Add CHECK constraint on notification_preferences.event_type
    values_list = ", ".join(f"'{v}'" for v in VALID_EVENT_TYPES)
    op.create_check_constraint(
        'ck_notif_pref_event_type_valid',
        'notification_preferences',
        f"event_type IN ({values_list})",
    )

    # ── C5: Tighten VARCHAR lengths on notification_log columns ──
    op.alter_column(
        'notification_log', 'event_type',
        existing_type=sa.String(),
        type_=sa.String(30),
        existing_nullable=False,
    )
    op.alter_column(
        'notification_log', 'entity_id',
        existing_type=sa.String(),
        type_=sa.String(36),
        existing_nullable=False,
    )
    op.alter_column(
        'notification_log', 'entity_type',
        existing_type=sa.String(),
        type_=sa.String(20),
        existing_nullable=False,
    )
    op.alter_column(
        'notification_log', 'email_to',
        existing_type=sa.String(),
        type_=sa.String(320),
        existing_nullable=False,
    )
    op.alter_column(
        'notification_log', 'email_subject',
        existing_type=sa.String(),
        type_=sa.String(500),
        existing_nullable=False,
    )
    op.alter_column(
        'notification_log', 'status',
        existing_type=sa.String(),
        type_=sa.String(10),
        existing_nullable=False,
    )
    op.alter_column(
        'notification_log', 'idempotency_key',
        existing_type=sa.String(),
        type_=sa.String(64),
        existing_nullable=False,
    )


def downgrade() -> None:
    # ── C5: Revert VARCHAR lengths back to unlimited ─────────────
    for col in ('event_type', 'entity_id', 'entity_type',
                'email_to', 'email_subject', 'status', 'idempotency_key'):
        op.alter_column(
            'notification_log', col,
            existing_type=sa.String(64),  # any length, just needs existing_type
            type_=sa.String(),
            existing_nullable=False,
        )

    # ── C4: Drop CHECK constraint ────────────────────────────────
    op.drop_constraint('ck_notif_pref_event_type_valid', 'notification_preferences', type_='check')

    # ── C3: Recreate the redundant index (to match original state)
    op.create_index('idx_notif_log_idemp', 'notification_log', ['idempotency_key'])

    # ── C1: Remove audit columns from 'clients' ─────────────────
    op.drop_index('idx_clients_deleted_at', table_name='clients')
    op.drop_column('clients', 'deleted_at')
    op.drop_column('clients', 'updated_at')
    op.drop_column('clients', 'created_at')
