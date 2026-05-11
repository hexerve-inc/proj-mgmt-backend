"""add_timer_fields_to_time_entries

Revision ID: a1b2c3d4e5f6
Revises: d911e4e500d3
Create Date: 2026-05-05 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'd911e4e500d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add timer-based activity tracking fields (non-destructive: all nullable / have defaults)
    op.add_column('time_entries', sa.Column('start_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('time_entries', sa.Column('end_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('time_entries', sa.Column('is_running', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    
    # Make duration nullable (was NOT NULL) to support running timers without a duration yet
    op.alter_column('time_entries', 'duration',
                     existing_type=sa.Integer(),
                     nullable=True)


def downgrade() -> None:
    # Revert duration back to NOT NULL (set running entries to 0 first)
    op.execute("UPDATE time_entries SET duration = 0 WHERE duration IS NULL")
    op.alter_column('time_entries', 'duration',
                     existing_type=sa.Integer(),
                     nullable=False)
    
    op.drop_column('time_entries', 'is_running')
    op.drop_column('time_entries', 'end_at')
    op.drop_column('time_entries', 'start_at')
