import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from models.user import User
from models.password_reset_token import PasswordResetToken
from services.auth_service import AuthService
from services.email_transport import EmailTransport
from services.email_templates import EmailTemplateEngine
from core.security import validate_password_strength

class PasswordResetService:
    def __init__(self, db: Session):
        self.db = db
        self.template_engine = EmailTemplateEngine()

    def _generate_token(self) -> tuple[str, str]:
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        return raw_token, token_hash

    async def request_reset(self, email: str) -> None:
        user = self.db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()
        if not user:
            return  # Always return success to prevent email enumeration

        raw_token, token_hash = self._generate_token()
        
        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
        )
        self.db.add(reset_token)
        self.db.commit()

        # Send email
        await self._send_reset_email(user, raw_token)

    async def _send_reset_email(self, user: User, raw_token: str) -> None:
        context = {
            "user_name": user.name,
            "reset_url": f"{self.template_engine._env.globals.get('frontend_url', 'http://localhost:3000')}/reset-password?token={raw_token}",
            "expiry_minutes": 15
        }
        
        transport = EmailTransport.get_transport(db=self.db)
        
        # Determine sender_name from email config if available
        sender_name = None
        try:
            from services.email_config_service import EmailConfigService
            service = EmailConfigService(self.db)
            config = service.get_active_config()
            if config and config.is_enabled:
                sender_name = config.sender_name
        except Exception:
            pass

        subject, html_body, text_body = self.template_engine.render("PASSWORD_RESET", context, sender_name=sender_name)
        
        await transport.send(
            to=user.email,
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )

    def validate_token(self, raw_token: str) -> User | None:
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        token = self.db.query(PasswordResetToken).filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > datetime.now(timezone.utc)
        ).first()

        if not token:
            return None
            
        user = self.db.query(User).filter(User.id == token.user_id, User.deleted_at.is_(None)).first()
        return user

    def reset_password(self, raw_token: str, new_password: str) -> tuple[bool, str]:
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        token = self.db.query(PasswordResetToken).filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > datetime.now(timezone.utc)
        ).first()

        if not token:
            return False, "Invalid or expired reset link."

        is_valid, error_msg = validate_password_strength(new_password)
        if not is_valid:
            return False, error_msg

        auth_service = AuthService(self.db)
        from core.security import get_password_hash
        new_hashed = get_password_hash(new_password)
        
        # Note: we need to check if the new password matches the old password
        user = self.db.query(User).filter(User.id == token.user_id).first()
        from core.security import verify_password
        if verify_password(new_password, user.hashed_password):
            return False, "New password cannot be the same as current password."

        # Update password
        auth_service.update_password(token.user_id, new_hashed)
        
        # Mark token as used
        token.used_at = datetime.now(timezone.utc)
        
        # Invalidate all other unused tokens for this user
        self._invalidate_all_tokens(token.user_id)
        
        self.db.commit()
        return True, ""

    def _invalidate_all_tokens(self, user_id: str) -> None:
        self.db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used_at.is_(None)
        ).update({"expires_at": datetime.now(timezone.utc)})

    def cleanup_expired_tokens(self) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=1)
        self.db.query(PasswordResetToken).filter(
            PasswordResetToken.expires_at < cutoff
        ).delete()
        self.db.commit()
