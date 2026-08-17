from dataclasses import asdict
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import (
    allow_admin,
    allow_all_staff,
    get_orders_service,
    get_retail_point_assignment_service,
    get_retail_point_members_service,
    get_retail_points_service,
    get_visit_debts_service,
)
from app.api.v1.schemas.orders import OrderResponse
from app.api.v1.schemas.retail_points import (
    AssignAgentRequest,
    BulkCreateRetailPointsResponse,
    CreateRetailPointRequest,
    InviteCodeResponse,
    RetailPointAssignmentResponse,
    RetailPointDetailsResponse,
    RetailPointMemberResponse,
    RetailPointResponse,
    RetailPointWithCodeResponse,
    UpdateRetailPointRequest,
)
from app.api.v1.schemas.visits import VisitDebtResponse
from app.application.dto.retail_points import (
    RetailPointCreateDTO,
    RetailPointUpdateDTO,
    VisitsDatesDTO,
)
from app.application.interfaces.services.retail_point_assignments import (
    IRetailPointAssignmentService,
)
from app.application.interfaces.services.visit_debts import IVisitDebtService
from app.application.services.members import RetailPointMembersService
from app.application.services.orders import OrdersService
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
        visits_dto = VisitsDatesDTO(
            mon=dto.visits.mon,
            tue=dto.visits.tue,
            wed=dto.visits.wed,
            thu=dto.visits.thu,
            fri=dto.visits.fri,
            sat=dto.visits.sat,
            sun=dto.visits.sun,
        )
        app_dto = RetailPointCreateDTO(
            name=dto.name,
            address=dto.address,
            legal_name=dto.legal_name,
            client_type=dto.client_type,
            landmark=dto.landmark,
            contact_person=dto.contact_person,
            phone_number=dto.phone_number,
            inn=dto.inn,
            checking_account=dto.checking_account,
            bank_name=dto.bank_name,
            mfo=dto.mfo,
            oked=dto.oked,
            latitude=dto.latitude,
            longitude=dto.longitude,
            photo_id=dto.photo_id,
            visits=visits_dto,
        )
        point, invite_code = await service.create_retail_point(app_dto, employee.id)

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
        app_dtos = [
            RetailPointCreateDTO(
                name=p.name,
                address=p.address,
                legal_name=p.legal_name,
                client_type=p.client_type,
                landmark=p.landmark,
                contact_person=p.contact_person,
                phone_number=p.phone_number,
                inn=p.inn,
                checking_account=p.checking_account,
                bank_name=p.bank_name,
                mfo=p.mfo,
                oked=p.oked,
                latitude=p.latitude,
                longitude=p.longitude,
                photo_id=p.photo_id,
                visits=VisitsDatesDTO(
                    mon=p.visits.mon,
                    tue=p.visits.tue,
                    wed=p.visits.wed,
                    thu=p.visits.thu,
                    fri=p.visits.fri,
                    sat=p.visits.sat,
                    sun=p.visits.sun,
                ),
            )
            for p in dto
        ]
        result = await service.bulk_create(employee.id, app_dtos)

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
    "/{retail_point_id}/details",
    response_model=RetailPointDetailsResponse,
    dependencies=[Depends(allow_all_staff)],
)
async def get_retail_point_details(
    retail_point_id: UUID,
    service: Annotated[RetailPointsService, Depends(get_retail_points_service)],
):
    details = await service.get_details(retail_point_id)
    return RetailPointDetailsResponse.model_validate(details)


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
        visits_dto = (
            VisitsDatesDTO(
                mon=dto.visits.mon,
                tue=dto.visits.tue,
                wed=dto.visits.wed,
                thu=dto.visits.thu,
                fri=dto.visits.fri,
                sat=dto.visits.sat,
                sun=dto.visits.sun,
            )
            if dto.visits is not None
            else None
        )
        app_dto = RetailPointUpdateDTO(
            name=dto.name,
            legal_name=dto.legal_name,
            client_type=dto.client_type,
            address=dto.address,
            landmark=dto.landmark,
            contact_person=dto.contact_person,
            phone_number=dto.phone_number,
            inn=dto.inn,
            checking_account=dto.checking_account,
            bank_name=dto.bank_name,
            mfo=dto.mfo,
            oked=dto.oked,
            latitude=dto.latitude,
            longitude=dto.longitude,
            photo_id=dto.photo_id,
            visits=visits_dto,
            is_active=dto.is_active,
        )
        return await service.update_retail_point(retail_point_id, app_dto)
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


@router.get(
    "/{retail_point_id}/orders",
    response_model=list[OrderResponse],
    dependencies=[Depends(allow_all_staff)],
)
async def list_retail_point_orders(
    retail_point_id: UUID,
    service: Annotated[OrdersService, Depends(get_orders_service)],
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
