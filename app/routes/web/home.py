from fastapi import APIRouter, Request, Depends
from sqlmodel import Session
from app.core.database import get_session
from app.core.templates import render_template
from app.services import TournamentService

router = APIRouter()

@router.get("/")
def home(request: Request, db: Session = Depends(get_session)):
    """Render the homepage dashboard with recent tournaments."""
    tournaments = TournamentService.get_all_tournaments(db)
    return render_template(request, db, "index.html", {
        "tournaments": tournaments,
        "active_page": "home"
    })
