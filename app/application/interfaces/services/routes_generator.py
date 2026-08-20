from abc import ABC, abstractmethod


class IRouteGenerationService(ABC):
    @abstractmethod
    async def generate(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def clear_all(self) -> None:
        raise NotImplementedError
