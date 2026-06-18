from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models.match import Match
from app.models.tournament import Tournament
from app.models.user import User
from app.services.notification_service import NotificationService

PROPOSABLE_STATUSES = ("pending", "rejected")
ACTIVE_PROPOSAL_STATUS = "proposed"
CONFIRMED_STATUS = "confirmed"


class MatchService:
    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_match_or_404(db: Session, match_id: int) -> Match:
        match = db.get(Match, match_id)
        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Partido no encontrado.",
            )
        return match

    @staticmethod
    def _get_user_or_404(db: Session, user_id: int) -> User:
        user = db.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado.",
            )
        return user

    @staticmethod
    def _is_match_player(match: Match, user_id: int) -> bool:
        return user_id in (match.player1_id, match.player2_id)

    @staticmethod
    def _is_admin(user: User) -> bool:
        return user.role in ("admin", "tournament_admin") or user.is_admin

    @staticmethod
    def _ensure_not_played(match: Match) -> None:
        if match.match_status == "played":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El partido ya fue jugado y no admite cambios de fecha.",
            )

    @staticmethod
    def _ensure_is_player(match: Match, user_id: int) -> None:
        if not MatchService._is_match_player(match, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los jugadores de este partido pueden realizar esta acción.",
            )

    @staticmethod
    def _ensure_is_opponent(match: Match, user_id: int) -> None:
        MatchService._ensure_is_player(match, user_id)
        if match.proposed_by_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay una propuesta activa en este partido.",
            )
        if match.proposed_by_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puedes confirmar ni rechazar tu propia propuesta.",
            )

    @staticmethod
    def validate_proposed_datetime(
        db: Session,
        tournament_id: int,
        proposed_datetime: datetime,
    ) -> None:
        """Ensure proposed datetime falls within the tournament date range."""
        tournament = db.get(Tournament, tournament_id)
        if not tournament:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Torneo no encontrado.",
            )

        if proposed_datetime < tournament.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "La fecha propuesta es anterior al inicio del torneo "
                    f"({tournament.start_date.strftime('%d/%m/%Y')})."
                ),
            )

        if tournament.end_date and proposed_datetime > tournament.end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "La fecha propuesta es posterior al fin del torneo "
                    f"({tournament.end_date.strftime('%d/%m/%Y')})."
                ),
            )

    @staticmethod
    def _save_match(db: Session, match: Match) -> Match:
        db.add(match)
        db.commit()
        db.refresh(match)
        return match

    @staticmethod
    def _clear_proposal_fields(match: Match) -> None:
        match.proposed_datetime = None
        match.proposed_by_id = None
        match.proposed_location_label = None
        match.proposed_location_url = None
        match.is_change_request = False

    @staticmethod
    def _proposal_location_label(match: Match) -> Optional[str]:
        if match.is_change_request:
            return match.proposed_location_label
        return match.location_label

    @staticmethod
    def _proposal_location_url(match: Match) -> Optional[str]:
        if match.is_change_request:
            return match.proposed_location_url
        return match.location_url

    @staticmethod
    def _apply_confirmed_proposal(match: Match) -> None:
        if not match.proposed_datetime:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La propuesta no tiene fecha definida.",
            )

        match.match_date = match.proposed_datetime

        if match.is_change_request:
            if match.proposed_location_label is not None:
                match.location_label = match.proposed_location_label
            if match.proposed_location_url is not None:
                match.location_url = match.proposed_location_url
        elif match.location_label is None and match.proposed_location_label:
            match.location_label = match.proposed_location_label
            match.location_url = match.proposed_location_url

        MatchService._clear_proposal_fields(match)
        match.match_status = CONFIRMED_STATUS

    @staticmethod
    def _get_opponent_id(match: Match, user_id: int) -> int:
        return match.player2_id if match.player1_id == user_id else match.player1_id

    @staticmethod
    def _match_description(db: Session, match: Match) -> str:
        tournament = db.get(Tournament, match.tournament_id)
        label = tournament.name if tournament else f"partido #{match.id}"
        if match.group_label:
            label += f" (Grupo {match.group_label}"
            if match.jornada_number:
                label += f", Jornada {match.jornada_number}"
            label += ")"
        elif match.jornada_number:
            label += f" (Jornada {match.jornada_number})"
        return label

    @staticmethod
    def _notify_match_event(
        db: Session,
        match: Match,
        recipient_id: int,
        notification_type: str,
        message: str,
    ) -> None:
        NotificationService.create_notification(
            db,
            user_id=recipient_id,
            type=notification_type,
            message=message,
            related_match_id=match.id,
        )

    # ------------------------------------------------------------------
    # Player actions
    # ------------------------------------------------------------------

    @staticmethod
    def propose_match_datetime(
        db: Session,
        match_id: int,
        user_id: int,
        proposed_datetime: datetime,
        location_label: Optional[str] = None,
        location_url: Optional[str] = None,
    ) -> Match:
        """
        Player proposes a date/time for their match.

        Allowed when match_status is pending or rejected.
        """
        match = MatchService._get_match_or_404(db, match_id)
        MatchService._get_user_or_404(db, user_id)
        MatchService._ensure_not_played(match)
        MatchService._ensure_is_player(match, user_id)

        if match.match_status not in PROPOSABLE_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"No se puede proponer fecha con estado '{match.match_status}'. "
                    f"Estados permitidos: {', '.join(PROPOSABLE_STATUSES)}."
                ),
            )

        MatchService.validate_proposed_datetime(
            db, match.tournament_id, proposed_datetime
        )

        match.proposed_datetime = proposed_datetime
        match.proposed_by_id = user_id
        match.location_label = location_label
        match.location_url = location_url
        match.match_status = ACTIVE_PROPOSAL_STATUS

        match = MatchService._save_match(db, match)
        opponent_id = MatchService._get_opponent_id(match, user_id)
        description = MatchService._match_description(db, match)
        MatchService._notify_match_event(
            db,
            match,
            opponent_id,
            "match_proposed",
            f"Tu oponente propuso una fecha para el partido {description}.",
        )
        return match

    @staticmethod
    def request_match_change(
        db: Session,
        match_id: int,
        user_id: int,
        proposed_datetime: datetime,
        location_label: Optional[str] = None,
        location_url: Optional[str] = None,
    ) -> Match:
        """Player requests a schedule change on a confirmed match (needs opponent/admin approval)."""
        match = MatchService._get_match_or_404(db, match_id)
        MatchService._get_user_or_404(db, user_id)
        MatchService._ensure_not_played(match)
        MatchService._ensure_is_player(match, user_id)

        if match.match_status != CONFIRMED_STATUS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se pueden solicitar cambios en partidos confirmados.",
            )

        MatchService.validate_proposed_datetime(
            db, match.tournament_id, proposed_datetime
        )

        match.proposed_datetime = proposed_datetime
        match.proposed_by_id = user_id
        match.proposed_location_label = location_label
        match.proposed_location_url = location_url
        match.is_change_request = True
        match.match_status = ACTIVE_PROPOSAL_STATUS

        match = MatchService._save_match(db, match)
        opponent_id = MatchService._get_opponent_id(match, user_id)
        description = MatchService._match_description(db, match)
        MatchService._notify_match_event(
            db,
            match,
            opponent_id,
            "match_change_requested",
            f"Tu oponente pidió cambiar la fecha del partido {description}.",
        )
        return match

    @staticmethod
    def confirm_match_datetime(db: Session, match_id: int, user_id: int) -> Match:
        """Opponent or admin confirms the proposed date or change request."""
        match = MatchService._get_match_or_404(db, match_id)
        user = MatchService._get_user_or_404(db, user_id)
        MatchService._ensure_not_played(match)

        if match.match_status != ACTIVE_PROPOSAL_STATUS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay una propuesta pendiente para confirmar.",
            )

        is_admin = MatchService._is_admin(user)
        if not is_admin:
            MatchService._ensure_is_opponent(match, user_id)

        was_change = match.is_change_request
        proposer_id = match.proposed_by_id
        MatchService._apply_confirmed_proposal(match)

        match = MatchService._save_match(db, match)
        if proposer_id and proposer_id != user_id:
            description = MatchService._match_description(db, match)
            if was_change:
                message = f"Se aprobó el cambio de fecha del partido {description}."
                notif_type = "match_change_confirmed"
            else:
                message = f"Tu oponente aceptó la fecha del partido {description}."
                notif_type = "match_confirmed"
            MatchService._notify_match_event(
                db, match, proposer_id, notif_type, message
            )
        return match

    @staticmethod
    def reject_match_datetime(db: Session, match_id: int, user_id: int) -> Match:
        """Opponent or admin rejects the proposal or change request."""
        match = MatchService._get_match_or_404(db, match_id)
        user = MatchService._get_user_or_404(db, user_id)
        MatchService._ensure_not_played(match)

        if match.match_status != ACTIVE_PROPOSAL_STATUS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay una propuesta pendiente para rechazar.",
            )

        is_admin = MatchService._is_admin(user)
        if not is_admin:
            MatchService._ensure_is_opponent(match, user_id)

        was_change = match.is_change_request
        proposer_id = match.proposed_by_id
        description = MatchService._match_description(db, match)

        if was_change:
            MatchService._clear_proposal_fields(match)
            match.match_status = CONFIRMED_STATUS
        else:
            MatchService._clear_proposal_fields(match)
            match.location_label = None
            match.location_url = None
            match.match_status = "pending"

        match = MatchService._save_match(db, match)
        if proposer_id and proposer_id != user_id:
            if was_change:
                message = f"Se rechazó el cambio de fecha del partido {description}."
                notif_type = "match_change_rejected"
            else:
                message = f"Tu oponente rechazó la fecha del partido {description}."
                notif_type = "match_rejected"
            MatchService._notify_match_event(
                db, match, proposer_id, notif_type, message
            )
        return match

    # ------------------------------------------------------------------
    # Admin actions
    # ------------------------------------------------------------------

    @staticmethod
    def admin_set_match_datetime(
        db: Session,
        match_id: int,
        admin_user: User,
        proposed_datetime: datetime,
        location_label: Optional[str] = None,
        location_url: Optional[str] = None,
    ) -> Match:
        """
        Admin sets match date directly without tournament range restrictions.
        Sets match_status to confirmed immediately.
        """
        if not MatchService._is_admin(admin_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Se requieren permisos de administrador.",
            )

        match = MatchService._get_match_or_404(db, match_id)
        MatchService._ensure_not_played(match)

        match.proposed_datetime = proposed_datetime
        match.proposed_by_id = admin_user.id
        match.match_date = proposed_datetime
        match.location_label = location_label
        match.location_url = location_url
        MatchService._clear_proposal_fields(match)
        match.match_status = CONFIRMED_STATUS

        return MatchService._save_match(db, match)

    # ------------------------------------------------------------------
    # Result integration (used by TournamentService.add_match)
    # ------------------------------------------------------------------

    @staticmethod
    def apply_result_status(match: Match, winner_id: Optional[int], score: Optional[str]) -> None:
        """Set match_status to played only when a winner is recorded."""
        if winner_id is not None:
            match.match_status = "played"
