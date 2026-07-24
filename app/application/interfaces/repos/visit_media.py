from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.visit_media import VisitMedia


class IVisitMediaRepository(ABC):

    @abstractmethod
    async def add(self, visit_media: VisitMedia) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_visit(self, visit_id: UUID) -> list[VisitMedia]:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, visit_media: VisitMedia) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_all_for_visit(self, visit_id: UUID) -> None:
        raise NotImplementedError
