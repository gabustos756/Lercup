import bcrypt
from fastapi import Request, Depends
from sqlmodel import Session
from app.core.database import get_session
from app.models.user import User
from typing import Optional

class NotAuthenticatedException(Exception):
    """Exception raised when a route requires an active login session."""
    pass

class NotAdminException(Exception):
    """Exception raised when an administrative action requires admin privileges."""
    pass

def hash_password(password: str) -> str:
    """Hash a plain text password using native bcrypt."""
    # Ensure password is under 72 bytes for bcrypt compatibility
    pwd_bytes = password.encode('utf-8')
    if len(pwd_bytes) > 72:
        pwd_bytes = pwd_bytes[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against the stored bcrypt hash."""
    try:
        pwd_bytes = plain_password.encode('utf-8')
        if len(pwd_bytes) > 72:
            pwd_bytes = pwd_bytes[:72]
        return bcrypt.checkpw(pwd_bytes, hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_current_user(request: Request, db: Session = Depends(get_session)) -> Optional[User]:
    """Retrieve the logged-in User object based on request session cookies. Returns None if unauthenticated."""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.get(User, user_id)

def get_current_user_or_redirect(request: Request, db: Session = Depends(get_session)) -> User:
    """Dependency that forces user authentication. Raises NotAuthenticatedException if session is missing."""
    user = get_current_user(request, db)
    if not user:
        raise NotAuthenticatedException()
    return user

def require_admin(request: Request, db: Session = Depends(get_session)) -> User:
    """Dependency that forces administrator authorization. Raises NotAdminException or NotAuthenticatedException."""
    user = get_current_user_or_redirect(request, db)
    if user.role != "admin" and not user.is_admin:
        raise NotAdminException()
    return user

def require_tournament_admin(request: Request, db: Session = Depends(get_session)) -> User:
    """Dependency that forces administrator or tournament organizer authorization."""
    user = get_current_user_or_redirect(request, db)
    if user.role not in ("admin", "tournament_admin") and not user.is_admin:
        raise NotAdminException()
    return user
