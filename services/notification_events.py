"""
Typed event payloads for the notification system.

Every notification begins as a NotificationEvent dataclass that
captures who did what, to which entity, in which project, and
any event-specific metadata (old/new values, etc.).
"""

from dataclasses import dataclass, field
from models.notification_preference import NotificationEventType


@dataclass
class NotificationEvent:
    """Immutable event payload passed to NotificationService.emit()."""

    event_type: NotificationEventType
    actor_id: str               # User who triggered the event
    entity_id: str              # Task / Sprint / Project ID
    entity_type: str            # "task", "sprint", "project"
    project_id: str             # For recipient resolution
    metadata: dict = field(default_factory=dict)
    # metadata examples:
    #   TASK_STATUS_CHANGED  → {"old_status": "Open", "new_status": "In Progress", "task_code": "PRO-12", "task_title": "..."}
    #   TASK_ASSIGNED        → {"assignee_id": "...", "assignee_name": "...", "task_code": "PRO-12", "task_title": "..."}
    #   TASK_REASSIGNED      → {"old_assignee_id": "...", "new_assignee_id": "...", ...}
    #   TASK_SPRINT_CHANGED  → {"old_sprint": "Sprint 1", "new_sprint": "Sprint 2", ...}
    #   SPRINT_STARTED       → {"sprint_name": "Sprint 3", ...}
