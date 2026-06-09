from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlmodel import Session
from app.core.database import get_session
from app.core.templates import render_template, flash
from app.models.tournament_format import TournamentFormat
from app.services.format_service import FormatService
from app.core.security import require_tournament_admin

router = APIRouter(prefix="/tournaments/formats", tags=["formats"])

@router.get("")
def list_formats(
    request: Request,
    db: Session = Depends(get_session),
    current_user = Depends(require_tournament_admin)
):
    formats = FormatService.get_all_formats(db)
    return render_template(request, db, "formats/list.html", {
        "formats": formats,
        "active_page": "tournaments"
    })

@router.get("/create")
def create_format_form(
    request: Request,
    db: Session = Depends(get_session),
    current_user = Depends(require_tournament_admin)
):
    return render_template(request, db, "formats/form.html", {
        "format": None,
        "active_page": "tournaments"
    })

@router.post("/create")
def create_format(
    request: Request,
    name: str = Form(...),
    description: str = Form(None),
    format_type: str = Form(...),
    groups_count: int = Form(0),
    gold_qualifiers: int = Form(0),
    silver_qualifiers: int = Form(0),
    bronze_qualifiers: int = Form(0),
    has_third_place: bool = Form(False),
    db: Session = Depends(get_session),
    current_user = Depends(require_tournament_admin)
):
    fmt = TournamentFormat(
        name=name,
        description=description,
        format_type=format_type,
        groups_count=groups_count,
        gold_qualifiers=gold_qualifiers,
        silver_qualifiers=silver_qualifiers,
        bronze_qualifiers=bronze_qualifiers,
        has_third_place=has_third_place
    )
    FormatService.create_format(db, fmt)
    flash(request, "Formato creado correctamente.", "success")
    return RedirectResponse(url="/tournaments/formats", status_code=303)

@router.get("/edit/{format_id}")
def edit_format_form(
    request: Request,
    format_id: int,
    db: Session = Depends(get_session),
    current_user = Depends(require_tournament_admin)
):
    fmt = FormatService.get_format(db, format_id)
    if not fmt:
        flash(request, "Formato no encontrado.", "danger")
        return RedirectResponse(url="/tournaments/formats", status_code=303)
        
    return render_template(request, db, "formats/form.html", {
        "format": fmt,
        "active_page": "tournaments"
    })

@router.post("/edit/{format_id}")
def edit_format(
    request: Request,
    format_id: int,
    name: str = Form(...),
    description: str = Form(None),
    format_type: str = Form(...),
    groups_count: int = Form(0),
    gold_qualifiers: int = Form(0),
    silver_qualifiers: int = Form(0),
    bronze_qualifiers: int = Form(0),
    has_third_place: bool = Form(False),
    db: Session = Depends(get_session),
    current_user = Depends(require_tournament_admin)
):
    data = {
        "name": name,
        "description": description,
        "format_type": format_type,
        "groups_count": groups_count,
        "gold_qualifiers": gold_qualifiers,
        "silver_qualifiers": silver_qualifiers,
        "bronze_qualifiers": bronze_qualifiers,
        "has_third_place": has_third_place
    }
    fmt = FormatService.update_format(db, format_id, data)
    if not fmt:
        flash(request, "Formato no encontrado.", "danger")
    else:
        flash(request, "Formato actualizado correctamente.", "success")
    return RedirectResponse(url="/tournaments/formats", status_code=303)

@router.post("/delete/{format_id}")
def delete_format(
    request: Request,
    format_id: int,
    db: Session = Depends(get_session),
    current_user = Depends(require_tournament_admin)
):
    success = FormatService.delete_format(db, format_id)
    if success:
        flash(request, "Formato eliminado correctamente.", "success")
    else:
        flash(request, "Formato no encontrado o no pudo eliminarse.", "danger")
    return RedirectResponse(url="/tournaments/formats", status_code=303)
