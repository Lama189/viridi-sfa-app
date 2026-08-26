from uuid import UUID

from app.application.dto.notifications import NotificationCreateDTO
from app.application.interfaces.services.notifications import INotificationsService
from app.application.interfaces.uow import IUnitOfWork
from app.core.exceptions import NotificationNotFoundError
from app.domain.entities.notifications import Notification


class NotificationsService(INotificationsService):
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def create(self, dto: NotificationCreateDTO) -> Notification:
        notification = Notification(
            employee_id=dto.employee_id,
            title=dto.title,
            body=dto.body,
            notification_type=dto.notification_type,
            payload=dto.payload,
        )

        await self._uow.notifications.add(notification)
        await self._uow.commit()
        return notification

    async def get_by_id(self, notification_id: UUID) -> Notification:
        notification = await self._uow.notifications.get_by_id(notification_id)
        if not notification:
            raise NotificationNotFoundError(
                f"Notification with id {notification_id} not found"
            )

        return notification

    async def list_by_employee(
        self,
        employee_id: UUID,
        only_unread: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Notification]:
        return await self._uow.notifications.list_by_employee(
            employee_id=employee_id,
            only_unread=only_unread,
            limit=limit,
            offset=offset,
        )

    async def count_unread_by_employee(self, employee_id: UUID) -> int:
        return await self._uow.notifications.count_unread_by_employee(employee_id)

    async def mark_as_read(
        self, notification_id: UUID, employee_id: UUID | None = None
    ) -> Notification:
        notification = await self.get_by_id(notification_id)

        if employee_id is not None and notification.employee_id != employee_id:
            raise PermissionError("Not authorized to access this notification")
        notification.mark_as_read()

        await self._uow.notifications.update(notification)

        await self._uow.commit()

        return notification

    async def mark_all_as_read(self, employee_id: UUID) -> None:
        await self._uow.notifications.mark_all_as_read(employee_id)
        await self._uow.commit()

    async def delete(
        self, notification_id: UUID, employee_id: UUID | None = None
    ) -> None:
        notification = await self.get_by_id(notification_id)

        if employee_id is not None and notification.employee_id != employee_id:
            raise PermissionError("Not authorized to access this notification")
        
        await self._uow.notifications.delete(notification.id)
        await self._uow.commit()
