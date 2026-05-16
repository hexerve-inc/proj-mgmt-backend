"""Introduce workflow status engine — replace hardcoded TaskStatus enum

Revision ID: c7a1e3f49b02
Revises: 3e2fec7f2953
Create Date: 2026-05-15 08:30:00.000000

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "c7a1e3f49b02"
down_revision: Union[str, Sequence[str], None] = "3e2fec7f2953"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ── Mapping of old enum values to the new workflow status system ──────
OLD_STATUS_MAP = [
    {"enum_key": "OPEN",             "name": "Open",             "group": "OPEN",        "position": 0, "is_default": True},
    {"enum_key": "ASSIGNED",         "name": "Assigned",         "group": "OPEN",        "position": 1, "is_default": False},
    {"enum_key": "IN_PROGRESS",      "name": "In Progress",      "group": "IN_PROGRESS", "position": 0, "is_default": False},
    {"enum_key": "PENDING_APPROVAL", "name": "Pending Approval", "group": "IN_PROGRESS", "position": 1, "is_default": False},
    {"enum_key": "ON_HOLD",          "name": "On Hold",          "group": "ON_HOLD",     "position": 0, "is_default": False},
    {"enum_key": "CLOSED",           "name": "Closed",           "group": "CLOSED",      "position": 0, "is_default": False},
]

DEFAULT_COLORS = {
    "OPEN":        "#6B7280",
    "IN_PROGRESS": "#7B68EE",
    "ON_HOLD":     "#F59E0B",
    "CLOSED":      "#22C55E",
}


def _slugify(name: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-") or "status"


def upgrade() -> None:
    """
    Step 1: Create workflow_statuses table
    Step 2: Seed statuses for each existing project (respecting status_aliases)
    Step 3: Add status_id column to tasks (nullable)
    Step 4: Populate status_id for all existing tasks
    Step 5: Make status_id NOT NULL
    Step 6: Drop old status column from tasks
    Step 7: Drop status_aliases column from projects
    """

    # ── Step 1: Create the workflow_group_enum type and workflow_statuses table ──
    workflow_group_enum = postgresql.ENUM(
        "OPEN", "IN_PROGRESS", "ON_HOLD", "CLOSED",
        name="workflow_group_enum",
        create_type=False,
    )
    # Create the enum type explicitly
    op.execute("CREATE TYPE workflow_group_enum AS ENUM ('OPEN', 'IN_PROGRESS', 'ON_HOLD', 'CLOSED')")

    op.create_table(
        "workflow_statuses",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("group_key", workflow_group_enum, nullable=False),
        sa.Column("color", sa.String(7), server_default="#6B7280"),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("project_id", "slug", name="uq_project_status_slug"),
    )
    op.create_index("idx_ws_project", "workflow_statuses", ["project_id"])
    op.create_index("idx_ws_group", "workflow_statuses", ["group_key"])

    # ── Step 2: Seed statuses for every existing project ─────────────
    bind = op.get_bind()

    projects = bind.execute(
        sa.text("SELECT id, status_aliases FROM projects")
    ).fetchall()

    # Build a lookup: (project_id, old_enum_key) → new_status_id
    # This is needed in Step 4 to populate tasks.status_id
    status_id_map: dict[tuple[str, str], str] = {}

    for project_row in projects:
        project_id = project_row[0]
        # status_aliases may be a JSON string or dict depending on DB driver
        aliases_raw = project_row[1]
        aliases: dict = {}
        if aliases_raw:
            if isinstance(aliases_raw, str):
                import json
                try:
                    aliases = json.loads(aliases_raw)
                except (json.JSONDecodeError, TypeError):
                    aliases = {}
            elif isinstance(aliases_raw, dict):
                aliases = aliases_raw

        for entry in OLD_STATUS_MAP:
            status_id = str(uuid.uuid4())
            display_name = aliases.get(entry["enum_key"], entry["name"])
            slug = _slugify(display_name)
            color = DEFAULT_COLORS.get(entry["group"], "#6B7280")

            bind.execute(
                sa.text(
                    """
                    INSERT INTO workflow_statuses
                        (id, project_id, name, slug, group_key, color, position, is_default)
                    VALUES
                        (:id, :project_id, :name, :slug, :group_key, :color, :position, :is_default)
                    """
                ),
                {
                    "id": status_id,
                    "project_id": project_id,
                    "name": display_name,
                    "slug": slug,
                    "group_key": entry["group"],
                    "color": color,
                    "position": entry["position"],
                    "is_default": entry["is_default"],
                },
            )
            status_id_map[(project_id, entry["enum_key"])] = status_id

    # ── Step 3: Add status_id column (nullable for now) ──────────────
    op.add_column(
        "tasks",
        sa.Column("status_id", sa.String(), nullable=True),
    )

    # ── Step 4: Populate status_id from old status enum ──────────────
    # For each (project_id, old_enum) combination, update matching tasks
    for (project_id, enum_key), new_status_id in status_id_map.items():
        bind.execute(
            sa.text(
                """
                UPDATE tasks
                SET status_id = :new_status_id
                WHERE project_id = :project_id
                  AND status = :old_status
                """
            ),
            {
                "new_status_id": new_status_id,
                "project_id": project_id,
                "old_status": enum_key,
            },
        )

    # ── Step 5: Make status_id NOT NULL + add FK ─────────────────────
    op.alter_column("tasks", "status_id", nullable=False)
    op.create_foreign_key(
        "fk_tasks_status_id",
        "tasks",
        "workflow_statuses",
        ["status_id"],
        ["id"],
    )

    # ── Step 6: Drop old status column and enum type ─────────────────
    op.drop_column("tasks", "status")
    # Drop the old PostgreSQL enum type
    op.execute("DROP TYPE IF EXISTS task_status_enum")

    # ── Step 7: Drop status_aliases from projects ────────────────────
    op.drop_column("projects", "status_aliases")


def downgrade() -> None:
    """Reverse the migration: restore old enum-based status system."""

    # ── Re-add status_aliases to projects ────────────────────────────
    op.add_column(
        "projects",
        sa.Column("status_aliases", sa.JSON(), nullable=False, server_default="{}"),
    )

    # ── Re-create the old task_status_enum ────────────────────────────
    op.execute(
        "CREATE TYPE task_status_enum AS ENUM "
        "('OPEN', 'ASSIGNED', 'IN_PROGRESS', 'PENDING_APPROVAL', 'ON_HOLD', 'CLOSED')"
    )
    op.add_column(
        "tasks",
        sa.Column(
            "status",
            postgresql.ENUM(
                "OPEN", "ASSIGNED", "IN_PROGRESS",
                "PENDING_APPROVAL", "ON_HOLD", "CLOSED",
                name="task_status_enum",
                create_type=False,
            ),
            nullable=True,
        ),
    )

    # ── Restore status from workflow_statuses group_key ───────────────
    bind = op.get_bind()

    # Map group_key back to the "best match" old enum value
    group_to_enum = {
        "OPEN": "OPEN",
        "IN_PROGRESS": "IN_PROGRESS",
        "ON_HOLD": "ON_HOLD",
        "CLOSED": "CLOSED",
    }
    for group_key, enum_val in group_to_enum.items():
        bind.execute(
            sa.text(
                """
                UPDATE tasks t
                SET status = :enum_val
                FROM workflow_statuses ws
                WHERE t.status_id = ws.id
                  AND ws.group_key = :group_key
                """
            ),
            {"enum_val": enum_val, "group_key": group_key},
        )

    op.alter_column("tasks", "status", nullable=False)

    # ── Drop status_id FK and column ─────────────────────────────────
    op.drop_constraint("fk_tasks_status_id", "tasks", type_="foreignkey")
    op.drop_column("tasks", "status_id")

    # ── Drop workflow_statuses table and enum ────────────────────────
    op.drop_index("idx_ws_group", "workflow_statuses")
    op.drop_index("idx_ws_project", "workflow_statuses")
    op.drop_table("workflow_statuses")
    op.execute("DROP TYPE IF EXISTS workflow_group_enum")
