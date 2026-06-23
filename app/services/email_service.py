import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    @staticmethod
    def is_configured() -> bool:
        return bool(settings.RESEND_API_KEY and settings.EMAIL_FROM)

    @staticmethod
    def send_password_reset_email(to_email: str, reset_url: str, user_name: str) -> bool:
        """Send password reset email via Resend. Returns True if sent (or logged in dev)."""
        subject = "Restablecer contraseña — Lercup"
        html = f"""
        <div style="font-family: 'Segoe UI', sans-serif; max-width: 520px; margin: 0 auto; color: #0f172a;">
            <h2 style="color: #142820;">Hola {user_name},</h2>
            <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta en Lercup.</p>
            <p style="margin: 1.5rem 0;">
                <a href="{reset_url}"
                   style="background: #c45a2c; color: #fff; padding: 12px 24px;
                          text-decoration: none; border-radius: 8px; font-weight: 600;">
                    Restablecer contraseña
                </a>
            </p>
            <p style="font-size: 0.9rem; color: #64748b;">
                Este enlace expira en {settings.PASSWORD_RESET_EXPIRE_MINUTES} minutos.
                Si no pediste este cambio, ignorá este correo.
            </p>
            <p style="font-size: 0.8rem; color: #94a3b8; word-break: break-all;">
                Si el botón no funciona, copiá este enlace:<br>{reset_url}
            </p>
        </div>
        """

        if not EmailService.is_configured():
            logger.warning(
                "Email no configurado (RESEND_API_KEY / EMAIL_FROM). "
                "Link de recuperación para %s: %s",
                to_email,
                reset_url,
            )
            return settings.ENV != "production"

        try:
            import resend

            resend.api_key = settings.RESEND_API_KEY
            resend.Emails.send(
                {
                    "from": settings.EMAIL_FROM,
                    "to": [to_email],
                    "subject": subject,
                    "html": html,
                }
            )
            return True
        except Exception:
            logger.exception("Error enviando email de recuperación a %s", to_email)
            return False
