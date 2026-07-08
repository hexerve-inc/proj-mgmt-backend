"""
Provider-agnostic email transport layer.

The system ships with two transports:
    • SMTPTransport  – sends via aiosmtplib (async, like Nodemailer)
    • ConsoleTransport – prints the email to stdout (dev/test mode)

Adding a new provider (SendGrid, SES, Resend) is a matter of
subclassing EmailTransportBase and selecting it in EmailTransport.

Dynamic Configuration:
    The transport layer now supports fetching SMTP parameters
    dynamically from the database (via EmailConfigService) on
    each call.  If no DB configuration exists, it falls back to
    the environment variables defined in core/config.py.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from core.config import settings

logger = logging.getLogger("notification.transport")


class EmailTransportBase(ABC):
    """Abstract base class for all email transports."""

    @abstractmethod
    async def send(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: str,
    ) -> bool:
        """Send an email. Return True on success, False on failure."""
        ...


class SMTPTransport(EmailTransportBase):
    """Async SMTP delivery via aiosmtplib.

    Accepts SMTP parameters either from constructor kwargs
    (DB-driven) or falls back to settings.* (env-driven).
    """

    def __init__(
        self,
        *,
        sender_email: Optional[str] = None,
        sender_name: Optional[str] = None,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        encryption_type: Optional[str] = None,
    ):
        self._sender_email = sender_email or settings.SMTP_FROM_EMAIL
        self._sender_name = sender_name or settings.SMTP_FROM_NAME
        self._smtp_host = smtp_host or settings.SMTP_HOST
        self._smtp_port = smtp_port or settings.SMTP_PORT
        self._smtp_username = smtp_username or settings.SMTP_USERNAME
        self._smtp_password = smtp_password or settings.SMTP_PASSWORD
        self._encryption_type = encryption_type  # TLS | SSL | NONE

    async def send(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: str,
    ) -> bool:
        import aiosmtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart("alternative")
        msg["From"] = f"{self._sender_name} <{self._sender_email}>"
        msg["To"] = to
        msg["Subject"] = subject

        # Plain text fallback
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        # HTML version (preferred by clients)
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # Determine TLS mode
        if self._encryption_type:
            use_tls = self._encryption_type == "SSL"
            start_tls = self._encryption_type == "TLS"
        else:
            # Legacy env-var mode
            use_tls = settings.SMTP_USE_TLS
            start_tls = not settings.SMTP_USE_TLS

        try:
            await aiosmtplib.send(
                msg,
                hostname=self._smtp_host,
                port=self._smtp_port,
                username=self._smtp_username or None,
                password=self._smtp_password or None,
                use_tls=use_tls,
                start_tls=start_tls,
            )
            logger.info(f"Email sent to {to}: {subject}")
            return True
        except Exception as e:
            logger.error(f"SMTP send failed for {to}: {e}")
            raise


class ConsoleTransport(EmailTransportBase):
    """Development transport — logs email content to stdout/logger."""

    async def send(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: str,
    ) -> bool:
        logger.info(
            f"\n{'='*60}\n"
            f"📧 EMAIL (console mode — not actually sent)\n"
            f"   To:      {to}\n"
            f"   Subject: {subject}\n"
            f"{'─'*60}\n"
            f"{text_body}\n"
            f"{'='*60}\n"
        )
        return True


# ── Future provider stubs ────────────────────────────────────────
# class SendGridTransport(EmailTransportBase): ...
# class SESTransport(EmailTransportBase): ...
# class ResendTransport(EmailTransportBase): ...


class EmailTransport:
    """Factory that selects the appropriate transport based on config.

    Resolution order:
        1. Check for an active DB email configuration
        2. Fall back to environment variables in core/config.py
        3. Use ConsoleTransport if email is not properly configured
    """

    @staticmethod
    def get_transport(db=None) -> EmailTransportBase:
        """Build the transport using the best available configuration.

        Args:
            db: Optional SQLAlchemy Session.  When provided, the factory
                checks the database for an active EmailConfiguration.
        """
        # ── Try DB configuration first ──────────────────────────
        if db is not None:
            try:
                from services.email_config_service import EmailConfigService

                service = EmailConfigService(db)
                params = service.get_active_smtp_params()

                if params:
                    if not params.get("smtp_host"):
                        logger.warning(
                            "DB email config has no smtp_host — falling back to ConsoleTransport"
                        )
                        return ConsoleTransport()

                    return SMTPTransport(
                        sender_email=params["sender_email"],
                        sender_name=params["sender_name"],
                        smtp_host=params["smtp_host"],
                        smtp_port=params["smtp_port"],
                        smtp_username=params.get("smtp_username"),
                        smtp_password=params.get("smtp_password"),
                        encryption_type=params.get("encryption_type"),
                    )
            except Exception as e:
                logger.error(f"Failed to load DB email config: {e}")
                # Fall through to env-var path

        # ── Fall back to environment variables ──────────────────
        if not settings.EMAIL_ENABLED:
            return ConsoleTransport()
        if not settings.SMTP_HOST:
            logger.warning("EMAIL_ENABLED=True but SMTP_HOST is empty — falling back to ConsoleTransport")
            return ConsoleTransport()
        return SMTPTransport()
