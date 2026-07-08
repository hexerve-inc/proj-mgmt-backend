"""
Business-logic service for managing outgoing email (SMTP) configuration.

Responsibilities:
    - CRUD for EmailConfiguration records
    - Encrypt / decrypt SMTP passwords via Fernet
    - Ensure only one configuration is active at a time
    - Test SMTP connectivity without persisting
    - Provide the active config to the email transport layer
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from core.security import encrypt_value, decrypt_value
from models.email_configuration import EmailConfiguration
from models.user import User

logger = logging.getLogger("email_config.service")


class EmailConfigService:
    """Centralized email configuration management."""

    def __init__(self, db: Session):
        self.db = db

    # ── Read ─────────────────────────────────────────────────────

    def get_active_config(self) -> Optional[EmailConfiguration]:
        """Return the single active email configuration, or None."""
        return (
            self.db.query(EmailConfiguration)
            .filter(
                EmailConfiguration.is_active.is_(True),
                EmailConfiguration.deleted_at.is_(None),
            )
            .first()
        )

    def get_config_by_id(self, config_id: str) -> Optional[EmailConfiguration]:
        """Fetch a configuration by ID."""
        return (
            self.db.query(EmailConfiguration)
            .filter(
                EmailConfiguration.id == config_id,
                EmailConfiguration.deleted_at.is_(None),
            )
            .first()
        )

    def get_config_history(self) -> list[EmailConfiguration]:
        """Return all configurations (active + soft-deleted) for audit."""
        return (
            self.db.query(EmailConfiguration)
            .order_by(EmailConfiguration.created_at.desc())
            .all()
        )

    # ── Write ────────────────────────────────────────────────────

    def create_or_update_config(
        self,
        *,
        sender_email: str,
        sender_name: str,
        smtp_host: str,
        smtp_port: int,
        smtp_username: Optional[str],
        smtp_password: Optional[str],
        encryption_type: str,
        is_enabled: bool,
        user_id: str,
    ) -> EmailConfiguration:
        """Create a new active configuration, deactivating any previous one.

        If smtp_password is the masked placeholder '••••••••' and a previous
        config exists, the old encrypted password is carried forward.
        """
        # Deactivate current active config
        current = self.get_active_config()
        carry_password: Optional[str] = None

        if current:
            # Carry forward the old password if the user didn't supply a new one
            if smtp_password in (None, "", "••••••••"):
                carry_password = current.smtp_password_encrypted

            current.is_active = False
            current.soft_delete()

        # Encrypt password
        encrypted_password = carry_password
        if smtp_password and smtp_password != "••••••••":
            encrypted_password = encrypt_value(smtp_password)

        new_config = EmailConfiguration(
            id=str(uuid.uuid4()),
            sender_email=sender_email,
            sender_name=sender_name,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password_encrypted=encrypted_password,
            encryption_type=encryption_type,
            is_enabled=is_enabled,
            is_active=True,
            configured_by_id=user_id,
        )

        self.db.add(new_config)
        self.db.commit()
        self.db.refresh(new_config)

        logger.info(
            f"Email config updated by user {user_id}: "
            f"sender={sender_email}, host={smtp_host}:{smtp_port}"
        )
        return new_config

    def toggle_email_service(self, enabled: bool) -> Optional[EmailConfiguration]:
        """Enable or disable the email service on the active config."""
        config = self.get_active_config()
        if not config:
            return None
        config.is_enabled = enabled
        self.db.commit()
        self.db.refresh(config)
        logger.info(f"Email service {'enabled' if enabled else 'disabled'}")
        return config

    def update_test_result(
        self,
        config_id: str,
        *,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """Record the result of an SMTP connection test."""
        config = self.get_config_by_id(config_id)
        if config:
            config.last_tested_at = datetime.now(timezone.utc)
            config.last_test_status = "success" if success else "failed"
            config.last_test_error = error
            self.db.commit()

    # ── SMTP test (does NOT persist config) ──────────────────────

    async def test_smtp_connection(
        self,
        *,
        sender_email: str,
        sender_name: str,
        smtp_host: str,
        smtp_port: int,
        smtp_username: Optional[str],
        smtp_password: Optional[str],
        encryption_type: str,
        test_recipient: str,
    ) -> tuple[bool, str]:
        """Attempt to connect to the SMTP server and send a test email.

        Returns (success: bool, message: str).
        """
        import aiosmtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        # If password is masked, try to use the stored one
        actual_password = smtp_password
        if smtp_password in (None, "", "••••••••"):
            current = self.get_active_config()
            if current and current.smtp_password_encrypted:
                try:
                    actual_password = decrypt_value(current.smtp_password_encrypted)
                except Exception:
                    actual_password = None

        msg = MIMEMultipart("alternative")
        msg["From"] = f"{sender_name} <{sender_email}>"
        msg["To"] = test_recipient
        msg["Subject"] = f"[{sender_name}] SMTP Test — Connection Verified ✓"

        text = (
            f"This is a test email from {sender_name}.\n\n"
            "If you received this message, your SMTP configuration is working correctly.\n\n"
            f"Server: {smtp_host}:{smtp_port}\n"
            f"Encryption: {encryption_type}\n"
        )
        html = (
            f"<div style='font-family:Inter,sans-serif;padding:32px;max-width:500px;margin:0 auto;'>"
            f"<div style='background:linear-gradient(135deg,#6366f1,#4f46e5);padding:24px;border-radius:12px 12px 0 0;text-align:center;'>"
            f"<h1 style='color:#fff;margin:0;font-size:20px;'>✓ SMTP Test Successful</h1>"
            f"</div>"
            f"<div style='background:#fff;padding:24px;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 12px 12px;'>"
            f"<p style='color:#334155;'>This is a test email from <strong>{sender_name}</strong>.</p>"
            f"<p style='color:#334155;'>Your SMTP configuration is working correctly.</p>"
            f"<div style='background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:16px;margin-top:16px;'>"
            f"<p style='margin:0;color:#64748b;font-size:13px;'><strong>Server:</strong> {smtp_host}:{smtp_port}</p>"
            f"<p style='margin:4px 0 0;color:#64748b;font-size:13px;'><strong>Encryption:</strong> {encryption_type}</p>"
            f"</div>"
            f"</div></div>"
        )

        msg.attach(MIMEText(text, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))

        use_tls = encryption_type == "SSL"
        start_tls = encryption_type == "TLS"

        try:
            await aiosmtplib.send(
                msg,
                hostname=smtp_host,
                port=smtp_port,
                username=smtp_username or None,
                password=actual_password or None,
                use_tls=use_tls,
                start_tls=start_tls,
            )
            return True, f"Test email sent successfully to {test_recipient}"
        except Exception as e:
            logger.error(f"SMTP test failed: {e}")
            return False, str(e)

    # ── Helpers for transport layer ──────────────────────────────

    def get_active_smtp_params(self) -> Optional[dict]:
        """Return SMTP parameters for the active configuration.

        Returns None if no active config or if email is disabled,
        signalling the transport layer to fall back to env vars.
        """
        config = self.get_active_config()
        if not config or not config.is_enabled:
            return None

        password = None
        if config.smtp_password_encrypted:
            try:
                password = decrypt_value(config.smtp_password_encrypted)
            except Exception as e:
                logger.error(f"Failed to decrypt SMTP password: {e}")
                return None

        return {
            "sender_email": config.sender_email,
            "sender_name": config.sender_name,
            "smtp_host": config.smtp_host,
            "smtp_port": config.smtp_port,
            "smtp_username": config.smtp_username,
            "smtp_password": password,
            "encryption_type": config.encryption_type,
            "is_enabled": config.is_enabled,
        }
