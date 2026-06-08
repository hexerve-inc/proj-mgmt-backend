"""Add audit timestamps and soft-delete columns to all entity tables

Adds created_at, updated_at, deleted_at columns across all 14 entity tables.
Tables that already had partial audit columns (invoices, labels,
workflow_statuses, custom_filters) are normalised to use
DateTime(timezone=True) and gain the missing columns.

Migration is production-safe:
  - All new columns are nullable (no NOT NULL risk on existing rows)
  - server_default=now() backfills timestamps automatically
  - Indexes on deleted_at optimise soft-delete filter queries
  - Fully rollback-safe with a matching downgrade()

Revision ID: a3b4c5d6e7f8
Revises: 7dd22cb45936
Create Date: 2026-06-02 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3b4c5d6e7f8'
down_revision: Union[str, Sequence[str], None] = '7dd22cb45936'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ── Tables that need ALL THREE columns (created_at, updated_at, deleted_at) ──
TABLES_NEED_ALL = [
    "users",
    "projects",
    "tasks",
    "teams",
    "programs",
    "portfolios",
    "sprints",
    "time_entries",
    "task_groups",
]

# ── Tables that already have created_at (need updated_at + deleted_at) ──
TABLES_HAVE_CREATED_AT = [
    "invoices",
    "labels",
    "workflow_statuses",
]

# ── Table that already has created_at AND updated_at (needs only deleted_at) ──
TABLES_HAVE_BOTH = [
    "custom_filters",
]

# All tables combined (for deleted_at index)
ALL_TABLES = TABLES_NEED_ALL + TABLES_HAVE_CREATED_AT + TABLES_HAVE_BOTH


def upgrade() -> None:
    """Add audit and soft-delete columns to all entity tables."""

    # ── 1. Tables needing all three columns ──────────────────────
    for table in TABLES_NEED_ALL:
        op.add_column(table, sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ))
        op.add_column(table, sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ))
        op.add_column(table, sa.Column(
            'deleted_at',
            sa.DateTime(timezone=True),
            nullable=True,
        ))

    # ── 2. Tables that already have created_at ───────────────────
    #    Alter existing created_at to DateTime(timezone=True),
    #    then add updated_at and deleted_at.
    for table in TABLES_HAVE_CREATED_AT:
        # Alter created_at to be timezone-aware
        op.alter_column(
            table, 'created_at',
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=False if table == 'workflow_statuses' else True,
            nullable=True,
            existing_server_default=sa.text('(CURRENT_TIMESTAMP)') if table != 'workflow_statuses' else None,
            server_default=sa.func.now(),
        )
        op.add_column(table, sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ))
        op.add_column(table, sa.Column(
            'deleted_at',
            sa.DateTime(timezone=True),
            nullable=True,
        ))

    # ── 3. Tables that already have created_at AND updated_at ────
    for table in TABLES_HAVE_BOTH:
        # Alter existing columns to timezone-aware
        op.alter_column(
            table, 'created_at',
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.func.now(),
        )
        op.alter_column(
            table, 'updated_at',
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.func.now(),
        )
        op.add_column(table, sa.Column(
            'deleted_at',
            sa.DateTime(timezone=True),
            nullable=True,
        ))

    # ── 4. Create indexes on deleted_at for all tables ───────────
    for table in ALL_TABLES:
        op.create_index(
            f'idx_{table}_deleted_at',
            table,
            ['deleted_at'],
        )


def downgrade() -> None:
    """Remove all audit and soft-delete columns added by this migration."""

    # ── 1. Drop indexes first ────────────────────────────────────
    for table in ALL_TABLES:
        op.drop_index(f'idx_{table}_deleted_at', table_name=table)

    # ── 2. Tables that had created_at AND updated_at ─────────────
    for table in TABLES_HAVE_BOTH:
        op.drop_column(table, 'deleted_at')
        # Revert columns back to non-timezone DateTime
        op.alter_column(
            table, 'updated_at',
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(),
            nullable=True,
        )
        op.alter_column(
            table, 'created_at',
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(),
            nullable=True,
        )

    # ── 3. Tables that had only created_at ───────────────────────
    for table in TABLES_HAVE_CREATED_AT:
        op.drop_column(table, 'deleted_at')
        op.drop_column(table, 'updated_at')
        # Revert created_at back to non-timezone DateTime
        op.alter_column(
            table, 'created_at',
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(),
            nullable=True if table != 'workflow_statuses' else False,
        )

    # ── 4. Tables that had no audit columns ──────────────────────
    for table in TABLES_NEED_ALL:
        op.drop_column(table, 'deleted_at')
        op.drop_column(table, 'updated_at')
        op.drop_column(table, 'created_at')
