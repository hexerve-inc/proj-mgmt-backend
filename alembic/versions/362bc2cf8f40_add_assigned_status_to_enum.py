"""add_assigned_status_to_enum

Revision ID: 362bc2cf8f40
Revises: 56e858d746f2
Create Date: 2026-04-27 21:44:46.816358

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '362bc2cf8f40'
down_revision: Union[str, Sequence[str], None] = '56e858d746f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add ASSIGNED value to task_status_enum
    # This must be run outside of a transaction block in PostgreSQL
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE task_status_enum ADD VALUE 'ASSIGNED'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
