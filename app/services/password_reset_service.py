import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlmodel import Session, select
from sqlalchemy import func

from app.core.config import settings
from app.core.security import hash_password
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.services.email_service import EmailService


class PasswordResetService:
    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def _reset_url(token: str) -> str:
        base = settings.APP_BASE_URL.rstrip("/")
        return f"{base}/auth/reset-password/{token}"

    @staticmethod
    def request_reset(db: Session, email: str) -> None:
        """
        Create reset token and send email if user exists.
        Always succeeds from caller perspective (no email enumeration).
        """
        normalized = email.strip().lower()
        user = db.exec(
            select(User).where(func.lower(User.email) == normalized)
        ).first()
        if not user:
            return

        PasswordResetService._invalidate_user_tokens(db, user.id)

        plain_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(
            minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES
        )
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=PasswordResetService._hash_token(plain_token),
                expires_at=expires_at,
            )
        )
        db.commit()

        reset_url = PasswordResetService._reset_url(plain_token)
        EmailService.send_password_reset_email(user.email, reset_url, user.full_name)

    @staticmethod
    def _invalidate_user_tokens(db: Session, user_id: int) -> None:
        tokens = db.exec(
            select(PasswordResetToken).where(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.used_at.is_(None),
            )
        ).all()
        now = datetime.utcnow()
        for t in tokens:
            t.used_at = now
            db.add(t)

    @staticmethod
    def validate_token(db: Session, plain_token: str) -> Optional[User]:
        token_hash = PasswordResetService._hash_token(plain_token)
        record = db.exec(
            select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        ).first()
        if not record or record.used_at is not None:
            return None
        if record.expires_at < datetime.utcnow():
            return None
        return db.get(User, record.user_id)

    @staticmethod
    def reset_password(
        db: Session, plain_token: str, new_password: str
    ) -> User:
        token_hash = PasswordResetService._hash_token(plain_token)
        record = db.exec(
            select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        ).first()

        if not record or record.used_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El enlace de recuperación no es válido o ya fue usado.",
            )
        if record.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El enlace de recuperación expiró. Solicitá uno nuevo.",
            )

        user = db.get(User, record.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuario no encontrado.",
            )

        user.hashed_password = hash_password(new_password)
        record.used_at = datetime.utcnow()
        db.add(user)
        db.add(record)
        db.commit()
        db.refresh(user)
        return user
