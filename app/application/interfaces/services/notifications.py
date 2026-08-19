from abc import ABC, abstractmethod
from uuid import UUID

from app.application.dto.notifications import NotificationCreateDTO
from app.domain.entities.notifications import Notification


class INotificationsService(ABC):
    @abstractmethod
    async def create(self, dto: NotificationCreateDTO) -> Notification:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, notification_id: UUID) -> Notification:
        raise NotImplementedError

    @abstractmethod
    async def list_by_employee(
        self,
        employee_id: UUID,
        only_unread: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Notification]:
        raise NotImplementedError

    @abstractmethod
    async def count_unread_by_employee(self, employee_id: UUID) -> int:
        raise NotImplementedError

    @abstractmethod
    async def mark_as_read(self, notification_id: UUID) -> Notification:
        raise NotImplementedError

    @abstractmethod
    async def mark_all_as_read(self, employee_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, notification_id: UUID) -> None:
        raise NotImplementedError
