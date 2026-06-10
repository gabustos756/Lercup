from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import get_current_user_or_redirect
from app.core.templates import flash, render_template
from app.models.user import User
from app.services import NotificationService

router = APIRouter(prefix="/notifications")


@router.get("")
def list_notifications(
    request: Request,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_or_redirect),
):
    """List all notifications for the authenticated user."""
    notifications = NotificationService.get_all_notifications(db, current_user.id)
    return render_template(request, db, "notifications/list.html", {
        "notifications": notifications,
        "active_page": "notifications",
    })


@router.post("/mark-all-read")
def mark_all_notifications_read(
    request: Request,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_or_redirect),
):
    """Mark every notification as read for the current user."""
    count = NotificationService.mark_all_as_read(db, current_user.id)
    if count:
        flash(request, f"{count} notificación(es) marcada(s) como leída(s).", "success")
    else:
        flash(request, "No tenés notificaciones sin leer.", "info")
    return RedirectResponse(url="/notifications", status_code=303)


@router.post("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    request: Request,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_or_redirect),
):
    """Mark a single notification as read and redirect to the related match."""
    from fastapi import HTTPException

    try:
        notification = NotificationService.mark_as_read(
            db, notification_id, current_user.id
        )
    except HTTPException as exc:
        flash(request, exc.detail, "danger")
        return RedirectResponse(url="/notifications", status_code=303)

    if notification.related_match_id:
        return RedirectResponse(
            url=f"/users/profile/{current_user.id}",
            status_code=303,
        )
    return RedirectResponse(url="/notifications", status_code=303)
