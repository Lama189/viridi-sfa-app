from abc import ABC, abstractmethod
from datetime import date

from app.domain.enums import RouteGenerationStart


class IRouteGenerationService(ABC):
    @abstractmethod
    async def generate(
        self, start: RouteGenerationStart = RouteGenerationStart.NEXT_WEEK
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def clear_all(self, from_date: date | None = None) -> None:
        raise NotImplementedError
