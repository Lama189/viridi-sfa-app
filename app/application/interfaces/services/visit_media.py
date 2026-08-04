from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.visit_media import VisitMedia


class IVisitMediaService(ABC):
    @abstractmethod
    async def attach(self, visit_id: UUID, media_id: UUID) -> VisitMedia:
        raise NotImplementedError

    @abstractmethod
    async def detach(self, visit_id: UUID, media_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_media(self, visit_id: UUID) -> list[VisitMedia]:
        raise NotImplementedError
