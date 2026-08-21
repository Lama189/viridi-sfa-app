from abc import ABC, abstractmethod

from app.domain.enums import RouteGenerationStart


class IRouteGenerationService(ABC):
    @abstractmethod
    async def generate(
        self, start: RouteGenerationStart = RouteGenerationStart.NEXT_WEEK
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def clear_all(self) -> None:
        raise NotImplementedError
