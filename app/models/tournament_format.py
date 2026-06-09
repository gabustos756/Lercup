from typing import Optional
from sqlmodel import SQLModel, Field

class TournamentFormat(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    description: Optional[str] = Field(default=None)
    format_type: str = Field(default="groups_to_playoffs")  # groups_to_playoffs, elimination_with_consolation
    groups_count: int = Field(default=2)
    gold_qualifiers: int = Field(default=2)
    silver_qualifiers: int = Field(default=2)
    bronze_qualifiers: int = Field(default=1)
    has_third_place: bool = Field(default=True)
