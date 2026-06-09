from typing import Optional
from sqlmodel import Session, select
from app.models.user import User
from app.models.player_profile import PlayerProfile
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password

class AuthService:
    @staticmethod
    def register_user(db: Session, user_data: UserCreate) -> User:
        """Register a new user, hashing their password, and instantiating a default tennis PlayerProfile."""
        existing = db.exec(select(User).where(User.email == user_data.email)).first()
        if existing:
            raise ValueError("El correo electrónico ya está registrado.")
        
        hashed = hash_password(user_data.password)
        role_val = user_data.role
        is_admin_val = user_data.is_admin
        if role_val == "admin":
            is_admin_val = True
        elif is_admin_val:
            role_val = "admin"

        db_user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            city=user_data.city,
            phone_number=user_data.phone_number,
            avatar_url=user_data.avatar_url,
            hashed_password=hashed,
            is_admin=is_admin_val,
            role=role_val
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Instantiate a default tennis PlayerProfile for self-registered competitors
        profile = PlayerProfile(
            user_id=db_user.id,
            sport="tennis",
            category="B2",
            nickname=None,
            hand_preference="right"
        )
        db.add(profile)
        db.commit()
        db.refresh(db_user)
        
        return db_user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate a user by checking email and verifying hashed password."""
        user = db.exec(select(User).where(User.email == email)).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
