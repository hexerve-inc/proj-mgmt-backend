"""add scrum master to team

Revision ID: 4616d35b9868
Revises: 2f8c2c2a222b
Create Date: 2026-05-12 00:27:18.987439

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4616d35b9868'
down_revision: Union[str, Sequence[str], None] = '2f8c2c2a222b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('teams', sa.Column('scrum_master_id', sa.String(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('teams', 'scrum_master_id')
