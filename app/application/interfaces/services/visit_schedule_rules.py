from abc import ABC, abstractmethod
from uuid import UUID

from app.api.v1.schemas.retail_points import VisitsDatesDTO


class IVisitScheduleService(ABC):

    @abstractmethod
    async def replace_schedule(
        self,
        retail_point_id: UUID,
        dto: VisitsDatesDTO,
    ) -> None:
        raise NotImplementedError