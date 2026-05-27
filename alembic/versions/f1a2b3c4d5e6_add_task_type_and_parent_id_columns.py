"""Add task_type and parent_id columns to tasks

Revision ID: f1a2b3c4d5e6
Revises: 2341a532ff9f
Create Date: 2026-05-28 00:07:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = '2341a532ff9f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column already exists in the table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    """Add task_type and parent_id columns if they don't already exist."""
    if not _column_exists('tasks', 'task_type'):
        op.add_column('tasks', sa.Column('task_type', sa.String(), nullable=False, server_default='task'))

    if not _column_exists('tasks', 'parent_id'):
        op.add_column('tasks', sa.Column('parent_id', sa.String(), nullable=True))


def downgrade() -> None:
    """Remove task_type and parent_id columns."""
    if _column_exists('tasks', 'parent_id'):
        op.drop_column('tasks', 'parent_id')

    if _column_exists('tasks', 'task_type'):
        op.drop_column('tasks', 'task_type')
