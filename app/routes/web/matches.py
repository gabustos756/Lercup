from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import get_current_user_or_redirect, require_admin
from app.core.templates import flash
from app.models.user import User
from app.services import MatchService

router = APIRouter(prefix="/matches")


def _redirect_profile(user_id: int) -> RedirectResponse:
    return RedirectResponse(url=f"/users/profile/{user_id}", status_code=303)


def _redirect_tournament(tournament_id: int) -> RedirectResponse:
    return RedirectResponse(url=f"/tournaments/detail/{tournament_id}", status_code=303)


def _safe_return_url(return_url: Optional[str]) -> Optional[str]:
    if return_url and return_url.startswith("/") and not return_url.startswith("//"):
        return return_url
    return None


def _redirect_after_action(
    current_user: User, return_url: Optional[str] = None
) -> RedirectResponse:
    safe_url = _safe_return_url(return_url)
    if safe_url:
        return RedirectResponse(url=safe_url, status_code=303)
    return _redirect_profile(current_user.id)


def _handle_match_action(
    request: Request,
    current_user: User,
    action,
    success_message: str,
    return_url: Optional[str] = None,
) -> RedirectResponse:
    try:
        action()
        flash(request, success_message, "success")
    except HTTPException as exc:
        flash(request, exc.detail, "danger")
    return _redirect_after_action(current_user, return_url)


@router.post("/{match_id}/propose")
def propose_match_datetime(
    match_id: int,
    request: Request,
    proposed_datetime: str = Form(...),
    location_label: Optional[str] = Form(None),
    location_url: Optional[str] = Form(None),
    return_url: Optional[str] = Form(None),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_or_redirect),
):
    """Player proposes a date/time for their match."""
    try:
        dt = datetime.fromisoformat(proposed_datetime)
    except ValueError:
        flash(request, "Formato de fecha y hora inválido.", "danger")
        return _redirect_after_action(current_user, return_url)

    return _handle_match_action(
        request,
        current_user,
        lambda: MatchService.propose_match_datetime(
            db,
            match_id,
            current_user.id,
            dt,
            location_label=location_label.strip() if location_label and location_label.strip() else None,
            location_url=location_url.strip() if location_url and location_url.strip() else None,
        ),
        "Propuesta de fecha enviada. Esperá la confirmación de tu oponente.",
        return_url,
    )


@router.post("/{match_id}/confirm")
def confirm_match_datetime(
    match_id: int,
    request: Request,
    return_url: Optional[str] = Form(None),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_or_redirect),
):
    """Opponent confirms the proposed date."""
    return _handle_match_action(
        request,
        current_user,
        lambda: MatchService.confirm_match_datetime(db, match_id, current_user.id),
        "Fecha confirmada. ¡A jugar!",
        return_url,
    )


@router.post("/{match_id}/reject")
def reject_match_datetime(
    match_id: int,
    request: Request,
    return_url: Optional[str] = Form(None),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_or_redirect),
):
    """Opponent rejects the proposed date."""
    return _handle_match_action(
        request,
        current_user,
        lambda: MatchService.reject_match_datetime(db, match_id, current_user.id),
        "Propuesta rechazada. Podés proponer una nueva fecha.",
        return_url,
    )


@router.post("/{match_id}/admin-set")
def admin_set_match_datetime(
    match_id: int,
    request: Request,
    proposed_datetime: str = Form(...),
    location_label: Optional[str] = Form(None),
    location_url: Optional[str] = Form(None),
    return_url: Optional[str] = Form(None),
    db: Session = Depends(get_session),
    admin_user: User = Depends(require_admin),
):
    """Admin sets match date directly."""
    try:
        dt = datetime.fromisoformat(proposed_datetime)
    except ValueError:
        flash(request, "Formato de fecha y hora inválido.", "danger")
        safe_url = _safe_return_url(return_url)
        return RedirectResponse(url=safe_url or "/tournaments", status_code=303)

    try:
        match = MatchService.admin_set_match_datetime(
            db,
            match_id,
            admin_user,
            dt,
            location_label=location_label.strip() if location_label and location_label.strip() else None,
            location_url=location_url.strip() if location_url and location_url.strip() else None,
        )
        flash(request, "Fecha del partido establecida por el administrador.", "success")
        safe_url = _safe_return_url(return_url)
        if safe_url:
            return RedirectResponse(url=safe_url, status_code=303)
        return _redirect_tournament(match.tournament_id)
    except HTTPException as exc:
        flash(request, exc.detail, "danger")
        safe_url = _safe_return_url(return_url)
        if safe_url:
            return RedirectResponse(url=safe_url, status_code=303)
        try:
            from app.models.match import Match

            match = db.get(Match, match_id)
            if match:
                return _redirect_tournament(match.tournament_id)
        except Exception:
            pass
        return RedirectResponse(url="/tournaments", status_code=303)
