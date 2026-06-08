"""
Provider-agnostic email transport layer.

The system ships with two transports:
    • SMTPTransport  – sends via aiosmtplib (async, like Nodemailer)
    • ConsoleTransport – prints the email to stdout (dev/test mode)

Adding a new provider (SendGrid, SES, Resend) is a matter of
subclassing EmailTransportBase and selecting it in EmailTransport.
"""

import logging
from abc import ABC, abstractmethod

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
    """Async SMTP delivery via aiosmtplib."""

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
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg["To"] = to
        msg["Subject"] = subject

        # Plain text fallback
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        # HTML version (preferred by clients)
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME or None,
                password=settings.SMTP_PASSWORD or None,
                use_tls=settings.SMTP_USE_TLS,
                start_tls=not settings.SMTP_USE_TLS,
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
    """Factory that selects the appropriate transport based on config."""

    @staticmethod
    def get_transport() -> EmailTransportBase:
        if not settings.EMAIL_ENABLED:
            return ConsoleTransport()
        if not settings.SMTP_HOST:
            logger.warning("EMAIL_ENABLED=True but SMTP_HOST is empty — falling back to ConsoleTransport")
            return ConsoleTransport()
        return SMTPTransport()
