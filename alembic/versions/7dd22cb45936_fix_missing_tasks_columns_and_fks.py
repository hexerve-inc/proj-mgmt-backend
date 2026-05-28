"""fix_missing_tasks_columns_and_fks

Revision ID: 7dd22cb45936
Revises: f1a2b3c4d5e6
Create Date: 2026-05-28 19:01:04.980977

Fixes columns and foreign key constraints on the `tasks` table that
were defined in SQLAlchemy models but missing from the live database.
Handles existing data safely by using server_default for NOT NULL columns.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7dd22cb45936'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing columns and FK constraints to tasks table."""
    # 1. Add is_milestone column (NOT NULL) with a server_default so that
    #    existing rows are backfilled with False. This is required because
    #    PostgreSQL will reject adding a NOT NULL column to a table with
    #    existing data unless a default value is provided.
    op.add_column(
        'tasks',
        sa.Column('is_milestone', sa.Boolean(), nullable=False, server_default=sa.text('false'))
    )

    # 2. Add group_id column (nullable FK to task_groups)
    op.add_column(
        'tasks',
        sa.Column('group_id', sa.String(), nullable=True)
    )

    # 3. Create FK constraint: tasks.group_id -> task_groups.id
    op.create_foreign_key(
        'fk_tasks_group_id_task_groups',
        'tasks', 'task_groups',
        ['group_id'], ['id'],
        ondelete='SET NULL'
    )

    # 4. Create FK constraint: tasks.parent_id -> tasks.id
    #    (the column already exists in the DB, but the FK constraint is missing)
    op.create_foreign_key(
        'fk_tasks_parent_id_tasks',
        'tasks', 'tasks',
        ['parent_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Remove the added columns and FK constraints from tasks table."""
    # Drop FK constraints (in reverse order of creation)
    op.drop_constraint('fk_tasks_parent_id_tasks', 'tasks', type_='foreignkey')
    op.drop_constraint('fk_tasks_group_id_task_groups', 'tasks', type_='foreignkey')

    # Drop columns (in reverse order of addition)
    op.drop_column('tasks', 'group_id')
    op.drop_column('tasks', 'is_milestone')
