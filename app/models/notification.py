from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.match import Match


class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", nullable=False, index=True)
    type: str = Field(nullable=False)  # match_proposed, match_confirmed, match_rejected
    message: str = Field(nullable=False)
    related_match_id: Optional[int] = Field(
        foreign_key="match.id", default=None, nullable=True
    )
    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: "User" = Relationship(
        sa_relationship_kwargs={"primaryjoin": "Notification.user_id == User.id"}
    )
    related_match: Optional["Match"] = Relationship(
        sa_relationship_kwargs={"primaryjoin": "Notification.related_match_id == Match.id"}
    )
