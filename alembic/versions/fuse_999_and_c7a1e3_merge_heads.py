"""merge heads: fuse 999_add_labels_and_task_groups and c7a1e3f49b02

Revision ID: fuse_999_and_c7a1e3
Revises: c7a1e3f49b02, 999_add_labels_and_task_groups
Create Date: 2026-05-21
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "fuse_999_and_c7a1e3"
down_revision: Union[str, Sequence[str], None] = ("c7a1e3f49b02", "999_add_labels_and_task_groups")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge migration to unify heads. No DB changes required."""
    pass


def downgrade() -> None:
    """Downgrade not supported for merge migration."""
    pass
