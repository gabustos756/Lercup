from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.core.database import get_session
from app.services import TournamentService
from app.models.tournament import Tournament
from typing import List, Dict, Any

router = APIRouter(prefix="/tournaments", tags=["API Tournaments"])

@router.get("", response_model=List[Tournament])
def api_list_tournaments(db: Session = Depends(get_session)):
    """API endpoint to retrieve all tournaments."""
    return TournamentService.get_all_tournaments(db)

@router.get("/detail/{tournament_id}", response_model=Dict[str, Any])
def api_get_tournament_detail(tournament_id: int, db: Session = Depends(get_session)):
    """API endpoint to get tournament detail including matches."""
    tournament = TournamentService.get_tournament_by_id(db, tournament_id)
    if not tournament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Torneo no encontrado.")
    
    matches = TournamentService.get_tournament_matches(db, tournament_id)
    return {
        "tournament": tournament,
        "matches": matches
    }
