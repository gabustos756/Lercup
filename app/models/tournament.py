from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.registration import TournamentRegistration
    from app.models.match import Match
    from app.models.tournament_format import TournamentFormat
    from app.models.group_round import GroupRound

class Tournament(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    description: Optional[str] = Field(default=None)
    start_date: datetime = Field(nullable=False)
    end_date: datetime = Field(nullable=False)
    surface: str = Field(default="clay")  # clay, grass, hard, indoor
    status: str = Field(default="draft")  # draft, ongoing, finished
    creator_id: int = Field(foreign_key="user.id", nullable=False)
    format_id: Optional[int] = Field(foreign_key="tournamentformat.id", default=None, nullable=True)
    sport: str = Field(default="tennis", index=True, nullable=False)  # tennis, padel, etc.
    category: str = Field(default="flexible", nullable=False) # flexible, Primera, A, B1, B2, C, D
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    creator: "User" = Relationship(back_populates="created_tournaments")
    format: Optional["TournamentFormat"] = Relationship()
    registrations: List["TournamentRegistration"] = Relationship(
        back_populates="tournament", 
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    matches: List["Match"] = Relationship(
        back_populates="tournament", 
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    group_rounds: List["GroupRound"] = Relationship(
        back_populates="tournament",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
