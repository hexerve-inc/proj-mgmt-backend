"""merge rbac

Revision ID: 8553cc8e8a7b
Revises: 72a9825b0ec2, rbac_001_tables
Create Date: 2026-06-29 18:19:16.161372

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8553cc8e8a7b'
down_revision: Union[str, Sequence[str], None] = ('72a9825b0ec2', 'rbac_001_tables')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
