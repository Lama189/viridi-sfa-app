from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repos.notifications import INotificationRepository
from app.domain.entities.notifications import Notification
from app.infrastructure.postgres.models.notifications import (
    Notification as NotificationModel,
)


class PostgresNotificationRepository(INotificationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, notification: Notification) -> None:
        model = self._to_model(notification)
        self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, notification_id: UUID) -> Notification | None:
        result = await self._session.execute(
            select(NotificationModel).where(NotificationModel.id == notification_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain(model)

    async def list_by_employee(
        self,
        employee_id: UUID,
        only_unread: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Notification]:
        stmt = (
            select(NotificationModel)
            .where(NotificationModel.employee_id == employee_id)
            .order_by(NotificationModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if only_unread:
            stmt = stmt.where(NotificationModel.is_read.is_(False))

        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def count_unread_by_employee(self, employee_id: UUID) -> int:
        stmt = select(func.count(NotificationModel.id)).where(
            NotificationModel.employee_id == employee_id,
            NotificationModel.is_read.is_(False),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() or 0

    async def update(self, notification: Notification) -> None:
        await self._session.execute(
            update(NotificationModel)
            .where(NotificationModel.id == notification.id)
            .values(
                title=notification.title,
                body=notification.body,
                notification_type=notification.notification_type,
                payload=notification.payload,
                is_read=notification.is_read,
                read_at=notification.read_at,
            )
        )
        await self._session.flush()

    async def mark_all_as_read(self, employee_id: UUID) -> None:
        now = datetime.now(UTC)
        await self._session.execute(
            update(NotificationModel)
            .where(
                NotificationModel.employee_id == employee_id,
                NotificationModel.is_read.is_(False),
            )
            .values(
                is_read=True,
                read_at=now,
            )
        )
        await self._session.flush()

    async def delete(self, notification_id: UUID) -> None:
        await self._session.execute(
            sa_delete(NotificationModel).where(NotificationModel.id == notification_id)
        )
        await self._session.flush()

    def _to_model(self, entity: Notification) -> NotificationModel:
        return NotificationModel(
            id=entity.id,
            employee_id=entity.employee_id,
            title=entity.title,
            body=entity.body,
            notification_type=entity.notification_type,
            payload=entity.payload,
            is_read=entity.is_read,
            created_at=entity.created_at,
            read_at=entity.read_at,
        )

    def _to_domain(self, model: NotificationModel) -> Notification:
        return Notification(
            id=model.id,
            employee_id=model.employee_id,
            title=model.title,
            body=model.body,
            notification_type=model.notification_type,
            payload=model.payload,
            is_read=model.is_read,
            created_at=model.created_at,
            read_at=model.read_at,
        )
