"""Pydantic schemas for task watcher API endpoints."""

from pydantic import BaseModel
from typing import Optional


class WatchStatusResponse(BaseModel):
    """Response for watch/unwatch and status check endpoints."""
    watching: bool
    watcher_count: int


class TaskWatcherUserResponse(BaseModel):
    """A single watcher entry with user info and subscription date."""
    id: str
    name: str
    email: str
    watching_since: Optional[str] = None


class TaskWatchersListResponse(BaseModel):
    """Response for listing all watchers of a task."""
    watchers: list[TaskWatcherUserResponse]
    count: int
