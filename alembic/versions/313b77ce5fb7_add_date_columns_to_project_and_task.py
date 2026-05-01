"""add_date_columns_to_project_and_task

Revision ID: 313b77ce5fb7
Revises: 25ffdbc70eda
Create Date: 2026-04-30 18:16:13.051021

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '313b77ce5fb7'
down_revision: Union[str, Sequence[str], None] = '25ffdbc70eda'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add start_date and end_date to projects
    op.add_column('projects', sa.Column('start_date', sa.Date(), nullable=True))
    op.add_column('projects', sa.Column('end_date', sa.Date(), nullable=True))
    
    # Add start_date and due_date to tasks
    op.add_column('tasks', sa.Column('start_date', sa.Date(), nullable=True))
    op.add_column('tasks', sa.Column('due_date', sa.Date(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('tasks', 'due_date')
    op.drop_column('tasks', 'start_date')
    op.drop_column('projects', 'end_date')
    op.drop_column('projects', 'start_date')
