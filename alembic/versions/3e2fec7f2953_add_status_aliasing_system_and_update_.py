"""Add status aliasing system and update task statuses

Revision ID: 3e2fec7f2953
Revises: 4616d35b9868
Create Date: 2026-05-13 22:57:56.044329

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3e2fec7f2953'
down_revision: Union[str, Sequence[str], None] = '4616d35b9868'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add status_aliases column to projects
    op.add_column('projects', sa.Column('status_aliases', sa.JSON(), nullable=False, server_default='{}'))
    
    # Update task_status_enum with new values
    # We use execute here because native Enum handling in Alembic/Postgres requires autocommit for TYPE alterations
    bind = op.get_bind()
    if bind.engine.name == 'postgresql':
        with op.get_context().autocommit_block():
            for status in ['OPEN', 'PENDING_APPROVAL', 'ON_HOLD', 'CLOSED']:
                op.execute(sa.text(f"ALTER TYPE task_status_enum ADD VALUE IF NOT EXISTS '{status}'"))

    # Update existing data to use new system keys
    op.execute("UPDATE tasks SET status = 'OPEN' WHERE status = 'TODO'")
    op.execute("UPDATE tasks SET status = 'PENDING_APPROVAL' WHERE status = 'IN_REVIEW'")
    op.execute("UPDATE tasks SET status = 'CLOSED' WHERE status = 'DONE'")


def downgrade() -> None:
    """Downgrade schema."""
    # Reverse data migration (approximate)
    op.execute("UPDATE tasks SET status = 'TODO' WHERE status = 'OPEN'")
    op.execute("UPDATE tasks SET status = 'IN_REVIEW' WHERE status = 'PENDING_APPROVAL'")
    op.execute("UPDATE tasks SET status = 'DONE' WHERE status = 'CLOSED'")
    
    # Remove status_aliases column
    op.drop_column('projects', 'status_aliases')
