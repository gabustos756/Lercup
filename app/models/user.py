from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.player_profile import PlayerProfile
    from app.models.registration import TournamentRegistration
    from app.models.tournament import Tournament

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    full_name: str = Field(nullable=False)
    city: Optional[str] = Field(default=None)
    phone_number: Optional[str] = Field(default=None)
    avatar_url: Optional[str] = Field(default=None)
    is_admin: bool = Field(default=False)
    role: str = Field(default="player") # player, tournament_admin, admin
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    # Cascade deletes: if a user is deleted, their profiles and registrations are deleted
    profiles: List["PlayerProfile"] = Relationship(
        back_populates="user", 
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    registrations: List["TournamentRegistration"] = Relationship(
        back_populates="user", 
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    created_tournaments: List["Tournament"] = Relationship(
        back_populates="creator"
    )
