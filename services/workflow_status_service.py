import re
import uuid
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.task import Task
from models.workflow_status import WorkflowGroup, WorkflowStatus
from schemas.workflow_status import (
    WorkflowStatusCreate,
    WorkflowStatusUpdate,
    WorkflowStatusReorderItem,
)

# Default statuses seeded for every new project
DEFAULT_STATUSES = [
    {"name": "Open",         "group_key": WorkflowGroup.OPEN,        "color": "#6B7280", "position": 0, "is_default": True},
    {"name": "In Progress",  "group_key": WorkflowGroup.IN_PROGRESS, "color": "#7B68EE", "position": 0, "is_default": False},
    {"name": "On Hold",      "group_key": WorkflowGroup.ON_HOLD,     "color": "#F59E0B", "position": 0, "is_default": False},
    {"name": "Closed",       "group_key": WorkflowGroup.CLOSED,      "color": "#22C55E", "position": 0, "is_default": False},
]

# Canonical ordering of workflow groups for deterministic sorting
GROUP_ORDER = {
    WorkflowGroup.OPEN: 0,
    WorkflowGroup.IN_PROGRESS: 1,
    WorkflowGroup.ON_HOLD: 2,
    WorkflowGroup.CLOSED: 3,
}

MAX_STATUSES_PER_PROJECT = 30


