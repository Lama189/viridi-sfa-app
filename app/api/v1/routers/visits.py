from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import (
    allow_all_staff,
    get_visit_media_service,
    get_visits_service,
)
from app.api.v1.schemas.visits import (
    AddDebtRequest,
    AttachMediaRequest,
    UpdateDebtRequest,
    VisitDebtResponse,
    VisitDetailsResponse,
    VisitMediaResponse,
    VisitResponse,
)
from app.application.services.visit_media import VisitMediaService
from app.application.services.visits import VisitService
from app.core.exceptions import VisitNotFoundError
from app.domain.entities.auth import AuthenticatedEmployee
from app.domain.enums import VisitStatus

router = APIRouter(prefix="/api/v1/visits", tags=["Visits"])


@router.post(
    path="/start",
    response_model=VisitResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_visit(
    retail_point_id: UUID,
    employee: Annotated[AuthenticatedEmployee, Depends(allow_all_staff)],
    service: Annotated[VisitService, Depends(get_visits_service)],
):
    visit = await service.start_visit(employee.id, retail_point_id)
    return VisitResponse.model_validate(visit)


@router.post(
    path="/{visit_id}/finish",
    response_model=VisitResponse,
    dependencies=[Depends(allow_all_staff)],
)
async def finish_visit(
    visit_id: UUID,
    service: Annotated[VisitService, Depends(get_visits_service)],
):
    try:
        visit = await service.finish_visit(visit_id)
        return VisitResponse.model_validate(visit)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    path="/{visit_id}/cancel",
    response_model=VisitResponse,
    dependencies=[Depends(allow_all_staff)],
)
async def cancel_visit(
    visit_id: UUID,
    service: Annotated[VisitService, Depends(get_visits_service)],
):
    try:
        visit = await service.cancel_visit(visit_id)
        return VisitResponse.model_validate(visit)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    path="/{visit_id}",
    response_model=VisitResponse,
    dependencies=[Depends(allow_all_staff)],
)
async def get_visit(
    visit_id: UUID,
    service: Annotated[VisitService, Depends(get_visits_service)],
):
    visit = await service.get_visit(visit_id)
    return VisitResponse.model_validate(visit)


@router.get(
    path="/{visit_id}/details",
    response_model=VisitDetailsResponse,
    dependencies=[Depends(allow_all_staff)],
)
async def get_visit_details(
    visit_id: UUID,
    service: Annotated[VisitService, Depends(get_visits_service)],
):
    try:
        visit_details = await service.get_visit_details(visit_id)
        return VisitDetailsResponse.model_validate(visit_details)
    except VisitNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visit not found",
        )


@router.get(
    path="",
    response_model=list[VisitResponse],
    dependencies=[Depends(allow_all_staff)],
)
async def list_visits(
    service: Annotated[VisitService, Depends(get_visits_service)],
    employee_id: UUID | None = Query(None),
    retail_point_id: UUID | None = Query(None),
    visit_status: VisitStatus | None = Query(None, alias="status"),
):
    visits = await service.list(employee_id, retail_point_id, visit_status)
    return [VisitResponse.model_validate(v) for v in visits]


# ======================================================================
# 2. VISIT MEDIA
# ======================================================================


@router.post(
    path="/{visit_id}/media",
    response_model=VisitMediaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(allow_all_staff)],
)
async def attach_media(
    visit_id: UUID,
    dto: AttachMediaRequest,
    service: Annotated[VisitService, Depends(get_visits_service)],
):
    media = await service.attach_media(visit_id, dto.media_id)
    return VisitMediaResponse.model_validate(media)


@router.delete(
    path="/{visit_id}/media/{media_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(allow_all_staff)],
)
async def detach_media(
    visit_id: UUID,
    media_id: UUID,
    service: Annotated[VisitService, Depends(get_visits_service)],
):
    await service.detach_media(visit_id, media_id)


@router.get(
    path="/{visit_id}/media",
    response_model=list[VisitMediaResponse],
    dependencies=[Depends(allow_all_staff)],
)
async def list_visit_media(
    visit_id: UUID,
    service: Annotated[VisitMediaService, Depends(get_visit_media_service)],
):
    media_list = await service.list_media(visit_id)
    return [VisitMediaResponse.model_validate(m) for m in media_list]


# ======================================================================
# 3. VISIT DEBTS
# ======================================================================


@router.post(
    path="/{visit_id}/debts",
    response_model=VisitDebtResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(allow_all_staff)],
)
async def add_debt(
    visit_id: UUID,
    dto: AddDebtRequest,
    service: Annotated[VisitService, Depends(get_visits_service)],
):
    debt = await service.add_debt(visit_id, dto.amount, dto.comment)
    return VisitDebtResponse.model_validate(debt)


@router.patch(
    path="/debts/{debt_id}",
    response_model=VisitDebtResponse,
    dependencies=[Depends(allow_all_staff)],
)
async def update_debt(
    debt_id: UUID,
    dto: UpdateDebtRequest,
    service: Annotated[VisitService, Depends(get_visits_service)],
):
    debt = await service.update_debt(debt_id, dto.amount, dto.comment)
    return VisitDebtResponse.model_validate(debt)


@router.delete(
    path="/debts/{debt_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(allow_all_staff)],
)
async def delete_debt(
    debt_id: UUID,
    service: Annotated[VisitService, Depends(get_visits_service)],
):
    await service.delete_debt(debt_id)
