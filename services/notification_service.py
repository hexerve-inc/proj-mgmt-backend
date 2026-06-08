"""
Central notification service — the single entry point for all notification logic.

Responsibilities:
    1. Resolve recipients for each event (assignees, team members, etc.)
    2. Check each recipient's notification preferences
    3. Enforce deduplication via idempotency keys
    4. Render email templates
    5. Dispatch emails via the configured transport
    6. Log every attempt (sent / failed / skipped) for audit

All email dispatch happens asynchronously — this service is called
from FastAPI BackgroundTasks so it never blocks API responses.
"""

import hashlib
import logging
import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import func

from core.config import settings
from models.notification_preference import NotificationEventType, NotificationPreference
from models.notification_log import NotificationLog
from models.user import User
from models.task import Task
from models.project import Project
from models.team import Team, team_members
from models.sprint import Sprint
from schemas.notification import EVENT_TYPE_METADATA
from services.notification_events import NotificationEvent
from services.email_transport import EmailTransport
from services.email_templates import EmailTemplateEngine

logger = logging.getLogger("notification.service")

# Rate limit: max emails per user per hour
MAX_EMAILS_PER_USER_PER_HOUR = 50

# Deduplication window in seconds (5 minutes)
DEDUP_WINDOW_SECONDS = 300


