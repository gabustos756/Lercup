from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint

if TYPE_CHECKING:
    from app.models.tournament import Tournament
    from app.models.user import User

class GroupRound(SQLModel, table=True):
    """One sporting round (jornada) within a group — stores the bye player."""

    __table_args__ = (
        UniqueConstraint(
            "tournament_id", "group_label", "jornada_number",
            name="uq_tournament_group_jornada",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    tournament_id: int = Field(foreign_key="tournament.id", nullable=False)
    group_label: str = Field(nullable=False, index=True)
    jornada_number: int = Field(nullable=False)
    bye_player_id: Optional[int] = Field(foreign_key="user.id", default=None, nullable=True)

    tournament: "Tournament" = Relationship(back_populates="group_rounds")
    bye_player: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[GroupRound.bye_player_id]"}
    )
