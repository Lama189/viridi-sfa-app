from uuid import uuid4

from app.application.interfaces.object_storage import IObjectStorage
from app.domain.entities.media import MediaFile
from app.domain.enums import MediaBucket


class MediaService:

    def __init__(
        self,
        storage: IObjectStorage,
    ) -> None:
        self._storage = storage


    async def upload(
        self,
        bucket: MediaBucket,
        data: bytes,
        content_type: str,
        filename: str | None = None,
        prefix: str | None = None,
    ) -> MediaFile:

        object_name = str(uuid4())

        if prefix:
            object_name = f"{prefix}/{object_name}"


        await self._storage.upload(
            bucket_name=bucket.value,
            object_name=object_name,
            data=data,
            filename=filename,
            content_type=content_type,
        )


        return MediaFile(
            bucket=bucket.value,
            object_name=object_name,
            content_type=content_type,
            size=len(data),
            original_filename=filename,
        )