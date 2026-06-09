from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.tournament import Tournament
    from app.models.user import User

class Match(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tournament_id: int = Field(foreign_key="tournament.id", nullable=False)
    player1_id: int = Field(foreign_key="user.id", nullable=False)
    player2_id: int = Field(foreign_key="user.id", nullable=False)
    winner_id: Optional[int] = Field(foreign_key="user.id", default=None)
    score: Optional[str] = Field(default=None)  # e.g. "6-4, 7-5"
    match_date: datetime = Field(default_factory=datetime.utcnow)
    stage: str = Field(default="groups") # groups, first_round, playoffs
    group_label: Optional[str] = Field(default=None, nullable=True) # e.g. "A", "B"
    cup_name: Optional[str] = Field(default=None, nullable=True) # e.g. "Oro", "Plata", "Bronce"
    round_name: Optional[str] = Field(default=None, nullable=True) # e.g. "Semifinal", "Final", "3° Puesto"

    # Relationships
    tournament: "Tournament" = Relationship(back_populates="matches")
    
    # Resolve ambiguity when multiple foreign keys point to the same User table
    player1: "User" = Relationship(
        sa_relationship_kwargs={"primaryjoin": "Match.player1_id == User.id"}
    )
    player2: "User" = Relationship(
        sa_relationship_kwargs={"primaryjoin": "Match.player2_id == User.id"}
    )
    winner: Optional["User"] = Relationship(
        sa_relationship_kwargs={"primaryjoin": "Match.winner_id == User.id"}
    )
