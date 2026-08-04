from abc import ABC, abstractmethod

from app.domain.entities.outbox_messages import OutboxMessage


class IPublisher(ABC):
    @abstractmethod
    async def publish(self, message: OutboxMessage) -> None:
        raise NotImplementedError
