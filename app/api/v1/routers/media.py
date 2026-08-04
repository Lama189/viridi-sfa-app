from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from starlette import status
from starlette.responses import StreamingResponse

from app.api.dependencies import allow_all_staff, get_media_service
from app.api.v1.schemas.media import MediaUploadResponse
from app.application.services.media import MediaService
from app.domain.entities.auth import AuthenticatedEmployee
from app.domain.enums import MediaBucket

router = APIRouter(prefix="/api/v1/media", tags=["Media"])


@router.post(
    path="/upload",
    status_code=status.HTTP_201_CREATED,
    response_model=MediaUploadResponse,
    dependencies=[Depends(allow_all_staff)],
)
async def upload_media(
    service: Annotated[MediaService, Depends(get_media_service)],
    employee: Annotated[AuthenticatedEmployee, Depends(allow_all_staff)],
    file: UploadFile = File(...),
    bucket: MediaBucket = Query(...),
):
    try:
        data = await file.read()

        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty",
            )

        media = await service.upload(
            bucket=bucket,
            data=data,
            filename=file.filename,
            content_type=file.content_type,
            uploaded_by=employee.id,
        )

        return MediaUploadResponse(
            id=media.id,
            original_object_name=media.original_object_name,
            thumbnail_object_name=media.thumbnail_object_name,
            content_type=media.content_type,
            size=media.size,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    path="/{media_id}/content",
    dependencies=[Depends(allow_all_staff)],
)
async def get_media_content(
    media_id: UUID,
    service: Annotated[MediaService, Depends(get_media_service)],
):
    data, content_type = await service.get_content(media_id)
    return StreamingResponse(
        iter([data]),
        media_type=content_type,
    )


@router.get(
    path="/{media_id}/thumbnail",
    dependencies=[Depends(allow_all_staff)],
)
async def get_media_thumbnail(
    media_id: UUID,
    service: Annotated[MediaService, Depends(get_media_service)],
):
    data, content_type = await service.get_thumbnail(media_id)
    return StreamingResponse(
        iter([data]),
        media_type=content_type,
    )
