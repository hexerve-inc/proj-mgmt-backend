"""add_unique_constraints_for_projects

Revision ID: d9a7a5c1e4bf
Revises: b431092c5544
Create Date: 2026-04-27 10:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d9a7a5c1e4bf"
down_revision: Union[str, Sequence[str], None] = "8550072168cc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("projects", sa.Column("project_key", sa.String(), nullable=True))

    # Backfill existing rows so project_key can be made non-null.
    op.execute(
        """
        UPDATE projects
        SET project_key = CONCAT('PRJ-', SUBSTRING(id, 1, 8))
        WHERE project_key IS NULL OR project_key = ''
        """
    )

    op.alter_column("projects", "project_key", existing_type=sa.String(), nullable=False)

    op.create_unique_constraint("uq_projects_name", "projects", ["name"])
    op.create_unique_constraint("uq_projects_project_key", "projects", ["project_key"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_projects_project_key", "projects", type_="unique")
    op.drop_constraint("uq_projects_name", "projects", type_="unique")
    op.drop_column("projects", "project_key")