class WorkflowStatusService:
    def __init__(self, db: Session):
        self.db = db

    # ── Helpers ──────────────────────────────────────────────────

    @staticmethod
    def _slugify(name: str) -> str:
        """Convert a display name to a URL-safe slug."""
        slug = name.strip().lower()
        slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
        return slug or "status"

    def _next_position(self, project_id: str, group_key: WorkflowGroup) -> int:
        """Return the next available position within a group."""
        max_pos = (
            self.db.query(func.max(WorkflowStatus.position))
            .filter(
                WorkflowStatus.project_id == project_id,
                WorkflowStatus.group_key == group_key,
            )
            .scalar()
        )
        return (max_pos or 0) + 1 if max_pos is not None else 0

    def _ensure_unique_slug(self, project_id: str, slug: str, exclude_id: Optional[str] = None) -> str:
        """Ensure the slug is unique within the project, appending a suffix if needed."""
        original_slug = slug
        counter = 1
        while True:
            query = self.db.query(WorkflowStatus).filter(
                WorkflowStatus.project_id == project_id,
                WorkflowStatus.slug == slug,
            )
            if exclude_id:
                query = query.filter(WorkflowStatus.id != exclude_id)
            if not query.first():
                return slug
            slug = f"{original_slug}-{counter}"
            counter += 1

    # ── Read ─────────────────────────────────────────────────────

    def get_statuses(self, project_id: str) -> list[WorkflowStatus]:
        """Return all statuses for a project, sorted by group order then position."""
        statuses = (
            self.db.query(WorkflowStatus)
            .filter(WorkflowStatus.project_id == project_id)
            .all()
        )
        return sorted(
            statuses,
            key=lambda s: (GROUP_ORDER.get(s.group_key, 99), s.position),
        )

    def get_status(self, status_id: str) -> Optional[WorkflowStatus]:
        return (
            self.db.query(WorkflowStatus)
            .filter(WorkflowStatus.id == status_id)
            .first()
        )

    def get_default_status(self, project_id: str) -> Optional[WorkflowStatus]:
        """Return the status marked as default for this project."""
        return (
            self.db.query(WorkflowStatus)
            .filter(
                WorkflowStatus.project_id == project_id,
                WorkflowStatus.is_default == True,
            )
            .first()
        )

    # ── Create ───────────────────────────────────────────────────

    def create_status(
        self, project_id: str, data: WorkflowStatusCreate
    ) -> WorkflowStatus:
        """Create a new custom status within a project."""
        # Enforce cap
        count = (
            self.db.query(func.count(WorkflowStatus.id))
            .filter(WorkflowStatus.project_id == project_id)
            .scalar()
        )
        if count >= MAX_STATUSES_PER_PROJECT:
            raise ValueError(
                f"Cannot exceed {MAX_STATUSES_PER_PROJECT} statuses per project."
            )

        slug = self._slugify(data.slug or data.name)
        slug = self._ensure_unique_slug(project_id, slug)

        position = (
            data.position
            if data.position is not None
            else self._next_position(project_id, data.group_key)
        )

        # If marked as default, unset any existing default
        if data.is_default:
            self._clear_defaults(project_id)

        status = WorkflowStatus(
            id=str(uuid.uuid4()),
            project_id=project_id,
            name=data.name.strip(),
            slug=slug,
            group_key=data.group_key,
            color=data.color or "#6B7280",
            icon=data.icon,
            position=position,
            is_default=data.is_default or False,
        )
        self.db.add(status)
        self.db.commit()
        self.db.refresh(status)
        return status

    # ── Update ───────────────────────────────────────────────────

    def update_status(
        self, status_id: str, data: WorkflowStatusUpdate
    ) -> Optional[WorkflowStatus]:
        status = self.get_status(status_id)
        if not status:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Handle slug regeneration if name changes
        if "name" in update_data and "slug" not in update_data:
            update_data["slug"] = self._slugify(update_data["name"])
        if "slug" in update_data:
            update_data["slug"] = self._ensure_unique_slug(
                status.project_id, update_data["slug"], exclude_id=status_id
            )

        # If setting as default, clear others
        if update_data.get("is_default"):
            self._clear_defaults(status.project_id)

        for field, value in update_data.items():
            setattr(status, field, value)

        self.db.commit()
        self.db.refresh(status)
        return status

    # ── Delete ───────────────────────────────────────────────────

    def delete_status(
        self, status_id: str, move_to_status_id: Optional[str] = None
    ) -> None:
        """Delete a status, moving its tasks to another status first.

        Enforces:
        - Cannot delete the last status in the OPEN or CLOSED groups.
        - Must provide a move_to_status_id if tasks exist with this status.
        """
        status = self.get_status(status_id)
        if not status:
            raise ValueError("Status not found.")

        # Check group minimum constraint
        siblings = (
            self.db.query(WorkflowStatus)
            .filter(
                WorkflowStatus.project_id == status.project_id,
                WorkflowStatus.group_key == status.group_key,
                WorkflowStatus.id != status_id,
            )
            .count()
        )
        if siblings == 0 and status.group_key in (
            WorkflowGroup.OPEN,
            WorkflowGroup.CLOSED,
        ):
            raise ValueError(
                f"Cannot delete the last status in the {status.group_key.value} group."
            )

        # Check for tasks using this status
        task_count = (
            self.db.query(func.count(Task.id))
            .filter(Task.status_id == status_id)
            .scalar()
        )
        if task_count > 0:
            if not move_to_status_id:
                raise ValueError(
                    f"{task_count} task(s) use this status. "
                    "Provide move_to_status_id to reassign them."
                )
            target = self.get_status(move_to_status_id)
            if not target or target.project_id != status.project_id:
                raise ValueError("Invalid target status for task reassignment.")
            # Move all affected tasks
            self.db.query(Task).filter(Task.status_id == status_id).update(
                {"status_id": move_to_status_id}
            )

        self.db.delete(status)
        self.db.commit()

    # ── Reorder ──────────────────────────────────────────────────

    def reorder_statuses(
        self, project_id: str, items: list[WorkflowStatusReorderItem]
    ) -> list[WorkflowStatus]:
        """Batch-update positions (and optionally group assignments)."""
        for item in items:
            status = self.get_status(item.id)
            if not status or status.project_id != project_id:
                continue
            status.position = item.position
            if item.group_key is not None:
                status.group_key = item.group_key

        self.db.commit()
        return self.get_statuses(project_id)

    # ── Seed Defaults ────────────────────────────────────────────

    def seed_defaults(self, project_id: str) -> list[WorkflowStatus]:
        """Create the four default statuses for a newly created project."""
        # Idempotency check: if project already has statuses, do not duplicate them.
        existing_count = self.db.query(func.count(WorkflowStatus.id)).filter(WorkflowStatus.project_id == project_id).scalar()
        if existing_count > 0:
            return self.get_statuses(project_id)

        created = []
        for entry in DEFAULT_STATUSES:
            slug = self._slugify(entry["name"])
            slug = self._ensure_unique_slug(project_id, slug)
            status = WorkflowStatus(
                id=str(uuid.uuid4()),
                project_id=project_id,
                name=entry["name"],
                slug=slug,
                group_key=entry["group_key"],
                color=entry["color"],
                position=entry["position"],
                is_default=entry["is_default"],
            )
            self.db.add(status)
            created.append(status)
        self.db.flush()  # Flush (not commit) — caller controls transaction
        return created

    # ── Internal ─────────────────────────────────────────────────

    def _clear_defaults(self, project_id: str) -> None:
        """Unset is_default on all statuses for a project."""
        self.db.query(WorkflowStatus).filter(
            WorkflowStatus.project_id == project_id,
            WorkflowStatus.is_default == True,
        ).update({"is_default": False})
