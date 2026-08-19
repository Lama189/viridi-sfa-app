from abc import ABC, abstractmethod
from uuid import UUID


class IPushNotificationService(ABC):
    @abstractmethod
    async def send_to_employee(
        self,
        employee_id: UUID,
        title: str,
        body: str,
        data: dict | None = None,
    ) -> int:
        raise NotImplementedError
