from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.outbox_messages import OutboxMessage


class IOutboxRepository(ABC):
    @abstractmethod
    async def add(self, message: OutboxMessage) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_unprocessed(
        self,
        limit: int,
    ) -> list[OutboxMessage]:
        raise NotImplementedError

    @abstractmethod
    async def mark_processed(
        self,
        message_id: UUID,
    ) -> None:
        raise NotImplementedError
