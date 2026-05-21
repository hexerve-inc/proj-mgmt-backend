"""add labels and task_groups

Revision ID: 999_add_labels_and_task_groups
Revises: ef3d8b34c69e
Create Date: 2026-05-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '999_add_labels_and_task_groups'
down_revision: Union[str, Sequence[str], None] = 'ef3d8b34c69e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'task_groups',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('project_id', sa.String(), nullable=True),
    )

    op.create_table(
        'labels',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('project_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'task_labels',
        sa.Column('task_id', sa.String(), sa.ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('label_id', sa.String(), sa.ForeignKey('labels.id', ondelete='CASCADE'), primary_key=True),
    )

    op.add_column('tasks', sa.Column('group_id', sa.String(), nullable=True))
    op.create_foreign_key('fk_tasks_task_group', 'tasks', 'task_groups', ['group_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint('fk_tasks_task_group', 'tasks', type_='foreignkey')
    op.drop_column('tasks', 'group_id')
    op.drop_table('task_labels')
    op.drop_table('labels')
    op.drop_table('task_groups')
