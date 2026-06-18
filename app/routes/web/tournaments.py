from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from app.core.database import get_session
from app.core.templates import render_template, flash
from app.models.user import User
from app.services import TournamentService, UserService, FormatService, FixtureService
from app.schemas.tournament import TournamentCreate, TournamentUpdate
from app.core.security import get_current_user, get_current_user_or_redirect, require_admin, require_tournament_admin
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/tournaments")

@router.get("")
def list_tournaments(
    request: Request, 
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_or_redirect)
):
    """Render list of all tournaments (Requires login)."""
    tournaments = TournamentService.get_all_tournaments(db)
    return render_template(request, db, "tournaments/list.html", {
        "tournaments": tournaments,
        "active_page": "tournaments"
    })

@router.get("/detail/{tournament_id}")
def tournament_detail(
    tournament_id: int, 
    request: Request, 
    db: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Render tournament details. Public view; scheduling panels require a logged-in player or admin."""
    tournament = TournamentService.get_tournament_by_id(db, tournament_id)
    if not tournament:
        flash(request, "Torneo no encontrado.", "danger")
        return RedirectResponse(url="/tournaments", status_code=303)
        
    # Fetch the raw match models to check stage and cup details
    from app.models.match import Match
    from app.models.registration import TournamentRegistration
    
    raw_matches = db.exec(
        select(Match).where(Match.tournament_id == tournament_id).order_by(Match.match_date.asc())
    ).all()
    
    # We want to format the matches list for rendering, keeping our detailed player details
    formatted_matches = []
    for m in raw_matches:
        p1 = db.get(User, m.player1_id)
        p2 = db.get(User, m.player2_id)
        w = db.get(User, m.winner_id) if m.winner_id else None
        proposed_by = db.get(User, m.proposed_by_id) if m.proposed_by_id else None
        formatted_matches.append({
            "id": m.id,
            "player1_id": m.player1_id,
            "player2_id": m.player2_id,
            "player1": p1,
            "player2": p2,
            "winner": w,
            "score": m.score,
            "match_date": m.match_date,
            "stage": m.stage,
            "group_label": m.group_label,
            "cup_name": m.cup_name,
            "round_name": m.round_name,
            "jornada_number": m.jornada_number,
            "match_status": m.match_status,
            "proposed_datetime": m.proposed_datetime,
            "proposed_by": proposed_by,
            "proposed_by_id": m.proposed_by_id,
            "location_label": m.location_label,
            "location_url": m.location_url,
            "is_change_request": m.is_change_request,
            "proposed_location_label": m.proposed_location_label,
            "proposed_location_url": m.proposed_location_url,
            "player1_phone": p1.phone_number if p1 else None,
            "player2_phone": p2.phone_number if p2 else None,
        })
        
    users = UserService.get_all_users(db)  # Needed for the match recorder dropdown
    
    # Calculate standings if format exists and has groups
    standings_A = []
    standings_B = []
    if tournament.format and tournament.format.groups_count > 0:
        standings_A = TournamentService.get_group_standings(db, tournament_id, "A")
        if tournament.format.groups_count > 1:
            standings_B = TournamentService.get_group_standings(db, tournament_id, "B")
            
    # Fetch registrations
    registrations = db.exec(
        select(TournamentRegistration).where(TournamentRegistration.tournament_id == tournament_id)
    ).all()
    
    reg_details = []
    for r in registrations:
        u = db.get(User, r.user_id)
        if u:
            reg_details.append({
                "id": r.id,
                "user": u,
                "status": r.status,
                "group_label": r.group_label,
                "registered_at": r.registered_at
            })

    progress = TournamentService.get_tournament_progress(db, tournament_id)
    playoff_bracket = TournamentService.get_playoff_bracket(db, tournament_id)
    group_fixture = FixtureService.get_group_fixture_view(db, tournament_id)
            
    return render_template(request, db, "tournaments/detail.html", {
        "tournament": tournament,
        "matches": formatted_matches,
        "users": users,
        "standings_A": standings_A,
        "standings_B": standings_B,
        "registrations": reg_details,
        "progress": progress,
        "playoff_bracket": playoff_bracket,
        "group_fixture": group_fixture,
        "current_user": current_user,
        "active_page": "tournaments",
    })

@router.post("/detail/{tournament_id}/register")
def register_self(
    tournament_id: int,
    request: Request,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_or_redirect)
):
    """Register the current logged-in user to the tournament, validating category locks."""
    tournament = TournamentService.get_tournament_by_id(db, tournament_id)
    if not tournament:
        flash(request, "Torneo no encontrado.", "danger")
        return RedirectResponse(url="/tournaments", status_code=303)
        
    if tournament.status != "draft":
        flash(request, "El torneo ya no acepta inscripciones.", "danger")
        return RedirectResponse(url=f"/tournaments/detail/{tournament_id}", status_code=303)
        
    # Check if already registered
    from app.models.registration import TournamentRegistration
    existing = db.exec(
        select(TournamentRegistration).where(
            TournamentRegistration.tournament_id == tournament_id,
            TournamentRegistration.user_id == current_user.id
        )
    ).first()
    if existing:
        flash(request, "Ya estás inscrito en este torneo.", "warning")
        return RedirectResponse(url=f"/tournaments/detail/{tournament_id}", status_code=303)
        
    # Category compatibility check
    user_category = "B2"
    for prof in current_user.profiles:
        if prof.sport == "tennis":
            user_category = prof.category
            break
            
    if tournament.category != "flexible" and tournament.category != user_category:
        flash(request, f"No cumples con el requisito de categoría. Este torneo es para la categoría '{tournament.category}' y tú eres '{user_category}'.", "danger")
        return RedirectResponse(url=f"/tournaments/detail/{tournament_id}", status_code=303)
        
    reg = TournamentRegistration(
        tournament_id=tournament_id,
        user_id=current_user.id,
        status="approved"
    )
    db.add(reg)
    db.commit()
    flash(request, "Inscripción realizada con éxito.", "success")
    return RedirectResponse(url=f"/tournaments/detail/{tournament_id}", status_code=303)

@router.get("/create")
def get_create_tournament(
    request: Request, 
    db: Session = Depends(get_session),
    admin_user: User = Depends(require_tournament_admin)
):
    """Render tournament creation form (Admin only)."""
    formats = FormatService.get_all_formats(db)
    return render_template(request, db, "tournaments/form.html", {
        "edit_mode": False,
        "formats": formats,
        "active_page": "tournaments"
    })

@router.post("/create")
def post_create_tournament(
    request: Request,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    start_date: str = Form(...),
    end_date: str = Form(...),
    surface: str = Form("clay"),
    status: str = Form("draft"),
    format_id: Optional[int] = Form(None),
    category: str = Form("flexible"),
    db: Session = Depends(get_session),
    admin_user: User = Depends(require_tournament_admin)
):
    """Process tournament creation form (Admin only)."""
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        if start_dt > end_dt:
            raise ValueError("La fecha de inicio no puede ser posterior a la fecha de fin.")
            
        tournament_data = TournamentCreate(
            name=name,
            description=description,
            start_date=start_dt,
            end_date=end_dt,
            surface=surface,
            status=status,
            format_id=format_id,
            category=category
        )
        TournamentService.create_tournament(db, tournament_data, creator_id=admin_user.id)
        flash(request, f"Torneo '{name}' creado con éxito.", "success")
        return RedirectResponse(url="/tournaments", status_code=303)
        
    except ValueError as e:
        flash(request, str(e), "danger")
        formats = FormatService.get_all_formats(db)
        return render_template(request, db, "tournaments/form.html", {
            "edit_mode": False,
            "name": name,
            "formats": formats,
            "description": description,
            "surface": surface,
            "status": status,
            "category": category,
            "active_page": "tournaments"
        })

@router.get("/edit/{tournament_id}")
def get_edit_tournament(
    tournament_id: int, 
    request: Request, 
    db: Session = Depends(get_session),
    admin_user: User = Depends(require_tournament_admin)
):
    """Render tournament edit form (Admin only)."""
    tournament = TournamentService.get_tournament_by_id(db, tournament_id)
    if not tournament:
        flash(request, "Torneo no encontrado.", "danger")
        return RedirectResponse(url="/tournaments", status_code=303)
        
    start_date_str = tournament.start_date.strftime("%Y-%m-%d")
    end_date_str = tournament.end_date.strftime("%Y-%m-%d")
    formats = FormatService.get_all_formats(db)
    
    return render_template(request, db, "tournaments/form.html", {
        "edit_mode": True,
        "tournament": tournament,
        "start_date_str": start_date_str,
        "end_date_str": end_date_str,
        "formats": formats,
        "active_page": "tournaments"
    })

@router.post("/edit/{tournament_id}")
def post_edit_tournament(
    tournament_id: int,
    request: Request,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    start_date: str = Form(...),
    end_date: str = Form(...),
    surface: str = Form("clay"),
    status: str = Form("draft"),
    format_id: Optional[int] = Form(None),
    category: str = Form("flexible"),
    db: Session = Depends(get_session),
    admin_user: User = Depends(require_tournament_admin)
):
    """Process tournament editing (Admin only)."""
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        if start_dt > end_dt:
            raise ValueError("La fecha de inicio no puede ser posterior a la fecha de fin.")
            
        tournament_data = TournamentUpdate(
            name=name,
            description=description,
            start_date=start_dt,
            end_date=end_dt,
            surface=surface,
            status=status,
            format_id=format_id,
            category=category
        )
        TournamentService.update_tournament(db, tournament_id, tournament_data)
        flash(request, f"Torneo '{name}' actualizado con éxito.", "success")
        return RedirectResponse(url="/tournaments", status_code=303)
        
    except ValueError as e:
        flash(request, str(e), "danger")
        tournament = TournamentService.get_tournament_by_id(db, tournament_id)
        start_date_str = tournament.start_date.strftime("%Y-%m-%d")
        end_date_str = tournament.end_date.strftime("%Y-%m-%d")
        formats = FormatService.get_all_formats(db)
        return render_template(request, db, "tournaments/form.html", {
            "edit_mode": True,
            "tournament": tournament,
            "start_date_str": start_date_str,
            "end_date_str": end_date_str,
            "formats": formats,
            "active_page": "tournaments"
        })

@router.post("/delete/{tournament_id}")
def post_delete_tournament(
    tournament_id: int, 
    request: Request, 
    db: Session = Depends(get_session),
    admin_user: User = Depends(require_tournament_admin)
):
    """Delete a tournament (Admin only)."""
    success = TournamentService.delete_tournament(db, tournament_id)
    if success:
        flash(request, "Torneo y partidos relacionados eliminados correctamente.", "success")
    else:
        flash(request, "El torneo no pudo ser eliminado.", "danger")
    return RedirectResponse(url="/tournaments", status_code=303)

@router.post("/detail/{tournament_id}/add-match")
def add_match(
    tournament_id: int,
    request: Request,
    player1_id: int = Form(...),
    player2_id: int = Form(...),
    winner_id: Optional[int] = Form(None),
    score: Optional[str] = Form(None),
    stage: str = Form("groups"),
    group_label: Optional[str] = Form(None),
    cup_name: Optional[str] = Form(None),
    round_name: Optional[str] = Form(None),
    db: Session = Depends(get_session),
    admin_user: User = Depends(require_tournament_admin)
):
    """Register a new match inside a tournament (Admin only)."""
    if group_label == "":
        group_label = None
    if cup_name == "":
        cup_name = None
    if round_name == "":
        round_name = None
        
    try:
        TournamentService.add_match(
            db, 
            tournament_id=tournament_id,
            player1_id=player1_id,
            player2_id=player2_id,
            winner_id=winner_id,
            score=score,
            stage=stage,
            group_label=group_label,
            cup_name=cup_name,
            round_name=round_name
        )
        flash(request, "Partido registrado con éxito.", "success")
    except ValueError as e:
        flash(request, str(e), "danger")
        
    return RedirectResponse(url=f"/tournaments/detail/{tournament_id}", status_code=303)

@router.post("/detail/{tournament_id}/delete-match/{match_id}")
def delete_match(
    tournament_id: int,
    match_id: int,
    request: Request,
    db: Session = Depends(get_session),
    admin_user: User = Depends(require_tournament_admin)
):
    """Delete a match from a tournament (Admin only)."""
    success = TournamentService.delete_match(db, match_id)
    if success:
        flash(request, "Partido eliminado correctamente.", "success")
    else:
        flash(request, "Error al eliminar el partido.", "danger")
        
    return RedirectResponse(url=f"/tournaments/detail/{tournament_id}", status_code=303)

@router.post("/detail/{tournament_id}/assign-group/{registration_id}")
def assign_group(
    tournament_id: int,
    registration_id: int,
    request: Request,
    group_label: Optional[str] = Form(None),
    db: Session = Depends(get_session),
    admin_user: User = Depends(require_tournament_admin)
):
    if group_label == "":
        group_label = None
    success = TournamentService.assign_player_to_group(db, registration_id, group_label)
    if success:
        flash(request, "Grupo asignado con éxito.", "success")
    else:
        flash(request, "Error al asignar grupo.", "danger")
    return RedirectResponse(url=f"/tournaments/detail/{tournament_id}", status_code=303)

@router.post("/detail/{tournament_id}/close-registrations")
def close_registrations(
    tournament_id: int,
    request: Request,
    db: Session = Depends(get_session),
    admin_user: User = Depends(require_tournament_admin)
):
    success = TournamentService.close_registrations(db, tournament_id)
    if success:
        flash(request, "Inscripciones cerradas. Ya podés realizar el sorteo de grupos.", "success")
    else:
        flash(request, "No se pudieron cerrar las inscripciones. Verificá que el torneo esté en borrador y tenga al menos 2 jugadores.", "danger")
    return RedirectResponse(url=f"/tournaments/detail/{tournament_id}", status_code=303)

@router.post("/detail/{tournament_id}/perform-draw")
def perform_draw(
    tournament_id: int,
    request: Request,
    db: Session = Depends(get_session),
    admin_user: User = Depends(require_tournament_admin)
):
    success = TournamentService.perform_group_draw(db, tournament_id)
    if success:
        flash(request, "Sorteo realizado. Jugadores distribuidos en grupos A y B con fixture round-robin generado.", "success")
    else:
        flash(request, "No se pudo realizar el sorteo. Cerrá inscripciones primero y verificá que no exista un sorteo previo.", "danger")
    return RedirectResponse(url=f"/tournaments/detail/{tournament_id}", status_code=303)

@router.post("/detail/{tournament_id}/auto-assign-groups")
def auto_assign_groups(
    tournament_id: int,
    request: Request,
    db: Session = Depends(get_session),
    admin_user: User = Depends(require_tournament_admin)
):
    from app.models.registration import TournamentRegistration
    regs = db.exec(
        select(TournamentRegistration).where(
            TournamentRegistration.tournament_id == tournament_id,
            TournamentRegistration.status == "approved"
        )
    ).all()
    
    # Alternating assignment A, B, A, B...
    for idx, r in enumerate(regs):
        r.group_label = "A" if idx % 2 == 0 else "B"
        db.add(r)
    db.commit()
    flash(request, "Jugadores distribuidos equitativamente en grupos A y B.", "success")
    return RedirectResponse(url=f"/tournaments/detail/{tournament_id}", status_code=303)

@router.post("/detail/{tournament_id}/generate-initial-round")
def generate_initial_round(
    tournament_id: int,
    request: Request,
    db: Session = Depends(get_session),
    admin_user: User = Depends(require_tournament_admin)
):
    success = TournamentService.generate_initial_elimination_round(db, tournament_id)
    if success:
        flash(request, "Primera ronda de eliminación directa generada con éxito.", "success")
    else:
        flash(request, "No se pudo generar la primera ronda. Verifique que no existan partidos previos y que haya suficientes jugadores.", "danger")
    return RedirectResponse(url=f"/tournaments/detail/{tournament_id}", status_code=303)

@router.post("/detail/{tournament_id}/generate-playoffs")
def generate_playoffs(
    tournament_id: int,
    request: Request,
    db: Session = Depends(get_session),
    admin_user: User = Depends(require_tournament_admin)
):
    success = TournamentService.generate_playoff_bracket(db, tournament_id)
    if success:
        flash(request, "Fase final / Copas generada con éxito.", "success")
    else:
        flash(request, "No se pudo generar la fase final. Completá todos los partidos de la fase de grupos antes de generar las copas.", "danger")
    return RedirectResponse(url=f"/tournaments/detail/{tournament_id}", status_code=303)
