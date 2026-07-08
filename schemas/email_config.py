"""Pydantic schemas for the email configuration API."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, field_validator


class EmailConfigCreate(BaseModel):
    """Input schema for creating / updating email configuration."""

    sender_email: EmailStr
    sender_name: str
    smtp_host: str
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None  # plaintext in; encrypted at rest
    encryption_type: Literal["TLS", "SSL", "NONE"] = "TLS"
    is_enabled: bool = True

    @field_validator("sender_name")
    @classmethod
    def validate_sender_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Sender name must not be empty")
        if len(v) > 200:
            raise ValueError("Sender name must not exceed 200 characters")
        return v

    @field_validator("smtp_host")
    @classmethod
    def validate_smtp_host(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("SMTP host must not be empty")
        return v

    @field_validator("smtp_port")
    @classmethod
    def validate_smtp_port(cls, v: int) -> int:
        if not 1 <= v <= 65535:
            raise ValueError("SMTP port must be between 1 and 65535")
        return v


class EmailConfigResponse(BaseModel):
    """Output schema — password is always masked."""

    id: str
    sender_email: str
    sender_name: str
    smtp_host: str
    smtp_port: int
    smtp_username: Optional[str] = None
    smtp_password: str = "••••••••"  # never expose real password
    encryption_type: str
    is_enabled: bool
    is_active: bool
    last_tested_at: Optional[datetime] = None
    last_test_status: Optional[str] = None
    last_test_error: Optional[str] = None
    configured_by_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EmailConfigTestRequest(BaseModel):
    """Input schema for testing SMTP connection."""

    sender_email: EmailStr
    sender_name: str
    smtp_host: str
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    encryption_type: Literal["TLS", "SSL", "NONE"] = "TLS"
    test_recipient: EmailStr


class EmailConfigTestResponse(BaseModel):
    """Result of an SMTP test."""

    success: bool
    message: str


class EmailConfigToggle(BaseModel):
    """Toggle the email service on/off."""

    is_enabled: bool


class EmailConfigHistoryItem(BaseModel):
    """Single entry in the configuration change history."""

    id: str
    sender_email: str
    sender_name: str
    smtp_host: str
    smtp_port: int
    encryption_type: str
    is_enabled: bool
    is_active: bool
    configured_by_name: Optional[str] = None
    created_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EmailConfigHistoryResponse(BaseModel):
    """List of historical configurations."""

    configurations: list[EmailConfigHistoryItem]
