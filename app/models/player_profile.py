from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint

if TYPE_CHECKING:
    from app.models.user import User

class PlayerProfile(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("user_id", "sport", name="uq_user_sport"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", nullable=False)
    sport: str = Field(default="tennis", index=True, nullable=False)  # tennis, padel, etc.
    category: Optional[str] = Field(default="B2")  # Primera, A, B1, B2, C, D
    nickname: Optional[str] = Field(default=None, nullable=True)  # player nickname/apodo
    hand_preference: Optional[str] = Field(default="right")  # right, left
    notes: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: "User" = Relationship(back_populates="profiles")
