from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.media import MediaFile


class IMediaObjectRepository(ABC):

    @abstractmethod
    async def add(self, media: MediaFile) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, media_id: UUID) -> MediaFile | None:
        raise NotImplementedError

    @abstractmethod
    async def update(self, media: MediaFile) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, media: MediaFile) -> None:
        raise NotImplementedError
