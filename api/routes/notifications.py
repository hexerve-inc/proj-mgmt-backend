"""
API endpoints for managing email notification preferences.

GET  /users/me/notification-preferences  — list all preferences with defaults
PUT  /users/me/notification-preferences  — batch-update preferences
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import get_db, get_current_user
from models.user import User
from schemas.notification import (
    NotificationPreferencesListResponse,
    NotificationPreferencesUpdate,
    NotificationPreferenceResponse,
)
from services.notification_service import NotificationService

router = APIRouter()


@router.get("/me/notification-preferences", response_model=NotificationPreferencesListResponse)
def get_notification_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all notification preferences for the current user.

    Preferences that have never been configured default to enabled.
    The response includes human-readable labels, descriptions, and
    category groupings for frontend rendering.
    """
    service = NotificationService(db)
    prefs = service.get_user_preferences(current_user.id)
    return NotificationPreferencesListResponse(
        preferences=[NotificationPreferenceResponse(**p) for p in prefs]
    )


@router.put("/me/notification-preferences", response_model=NotificationPreferencesListResponse)
def update_notification_preferences(
    body: NotificationPreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Batch-update notification preferences for the current user.

    Accepts a list of {event_type, email_enabled} items. Only the
    provided event types are updated — others remain unchanged.
    """
    service = NotificationService(db)
    updates = [{"event_type": p.event_type, "email_enabled": p.email_enabled} for p in body.preferences]
    prefs = service.update_user_preferences(current_user.id, updates)
    return NotificationPreferencesListResponse(
        preferences=[NotificationPreferenceResponse(**p) for p in prefs]
    )
