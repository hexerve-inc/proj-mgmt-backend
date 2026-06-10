"""Pydantic schemas for notification preference API endpoints."""

from pydantic import BaseModel
from typing import Optional
from models.notification_preference import NotificationEventType


# ── Human-readable metadata for each event type ────────────────────

EVENT_TYPE_METADATA: dict[str, dict[str, str]] = {
    "TASK_CREATED": {
        "label": "Task Created",
        "description": "Notify me when a new task is created in my project",
        "category": "Tasks",
    },
    "TASK_STATUS_CHANGED": {
        "label": "Task Status Changed",
        "description": "Notify me when a task's status is updated",
        "category": "Tasks",
    },
    "TASK_ASSIGNED": {
        "label": "Task Assigned",
        "description": "Notify me when I am assigned a task",
        "category": "Tasks",
    },
    "TASK_REASSIGNED": {
        "label": "Task Reassigned",
        "description": "Notify me when a task I'm assigned to is reassigned",
        "category": "Tasks",
    },
    "TASK_DETAILS_UPDATED": {
        "label": "Task Details Updated",
        "description": "Notify me when task title, description, or story points are modified",
        "category": "Tasks",
    },
    "TASK_DELETED": {
        "label": "Task Deleted",
        "description": "Notify me when a task is deleted from my project",
        "category": "Tasks",
    },
    "TASK_PRIORITY_CHANGED": {
        "label": "Task Priority Changed",
        "description": "Notify me when a task's priority level changes",
        "category": "Tasks",
    },
    "TASK_DUE_DATE_CHANGED": {
        "label": "Task Due Date Changed",
        "description": "Notify me when a task's due date is modified",
        "category": "Tasks",
    },
    "TASK_SPRINT_CHANGED": {
        "label": "Task Moved Between Sprints",
        "description": "Notify me when a task is moved to a different sprint",
        "category": "Tasks",
    },
    "TASK_COMMENT_ADDED": {
        "label": "Comment Added",
        "description": "Notify me when someone comments on my task",
        "category": "Comments",
    },
    "TASK_COMMENT_MENTION": {
        "label": "Mentioned in Comment",
        "description": "Notify me when I am @mentioned in a comment",
        "category": "Comments",
    },
    "SPRINT_STARTED": {
        "label": "Sprint Started",
        "description": "Notify me when a sprint begins",
        "category": "Sprints",
    },
    "SPRINT_COMPLETED": {
        "label": "Sprint Completed",
        "description": "Notify me when a sprint is completed",
        "category": "Sprints",
    },
    "PROJECT_STATUS_CHANGED": {
        "label": "Project Status Changed",
        "description": "Notify me when a project's status transitions",
        "category": "Projects",
    },
}


class NotificationPreferenceItem(BaseModel):
    event_type: NotificationEventType
    email_enabled: bool


class NotificationPreferenceResponse(BaseModel):
    event_type: str
    email_enabled: bool
    label: str
    description: str
    category: str

    class Config:
        from_attributes = True


class NotificationPreferencesListResponse(BaseModel):
    preferences: list[NotificationPreferenceResponse]


class NotificationPreferencesUpdate(BaseModel):
    preferences: list[NotificationPreferenceItem]
