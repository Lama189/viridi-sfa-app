from io import BytesIO
from uuid import UUID, uuid4

from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

from app.core.exceptions import MediaNotFoundError
from app.application.interfaces.object_storage import IObjectStorage
from app.application.interfaces.uow import IUnitOfWork
from app.domain.entities.media import MediaFile
from app.domain.enums import MediaBucket


register_heif_opener()


class MediaService:
    MAX_FILE_SIZE = 15 * 1024 * 1024

    MAX_IMAGE_SIZE = (1920, 1920)
    THUMBNAIL_SIZE = (256, 256)

    OUTPUT_FORMAT = "WEBP"
    OUTPUT_CONTENT_TYPE = "image/webp"
    OUTPUT_EXTENSION = "webp"

    OUTPUT_QUALITY = 85
    THUMBNAIL_QUALITY = 75

    ALLOWED_CONTENT_TYPES = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/heic",
        "image/heif",
    }

    def __init__(self, uow: IUnitOfWork, storage: IObjectStorage,) -> None:
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
        prepared_data, content_type, extension = self._prepare_image(
            data,
            content_type,
        )

        thumbnail_data = self._create_thumbnail(prepared_data)

        media_id = uuid4()
        original_object_name = f"{media_id}.{extension}"
        thumbnail_object_name = f"{media_id}_thumb.{extension}"

        if prefix:
            original_object_name = f"{prefix}/original/{original_object_name}"
            thumbnail_object_name = f"{prefix}/thumbnail/{thumbnail_object_name}"

        media_file = MediaFile(
            bucket=bucket.value,
            original_object_name=original_object_name,
            thumbnail_object_name=thumbnail_object_name,
            content_type=content_type,
            size=len(prepared_data),
            original_filename=filename,
            uploaded_by=uploaded_by,
        )

        await self._uow.media_objects.add(media_file)
        await self._uow.commit()

        await self._storage.upload(
            bucket_name=bucket.value,
            object_name=original_object_name,
            data=prepared_data,
            filename=filename,
            content_type=content_type,
        )

        await self._storage.upload(
            bucket_name=bucket.value,
            object_name=thumbnail_object_name,
            data=thumbnail_data,
            filename=filename,
            content_type=content_type,
        )

        return media_file

    async def get_content(self, media_id: UUID) -> tuple[bytes, str]:
        media = await self._uow.media_objects.get_by_id(media_id)
        if not media:
            raise MediaNotFoundError()

        data, _ = await self._storage.download(media.bucket, media.original_object_name)

        return data, media.content_type

    async def get_thumbnail(self, media_id: UUID) -> tuple[bytes, str]:
        media = await self._uow.media_objects.get_by_id(media_id)
        if not media:
            raise MediaNotFoundError()

        data, _ = await self._storage.download(media.bucket, media.thumbnail_object_name)

        return data, media.content_type

    def _prepare_image(self, data: bytes, content_type: str) -> tuple[bytes, str, str]:
        if content_type not in self.ALLOWED_CONTENT_TYPES:
            raise ValueError("Unsupported image type.")

        if len(data) > self.MAX_FILE_SIZE:
            raise ValueError("Image is too large.")
        
        try:
            image = Image.open(BytesIO(data))
        except Exception as exc:
            raise ValueError("Invalid image.") from exc

        image = self._normalize_image(image)
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

    def _create_thumbnail(self, data: bytes) -> bytes:
        try:
            image = Image.open(BytesIO(data))
        except Exception as exc:
            raise ValueError("Invalid image.") from exc

        image = self._normalize_image(image)
        image = ImageOps.fit(
            image,
            self.THUMBNAIL_SIZE,
            method=Image.Resampling.LANCZOS,
        )
        output = BytesIO()

        image.save(
            output,
            format=self.OUTPUT_FORMAT,
            quality=self.THUMBNAIL_QUALITY,
            optimize=True,
        )

        return output.getvalue()

    def _normalize_image(self, image: Image.Image) -> Image.Image:
        image = ImageOps.exif_transpose(image)

        if image.mode not in ("RGB","RGBA"):
            image = image.convert("RGB")

        if image.mode == "RGBA":
            background = Image.new(
                "RGB",
                image.size,
                (255, 255, 255),
            )
            background.paste(image, mask=image.getchannel("A"),)
            image = background

        return image