"""add_task_watchers_table

Revision ID: 39411915bcb9
Revises: a1b2c3d4e5f9
Create Date: 2026-06-16 20:57:06.701926

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39411915bcb9'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('task_watchers',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('task_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('task_id', 'user_id', name='uq_task_watcher')
    )
    op.create_index('idx_task_watcher_task', 'task_watchers', ['task_id'], unique=False)
    op.create_index('idx_task_watcher_user', 'task_watchers', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_task_watcher_user', table_name='task_watchers')
    op.drop_index('idx_task_watcher_task', table_name='task_watchers')
    op.drop_table('task_watchers')
