"""Add task_type and parent_id columns

Revision ID: a3b4c5d6e7f8
Revises: ff28dfdaa080
Create Date: 2026-05-25 21:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3b4c5d6e7f8'
down_revision: Union[str, Sequence[str], None] = 'ff28dfdaa080'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add task_type and parent_id columns to the tasks table."""
    op.add_column('tasks', sa.Column('task_type', sa.String(), nullable=False, server_default='task'))
    op.add_column('tasks', sa.Column('parent_id', sa.String(), nullable=True))


def downgrade() -> None:
    """Remove task_type and parent_id columns from the tasks table."""
    op.drop_column('tasks', 'parent_id')
    op.drop_column('tasks', 'task_type')
