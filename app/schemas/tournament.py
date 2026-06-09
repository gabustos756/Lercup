from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TournamentBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    surface: str = "clay"  # clay, grass, hard, indoor
    status: str = "draft"  # draft, ongoing, finished
    format_id: Optional[int] = None
    category: str = "flexible"

class TournamentCreate(TournamentBase):
    pass

class TournamentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    surface: Optional[str] = None
    status: Optional[str] = None
    format_id: Optional[int] = None
    category: Optional[str] = None

class TournamentResponse(TournamentBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