class NotificationService:
    """Centralized notification orchestrator."""

    def __init__(self, db: Session):
        self.db = db
        self.transport = EmailTransport.get_transport()
        self.template_engine = EmailTemplateEngine()

    # ── Public API ───────────────────────────────────────────────

    async def emit(self, event: NotificationEvent) -> None:
        """
        Main dispatch method. Resolves recipients, checks preferences,
        renders templates, and sends emails asynchronously.
        """
        try:
            recipients = self._resolve_recipients(event)

            # Remove the actor (never self-notify)
            recipients = [r for r in recipients if r.id != event.actor_id]

            if not recipients:
                logger.debug(f"No recipients for {event.event_type.value} on {event.entity_id}")
                return

            # Resolve actor name for templates
            actor = self.db.query(User).filter(User.id == event.actor_id).first()
            actor_name = actor.name if actor else "Someone"

            # Resolve project name for templates
            project = self.db.query(Project).filter(Project.id == event.project_id).first()
            project_name = project.name if project else "Unknown Project"

            for recipient in recipients:
                await self._process_for_recipient(
                    event=event,
                    recipient=recipient,
                    actor_name=actor_name,
                    project_name=project_name,
                )

        except Exception as e:
            logger.error(f"Notification emit failed for {event.event_type.value}: {e}", exc_info=True)

    def emit_sync(self, event: NotificationEvent) -> None:
        """Synchronous wrapper for calling emit from BackgroundTasks."""
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(self.emit(event))
        finally:
            loop.close()

    # ── Preference Management ────────────────────────────────────

    def get_user_preferences(self, user_id: str) -> list[dict]:
        """
        Return all notification preferences for a user.
        Missing rows default to email_enabled=True.
        """
        # Load existing preferences
        existing = (
            self.db.query(NotificationPreference)
            .filter(
                NotificationPreference.user_id == user_id,
                NotificationPreference.deleted_at.is_(None),
            )
            .all()
        )
        existing_map = {p.event_type.value: p.email_enabled for p in existing}

        result = []
        for event_type in NotificationEventType:
            meta = EVENT_TYPE_METADATA.get(event_type.value, {})
            result.append({
                "event_type": event_type.value,
                "email_enabled": existing_map.get(event_type.value, True),  # default ON
                "label": meta.get("label", event_type.value),
                "description": meta.get("description", ""),
                "category": meta.get("category", "Other"),
            })

        return result

    def update_user_preferences(
        self, user_id: str, updates: list[dict]
    ) -> list[dict]:
        """
        Batch-update notification preferences.
        Creates rows that don't exist yet (upsert).
        """
        for item in updates:
            event_type = item["event_type"]
            email_enabled = item["email_enabled"]

            existing = (
                self.db.query(NotificationPreference)
                .filter(
                    NotificationPreference.user_id == user_id,
                    NotificationPreference.event_type == event_type,
                    NotificationPreference.deleted_at.is_(None),
                )
                .first()
            )

            if existing:
                existing.email_enabled = email_enabled
            else:
                pref = NotificationPreference(
                    user_id=user_id,
                    event_type=event_type,
                    email_enabled=email_enabled,
                )
                self.db.add(pref)

        self.db.commit()
        return self.get_user_preferences(user_id)

    # ── Internal: per-recipient processing ───────────────────────

    async def _process_for_recipient(
        self,
        event: NotificationEvent,
        recipient: User,
        actor_name: str,
        project_name: str,
    ) -> None:
        """Check preferences, deduplicate, render, send, and log for one recipient."""

        # 1. Check preference
        if not self._should_notify(recipient.id, event.event_type):
            logger.debug(f"Skipped {event.event_type.value} for {recipient.email} (preference disabled)")
            return

        # 2. Check rate limit
        if self._is_rate_limited(recipient.id):
            logger.warning(f"Rate limited: {recipient.email}")
            return

        # 3. Generate idempotency key and check dedup
        idemp_key = self._generate_idempotency_key(
            recipient.id, event.event_type.value, event.entity_id
        )
        if self._is_duplicate(idemp_key):
            logger.debug(f"Duplicate notification skipped: {idemp_key}")
            return

        # 4. Build template context
        context = {
            "actor_name": actor_name,
            "project_name": project_name,
            "task_id": event.entity_id if event.entity_type == "task" else None,
            **event.metadata,
        }

        # 5. Render email
        subject, html_body, text_body = self.template_engine.render(
            event.event_type.value, context
        )

        # 6. Send via transport
        status = "sent"
        error_message = None
        try:
            await self.transport.send(
                to=recipient.email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
            )
        except Exception as e:
            status = "failed"
            error_message = str(e)
            logger.error(f"Failed to send to {recipient.email}: {e}")

        # 7. Log result
        self._log_notification(
            user_id=recipient.id,
            event_type=event.event_type.value,
            entity_id=event.entity_id,
            entity_type=event.entity_type,
            email_to=recipient.email,
            email_subject=subject,
            status=status,
            error_message=error_message,
            idempotency_key=idemp_key,
        )

    # ── Recipient Resolution ─────────────────────────────────────

    def _resolve_recipients(self, event: NotificationEvent) -> list[User]:
        """
        Determine who should receive a notification for this event.
        Returns a list of User objects.
        """
        recipients: list[User] = []

        if event.event_type == NotificationEventType.TASK_ASSIGNED:
            # Notify only the newly assigned user
            assignee_id = event.metadata.get("assignee_id")
            if assignee_id:
                user = self._get_user(assignee_id)
                if user:
                    recipients.append(user)

        elif event.event_type == NotificationEventType.TASK_REASSIGNED:
            # Notify both old and new assignee
            for key in ("old_assignee_id", "new_assignee_id"):
                uid = event.metadata.get(key)
                if uid:
                    user = self._get_user(uid)
                    if user:
                        recipients.append(user)

        elif event.event_type in (
            NotificationEventType.TASK_DETAILS_UPDATED,
            NotificationEventType.TASK_PRIORITY_CHANGED,
            NotificationEventType.TASK_DUE_DATE_CHANGED,
            NotificationEventType.TASK_DELETED,
        ):
            # Notify the task assignee only
            assignee = self._get_task_assignee(event.entity_id)
            if assignee:
                recipients.append(assignee)

        elif event.event_type in (
            NotificationEventType.TASK_CREATED,
            NotificationEventType.TASK_STATUS_CHANGED,
            NotificationEventType.TASK_SPRINT_CHANGED,
            NotificationEventType.SPRINT_STARTED,
            NotificationEventType.SPRINT_COMPLETED,
            NotificationEventType.PROJECT_STATUS_CHANGED,
        ):
            # Notify all project team members
            team_users = self._get_project_team_members(event.project_id)
            recipients.extend(team_users)

            # Also add task assignee for task-level events
            if event.entity_type == "task":
                assignee = self._get_task_assignee(event.entity_id)
                if assignee and assignee not in recipients:
                    recipients.append(assignee)

        elif event.event_type in (
            NotificationEventType.TASK_COMMENT_ADDED,
            NotificationEventType.TASK_COMMENT_MENTION,
        ):
            # Future: notify task assignee + mentioned users
            assignee = self._get_task_assignee(event.entity_id)
            if assignee:
                recipients.append(assignee)

            # For mentions, also include the mentioned user
            mentioned_id = event.metadata.get("mentioned_user_id")
            if mentioned_id:
                user = self._get_user(mentioned_id)
                if user and user not in recipients:
                    recipients.append(user)

        # Deduplicate by user ID
        seen = set()
        unique = []
        for u in recipients:
            if u.id not in seen:
                seen.add(u.id)
                unique.append(u)

        return unique

    # ── Preference Check ─────────────────────────────────────────

    def _should_notify(self, user_id: str, event_type: NotificationEventType) -> bool:
        """Check if a user has this notification type enabled."""
        pref = (
            self.db.query(NotificationPreference)
            .filter(
                NotificationPreference.user_id == user_id,
                NotificationPreference.event_type == event_type,
                NotificationPreference.deleted_at.is_(None),
            )
            .first()
        )
        # If no preference row exists, default to enabled
        if pref is None:
            return True
        return pref.email_enabled

    # ── Deduplication ────────────────────────────────────────────

    def _generate_idempotency_key(
        self, user_id: str, event_type: str, entity_id: str
    ) -> str:
        """Generate a dedup key scoped to a 5-minute window."""
        now = datetime.now(timezone.utc)
        bucket = int(now.timestamp()) // DEDUP_WINDOW_SECONDS
        raw = f"{user_id}:{event_type}:{entity_id}:{bucket}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def _is_duplicate(self, idempotency_key: str) -> bool:
        """Check if a notification with this key was already sent."""
        return (
            self.db.query(NotificationLog)
            .filter(NotificationLog.idempotency_key == idempotency_key)
            .first()
            is not None
        )

    # ── Rate Limiting ────────────────────────────────────────────

    def _is_rate_limited(self, user_id: str) -> bool:
        """Check if user exceeded max emails per hour."""
        from datetime import timedelta

        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        count = (
            self.db.query(func.count(NotificationLog.id))
            .filter(
                NotificationLog.user_id == user_id,
                NotificationLog.status == "sent",
                NotificationLog.created_at >= one_hour_ago,
            )
            .scalar()
        )
        return (count or 0) >= MAX_EMAILS_PER_USER_PER_HOUR

    # ── Logging ──────────────────────────────────────────────────

    def _log_notification(self, **kwargs) -> None:
        """Record a notification attempt in the log table."""
        try:
            log_entry = NotificationLog(id=str(uuid.uuid4()), **kwargs)
            self.db.add(log_entry)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log notification: {e}")
            self.db.rollback()

    # ── DB Helpers ───────────────────────────────────────────────

    def _get_user(self, user_id: str):
        return (
            self.db.query(User)
            .filter(User.id == user_id, User.deleted_at.is_(None))
            .first()
        )

    def _get_task_assignee(self, task_id: str):
        task = (
            self.db.query(Task)
            .filter(Task.id == task_id, Task.deleted_at.is_(None))
            .first()
        )
        if task and task.assignee_id:
            return self._get_user(task.assignee_id)
        return None

    def _get_project_team_members(self, project_id: str) -> list[User]:
        """Get all team members for the project's team."""
        project = (
            self.db.query(Project)
            .filter(Project.id == project_id, Project.deleted_at.is_(None))
            .first()
        )
        if not project or not project.team_id:
            return []

        team = (
            self.db.query(Team)
            .filter(Team.id == project.team_id, Team.deleted_at.is_(None))
            .first()
        )
        if not team:
            return []

        return list(team.members)
