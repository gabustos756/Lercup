from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.tournament import Tournament

class TournamentRegistration(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("tournament_id", "user_id", name="uq_tournament_user"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    tournament_id: int = Field(foreign_key="tournament.id", nullable=False)
    user_id: int = Field(foreign_key="user.id", nullable=False)
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="registered")  # registered, approved, cancelled
    group_label: Optional[str] = Field(default=None, nullable=True)  # e.g. "A", "B"

    # Relationships
    user: "User" = Relationship(back_populates="registrations")
    tournament: "Tournament" = Relationship(back_populates="registrations")
