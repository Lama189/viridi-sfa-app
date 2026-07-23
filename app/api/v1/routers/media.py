from typing import Annotated
from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
from starlette import status

from app.api.dependencies import get_media_service, allow_all_staff
from app.application.services.media import MediaService
from app.api.v1.schemas.media import MediaUploadResponse
from app.domain.entities.employees import Employee
from app.domain.enums import MediaBucket


router = APIRouter(prefix="/api/v1/media", tags=["Media"])


@router.post(
    path="/upload",
    status_code=status.HTTP_201_CREATED,
    response_model=MediaUploadResponse,
    dependencies=[Depends(allow_all_staff)]
)
async def upload_media(
    service: Annotated[MediaService, Depends(get_media_service)],
    employee: Annotated[Employee, Depends(allow_all_staff)],
    file: UploadFile = File(...),
    bucket: MediaBucket = Query(...)
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
            uploaded_by=employee.id
        )

        return MediaUploadResponse(
            id=media.id,
            bucket=media.bucket,
            object_name=media.object_name,
            content_type=media.content_type,
            size=media.size,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
