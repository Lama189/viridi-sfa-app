from dataclasses import asdict
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import (
    allow_admin,
    allow_all_staff,
    get_retail_point_assignment_service,
    get_retail_point_members_service,
    get_retail_points_service,
    get_visit_debts_service,
)
from app.api.v1.schemas.retail_points import (
    AssignAgentRequest,
    BulkCreateRetailPointsResponse,
    CreateRetailPointRequest,
    InviteCodeResponse,
    RetailPointAssignmentResponse,
    RetailPointMemberResponse,
    RetailPointResponse,
    RetailPointWithCodeResponse,
    UpdateRetailPointRequest,
)
from app.api.v1.schemas.visits import VisitDebtResponse
from app.application.interfaces.services.retail_point_assignments import (
    IRetailPointAssignmentService,
)
from app.application.interfaces.services.visit_debts import IVisitDebtService
from app.application.services.members import RetailPointMembersService
from app.application.services.retail_points import RetailPointsService
from app.domain.entities.auth import AuthenticatedEmployee
from app.domain.enums import Weekday

router = APIRouter(prefix="/api/v1/retail_points", tags=["RetailPoints"])


@router.get(
    "/by-weekday/{weekday}",
    response_model=list[RetailPointResponse],
)
async def list_retail_points_by_weekday(
    weekday: Weekday,
    employee: Annotated[AuthenticatedEmployee, Depends(allow_all_staff)],
    service: Annotated[RetailPointsService, Depends(get_retail_points_service)],
):
    return await service.list_by_employee_and_weekday(
        employee_id=employee.id,
        weekday=weekday,
    )


@router.post(
    path="",
    response_model=RetailPointWithCodeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_retail_point(
    dto: CreateRetailPointRequest,
    service: Annotated[RetailPointsService, Depends(get_retail_points_service)],
    employee: Annotated[AuthenticatedEmployee, Depends(allow_all_staff)],
):
    try:
        point, invite_code = await service.create_retail_point(dto, employee.id)

        return RetailPointWithCodeResponse(
            retail_point=asdict(point), invite_code=invite_code
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.post(
    path="/bulk",
    response_model=BulkCreateRetailPointsResponse,
    status_code=status.HTTP_201_CREATED,
)
async def bulk_create_retail_points(
    dto: list[CreateRetailPointRequest],
    service: Annotated[RetailPointsService, Depends(get_retail_points_service)],
    employee: Annotated[AuthenticatedEmployee, Depends(allow_admin)],
):
    try:
        result = await service.bulk_create(employee.id, dto)

        return BulkCreateRetailPointsResponse(
            created_count=result.created_count, created=result.created
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/{retail_point_id}", response_model=RetailPointResponse)
async def get_retail_point(
    retail_point_id: UUID,
    service: Annotated[RetailPointsService, Depends(get_retail_points_service)],
):
    return await service.get_by_id(retail_point_id)


@router.get(
    "/{retail_point_id}/code",
    response_model=InviteCodeResponse,
    dependencies=[Depends(allow_all_staff)],
)
async def get_retail_point_invite_code(
    retail_point_id: UUID,
    service: Annotated[RetailPointsService, Depends(get_retail_points_service)],
):
    invite_code = await service.get_retail_point_invite_code(retail_point_id)

    return InviteCodeResponse(invite_code=invite_code)


@router.patch(
    "/{retail_point_id}",
    response_model=RetailPointResponse,
    dependencies=[Depends(allow_all_staff)],
)
async def update_retail_point(
    retail_point_id: UUID,
    dto: UpdateRetailPointRequest,
    service: Annotated[RetailPointsService, Depends(get_retail_points_service)],
):
    try:
        return await service.update_retail_point(retail_point_id, dto)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete(
    "/{retail_point_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(allow_admin)],
)
async def delete_retail_point(
    retail_point_id: UUID,
    service: Annotated[RetailPointsService, Depends(get_retail_points_service)],
):
    await service.delete_retail_point(retail_point_id)


@router.get(
    "",
    response_model=list[RetailPointResponse],
)
async def list_retail_points(
    service: Annotated[RetailPointsService, Depends(get_retail_points_service)],
    employee: Annotated[AuthenticatedEmployee, Depends(allow_all_staff)],
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
):
    return await service.list_retail_points(
        employee_id=employee.id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{retail_point_id}/members",
    response_model=list[RetailPointMemberResponse],
)
async def list_retail_point_members(
    retail_point_id: UUID,
    service: Annotated[
        RetailPointMembersService, Depends(get_retail_point_members_service)
    ],
):
    return await service.list_members(retail_point_id)


@router.get(
    "/{retail_point_id}/debts",
    response_model=list[VisitDebtResponse],
    dependencies=[Depends(allow_all_staff)],
)
async def list_retail_point_debts(
    retail_point_id: UUID,
    service: Annotated[IVisitDebtService, Depends(get_visit_debts_service)],
):
    return await service.list_by_retail_point(retail_point_id)


@router.post(
    "/{retail_point_id}/assign-agent",
    response_model=RetailPointAssignmentResponse,
    dependencies=[Depends(allow_all_staff)],
)
async def assign_agent_to_retail_point(
    retail_point_id: UUID,
    dto: AssignAgentRequest,
    service: Annotated[
        IRetailPointAssignmentService, Depends(get_retail_point_assignment_service)
    ],
):
    try:
        return await service.assign_employee(retail_point_id, dto.employee_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

