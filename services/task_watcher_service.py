"""
Task Watcher service — business logic for watching / unwatching tasks.

Handles all CRUD operations on the task_watchers table, including
soft-delete semantics (unwatch) and re-activation (re-watch).
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from models.task_watcher import TaskWatcher
from models.task import Task
from models.user import User

logger = logging.getLogger("task_watcher.service")


class TaskWatcherService:
    """Encapsulates all task-watcher business logic."""

    def __init__(self, db: Session):
        self.db = db

    # ── Watch / Unwatch ──────────────────────────────────────────

    def watch_task(self, task_id: str, user_id: str) -> TaskWatcher:
        """
        Add user as a watcher of the task.

        If a soft-deleted record exists it is re-activated (deleted_at → None).
        Returns the (new or re-activated) TaskWatcher row.
        """
        # Check for existing record (including soft-deleted)
        existing = (
            self.db.query(TaskWatcher)
            .filter(
                TaskWatcher.task_id == task_id,
                TaskWatcher.user_id == user_id,
            )
            .first()
        )

        if existing:
            if existing.deleted_at is not None:
                # Re-activate soft-deleted record
                existing.deleted_at = None
                self.db.commit()
                logger.info(f"Re-activated watcher: user={user_id} task={task_id}")
            # else: already actively watching — no-op
            return existing

        # Create new watcher
        watcher = TaskWatcher(task_id=task_id, user_id=user_id)
        self.db.add(watcher)
        self.db.commit()
        self.db.refresh(watcher)
        logger.info(f"New watcher: user={user_id} task={task_id}")
        return watcher

    def unwatch_task(self, task_id: str, user_id: str) -> bool:
        """
        Remove user as a watcher (soft-delete).

        Returns True if the user was watching (and is now unwatched),
        False if they were not watching.
        """
        watcher = (
            self.db.query(TaskWatcher)
            .filter(
                TaskWatcher.task_id == task_id,
                TaskWatcher.user_id == user_id,
                TaskWatcher.deleted_at.is_(None),
            )
            .first()
        )

        if not watcher:
            return False

        watcher.soft_delete()
        self.db.commit()
        logger.info(f"Unwatched: user={user_id} task={task_id}")
        return True

    # ── Query helpers ────────────────────────────────────────────

    def is_watching(self, task_id: str, user_id: str) -> bool:
        """Check if user is actively watching the task."""
        return (
            self.db.query(TaskWatcher)
            .filter(
                TaskWatcher.task_id == task_id,
                TaskWatcher.user_id == user_id,
                TaskWatcher.deleted_at.is_(None),
            )
            .first()
            is not None
        )

    def get_task_watchers(self, task_id: str) -> list[User]:
        """Return all active watcher User objects for a task."""
        watcher_records = (
            self.db.query(TaskWatcher)
            .filter(
                TaskWatcher.task_id == task_id,
                TaskWatcher.deleted_at.is_(None),
            )
            .all()
        )
        if not watcher_records:
            return []

        user_ids = [w.user_id for w in watcher_records]
        return (
            self.db.query(User)
            .filter(User.id.in_(user_ids), User.deleted_at.is_(None))
            .all()
        )

    def get_task_watchers_with_since(self, task_id: str) -> list[dict]:
        """
        Return watcher details including when they started watching.
        Used for the watcher list popover.
        """
        watcher_records = (
            self.db.query(TaskWatcher)
            .filter(
                TaskWatcher.task_id == task_id,
                TaskWatcher.deleted_at.is_(None),
            )
            .all()
        )
        if not watcher_records:
            return []

        user_ids = [w.user_id for w in watcher_records]
        users = (
            self.db.query(User)
            .filter(User.id.in_(user_ids), User.deleted_at.is_(None))
            .all()
        )
        user_map = {u.id: u for u in users}
        watcher_since_map = {w.user_id: w.created_at for w in watcher_records}

        result = []
        for uid in user_ids:
            user = user_map.get(uid)
            if user:
                result.append({
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "watching_since": (
                        watcher_since_map[uid].isoformat()
                        if watcher_since_map.get(uid)
                        else None
                    ),
                })
        return result

    def get_watcher_count(self, task_id: str) -> int:
        """Return count of active watchers for a task."""
        return (
            self.db.query(func.count(TaskWatcher.id))
            .filter(
                TaskWatcher.task_id == task_id,
                TaskWatcher.deleted_at.is_(None),
            )
            .scalar()
            or 0
        )

    def get_watcher_counts_bulk(self, task_ids: list[str]) -> dict[str, int]:
        """
        Return watcher counts for multiple tasks in a single query.
        Used for list/board views to avoid N+1.
        """
        if not task_ids:
            return {}

        rows = (
            self.db.query(
                TaskWatcher.task_id,
                func.count(TaskWatcher.id).label("cnt"),
            )
            .filter(
                TaskWatcher.task_id.in_(task_ids),
                TaskWatcher.deleted_at.is_(None),
            )
            .group_by(TaskWatcher.task_id)
            .all()
        )
        return {row.task_id: row.cnt for row in rows}

    def get_watchers_bulk(self, task_ids: list[str]) -> dict[str, list[dict]]:
        """
        Return watchers for multiple tasks. Returns a dict of task_id -> list of user dicts.
        """
        if not task_ids:
            return {}

        watcher_records = (
            self.db.query(TaskWatcher, User)
            .join(User, TaskWatcher.user_id == User.id)
            .filter(
                TaskWatcher.task_id.in_(task_ids),
                TaskWatcher.deleted_at.is_(None),
                User.deleted_at.is_(None)
            )
            .all()
        )

        # Import locally to avoid circular dependency
        from schemas.user import UserResponse

        result = {}
        for w, u in watcher_records:
            if w.task_id not in result:
                result[w.task_id] = []
            
            result[w.task_id].append(UserResponse.model_validate(u).model_dump())

        return result

    def get_watching_status_bulk(
        self, task_ids: list[str], user_id: str
    ) -> dict[str, bool]:
        """
        Check which tasks a user is watching from a list.
        Returns a dict of {task_id: True} for tasks being watched.
        """
        if not task_ids or not user_id:
            return {}

        rows = (
            self.db.query(TaskWatcher.task_id)
            .filter(
                TaskWatcher.task_id.in_(task_ids),
                TaskWatcher.user_id == user_id,
                TaskWatcher.deleted_at.is_(None),
            )
            .all()
        )
        return {row.task_id: True for row in rows}

    def get_watched_task_ids(self, user_id: str) -> list[str]:
        """Return all task IDs that a user is actively watching."""
        rows = (
            self.db.query(TaskWatcher.task_id)
            .filter(
                TaskWatcher.user_id == user_id,
                TaskWatcher.deleted_at.is_(None),
            )
            .all()
        )
        return [row.task_id for row in rows]

    def bulk_watch(self, task_id: str, user_ids: list[str]) -> int:
        """
        Add multiple watchers to a task at once.
        Skips users already watching. Returns count of newly added watchers.
        """
        added = 0
        for user_id in user_ids:
            existing = (
                self.db.query(TaskWatcher)
                .filter(
                    TaskWatcher.task_id == task_id,
                    TaskWatcher.user_id == user_id,
                )
                .first()
            )
            if existing:
                if existing.deleted_at is not None:
                    existing.deleted_at = None
                    added += 1
            else:
                self.db.add(TaskWatcher(task_id=task_id, user_id=user_id))
                added += 1

        if added:
            self.db.commit()
        return added
