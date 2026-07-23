from io import BytesIO
from uuid import UUID, uuid4

from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

from app.application.interfaces.object_storage import IObjectStorage
from app.application.interfaces.uow import IUnitOfWork
from app.domain.entities.media import MediaFile
from app.domain.enums import MediaBucket

register_heif_opener()


class MediaService:
    MAX_FILE_SIZE = 15 * 1024 * 1024
    MAX_IMAGE_SIZE = (1920, 1920)
    OUTPUT_FORMAT = "WEBP"
    OUTPUT_CONTENT_TYPE = "image/webp"
    OUTPUT_EXTENSION = "webp"
    OUTPUT_QUALITY = 85

    ALLOWED_CONTENT_TYPES = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/heic",
        "image/heif",
    }

    def __init__(self, uow: IUnitOfWork, storage: IObjectStorage) -> None:
        self._uow = uow
        self._storage = storage

    async def upload(
        self,
        uploaded_by: UUID,
        bucket: MediaBucket,
        data: bytes,
        content_type: str,
        filename: str | None = None,
        prefix: str | None = None,
    ) -> MediaFile:

        data, content_type, extension = self._prepare_image(
            data=data,
            content_type=content_type,
        )

        object_name = f"{uuid4()}.{extension}"

        if prefix:
            object_name = f"{prefix}/{object_name}"

        media_file = MediaFile(
            bucket=bucket.value,
            object_name=object_name,
            content_type=content_type,
            size=len(data),
            original_filename=filename,
            uploaded_by=uploaded_by,
        )

        await self._uow.media_objects.add(media_file)

        await self._storage.upload(
            bucket_name=bucket.value,
            object_name=object_name,
            data=data,
            filename=filename,
            content_type=content_type,
        )

        return media_file

    def _prepare_image(
        self,
        data: bytes,
        content_type: str,
    ) -> tuple[bytes, str, str]:

        if content_type not in self.ALLOWED_CONTENT_TYPES:
            raise ValueError("Unsupported image type.")

        if len(data) > self.MAX_FILE_SIZE:
            raise ValueError("Image is too large.")

        try:
            image = Image.open(BytesIO(data))
        except Exception as exc:
            raise ValueError("Invalid image.") from exc

        image = ImageOps.exif_transpose(image)

        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")

        if image.mode == "RGBA":
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.getchannel("A"))
            image = background

        image.thumbnail(
            self.MAX_IMAGE_SIZE,
            Image.Resampling.LANCZOS,
        )

        output = BytesIO()

        image.save(
            output,
            format=self.OUTPUT_FORMAT,
            quality=self.OUTPUT_QUALITY,
            optimize=True,
        )

        return (
            output.getvalue(),
            self.OUTPUT_CONTENT_TYPE,
            self.OUTPUT_EXTENSION,
        )