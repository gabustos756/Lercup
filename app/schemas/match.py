from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime

MATCH_STATUSES = (
    "pending",
    "proposed",
    "confirmed",
    "result_pending",
    "result_disputed",
    "played",
    "rejected",
)


class MatchProposalCreate(BaseModel):
    proposed_datetime: datetime
    location_label: Optional[str] = None
    location_url: Optional[str] = None


class MatchAdminScheduleUpdate(BaseModel):
    """Admin can set or override scheduling fields freely."""
    match_date: Optional[datetime] = None
    proposed_datetime: Optional[datetime] = None
    location_label: Optional[str] = None
    location_url: Optional[str] = None
    match_status: Optional[
        Literal[
            "pending",
            "proposed",
            "confirmed",
            "result_pending",
            "result_disputed",
            "played",
            "rejected",
        ]
    ] = None


class MatchResultUpdate(BaseModel):
    winner_id: Optional[int] = None
    score: Optional[str] = None


class MatchScheduleResponse(BaseModel):
    id: int
    tournament_id: int
    player1_id: int
    player2_id: int
    match_date: datetime
    proposed_datetime: Optional[datetime] = None
    proposed_by_id: Optional[int] = None
    location_label: Optional[str] = None
    location_url: Optional[str] = None
    match_status: str
    winner_id: Optional[int] = None
    score: Optional[str] = None

    class Config:
        from_attributes = True
