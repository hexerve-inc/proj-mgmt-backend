"""
API routes for managing outgoing email (SMTP) configuration.

All endpoints are guarded by RBAC — only users with ``settings:update``
(or ``settings:read`` for GET) can access them.

Endpoints:
    GET    /settings/email-config          — current active config (masked password)
    PUT    /settings/email-config          — create / update active config
    POST   /settings/email-config/test     — test SMTP connection + send test email
    GET    /settings/email-config/history  — configuration change history
    PATCH  /settings/email-config/toggle   — enable / disable email service
"""

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_db, get_current_user, require_permission
from models.user import User
from schemas.email_config import (
    EmailConfigCreate,
    EmailConfigResponse,
    EmailConfigTestRequest,
    EmailConfigTestResponse,
    EmailConfigToggle,
    EmailConfigHistoryItem,
    EmailConfigHistoryResponse,
)
from services.email_config_service import EmailConfigService

logger = logging.getLogger("email_config.routes")

router = APIRouter()


def _config_to_response(config, db: Session) -> EmailConfigResponse:
    """Map an EmailConfiguration ORM object to the API response schema."""
    configured_by_name = None
    if config.configured_by_id:
        user = db.query(User).filter(User.id == config.configured_by_id).first()
        if user:
            configured_by_name = user.name

    return EmailConfigResponse(
        id=config.id,
        sender_email=config.sender_email,
        sender_name=config.sender_name,
        smtp_host=config.smtp_host,
        smtp_port=config.smtp_port,
        smtp_username=config.smtp_username,
        smtp_password="••••••••" if config.smtp_password_encrypted else "",
        encryption_type=config.encryption_type,
        is_enabled=config.is_enabled,
        is_active=config.is_active,
        last_tested_at=config.last_tested_at,
        last_test_status=config.last_test_status,
        last_test_error=config.last_test_error,
        configured_by_name=configured_by_name,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


# ── GET active config ────────────────────────────────────────────

@router.get(
    "/email-config",
    response_model=EmailConfigResponse,
    dependencies=[Depends(require_permission("settings:read"))],
)
def get_email_config(
    db: Session = Depends(get_db),
):
    """Return the current active email configuration (password masked)."""
    service = EmailConfigService(db)
    config = service.get_active_config()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No email configuration found. Please configure SMTP settings.",
        )
    return _config_to_response(config, db)


# ── PUT create / update config ───────────────────────────────────

@router.put(
    "/email-config",
    response_model=EmailConfigResponse,
    dependencies=[Depends(require_permission("settings:update"))],
)
def update_email_config(
    body: EmailConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create or update the active email configuration.

    Deactivates the previous configuration and creates a new active one.
    If the password field contains the masked placeholder, the previous
    password is carried forward.
    """
    service = EmailConfigService(db)
    config = service.create_or_update_config(
        sender_email=body.sender_email,
        sender_name=body.sender_name,
        smtp_host=body.smtp_host,
        smtp_port=body.smtp_port,
        smtp_username=body.smtp_username,
        smtp_password=body.smtp_password,
        encryption_type=body.encryption_type,
        is_enabled=body.is_enabled,
        user_id=current_user.id,
    )
    return _config_to_response(config, db)


# ── POST test SMTP connection ───────────────────────────────────

@router.post(
    "/email-config/test",
    response_model=EmailConfigTestResponse,
    dependencies=[Depends(require_permission("settings:update"))],
)
def test_email_config(
    body: EmailConfigTestRequest,
    db: Session = Depends(get_db),
):
    """Test SMTP connection by sending a test email.

    Does not persist the configuration. Returns success/failure
    with a descriptive message.
    """
    service = EmailConfigService(db)

    # Run the async SMTP test in a synchronous context
    loop = asyncio.new_event_loop()
    try:
        success, message = loop.run_until_complete(
            service.test_smtp_connection(
                sender_email=body.sender_email,
                sender_name=body.sender_name,
                smtp_host=body.smtp_host,
                smtp_port=body.smtp_port,
                smtp_username=body.smtp_username,
                smtp_password=body.smtp_password,
                encryption_type=body.encryption_type,
                test_recipient=body.test_recipient,
            )
        )
    finally:
        loop.close()

    # If there's an active config, record the test result
    active = service.get_active_config()
    if active:
        service.update_test_result(active.id, success=success, error=message if not success else None)

    return EmailConfigTestResponse(success=success, message=message)


# ── GET config history ───────────────────────────────────────────

@router.get(
    "/email-config/history",
    response_model=EmailConfigHistoryResponse,
    dependencies=[Depends(require_permission("settings:read"))],
)
def get_email_config_history(
    db: Session = Depends(get_db),
):
    """Return the configuration change history (active + previous)."""
    service = EmailConfigService(db)
    configs = service.get_config_history()

    items = []
    for cfg in configs:
        configured_by_name = None
        if cfg.configured_by_id:
            user = db.query(User).filter(User.id == cfg.configured_by_id).first()
            if user:
                configured_by_name = user.name

        items.append(
            EmailConfigHistoryItem(
                id=cfg.id,
                sender_email=cfg.sender_email,
                sender_name=cfg.sender_name,
                smtp_host=cfg.smtp_host,
                smtp_port=cfg.smtp_port,
                encryption_type=cfg.encryption_type,
                is_enabled=cfg.is_enabled,
                is_active=cfg.is_active,
                configured_by_name=configured_by_name,
                created_at=cfg.created_at,
                deleted_at=cfg.deleted_at,
            )
        )

    return EmailConfigHistoryResponse(configurations=items)


# ── PATCH toggle email service ───────────────────────────────────

@router.patch(
    "/email-config/toggle",
    response_model=EmailConfigResponse,
    dependencies=[Depends(require_permission("settings:update"))],
)
def toggle_email_service(
    body: EmailConfigToggle,
    db: Session = Depends(get_db),
):
    """Enable or disable the email service."""
    service = EmailConfigService(db)
    config = service.toggle_email_service(body.is_enabled)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active email configuration to toggle.",
        )
    return _config_to_response(config, db)
