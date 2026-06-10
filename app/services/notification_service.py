from typing import List, Optional

from fastapi import HTTPException, status
from sqlmodel import Session, select, func

from app.models.notification import Notification


class NotificationService:
    @staticmethod
    def create_notification(
        db: Session,
        user_id: int,
        type: str,
        message: str,
        related_match_id: Optional[int] = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            type=type,
            message=message,
            related_match_id=related_match_id,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def count_unread(db: Session, user_id: int) -> int:
        result = db.exec(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,  # noqa: E712
            )
        ).one()
        return result

    @staticmethod
    def get_unread_notifications(
        db: Session, user_id: int, limit: Optional[int] = None
    ) -> List[Notification]:
        query = (
            select(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,  # noqa: E712
            )
            .order_by(Notification.created_at.desc())
        )
        if limit:
            query = query.limit(limit)
        return list(db.exec(query).all())

    @staticmethod
    def get_all_notifications(db: Session, user_id: int) -> List[Notification]:
        return list(
            db.exec(
                select(Notification)
                .where(Notification.user_id == user_id)
                .order_by(Notification.created_at.desc())
            ).all()
        )

    @staticmethod
    def mark_as_read(db: Session, notification_id: int, user_id: int) -> Notification:
        notification = db.get(Notification, notification_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notificación no encontrada.",
            )
        if notification.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tenés permiso para modificar esta notificación.",
            )
        notification.is_read = True
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def mark_all_as_read(db: Session, user_id: int) -> int:
        notifications = db.exec(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.is_read == False,  # noqa: E712
            )
        ).all()
        count = 0
        for notification in notifications:
            notification.is_read = True
            db.add(notification)
            count += 1
        if count:
            db.commit()
        return count
