from abc import ABC, abstractmethod


class IRouteGenerationService(ABC):
    @abstractmethod
    async def generate(self) -> None:
        raise NotImplementedError