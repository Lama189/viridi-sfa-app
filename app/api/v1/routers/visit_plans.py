from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import (
    allow_admin,
    get_current_employee,
    get_routes_generator_service,
    get_visit_plans_service,
)
from app.api.v1.schemas.visit_plans import (
    GenerateVisitPlanRequest,
    VisitPlanResponse,
)
from app.application.interfaces.services.routes_generator import IRouteGenerationService
from app.application.services.visit_plans import VisitPlanService
from app.domain.entities.auth import AuthenticatedEmployee
from app.domain.enums import RouteGenerationStart

router = APIRouter(prefix="/api/v1/visit-plans", tags=["Visit Plans"])


@router.get(
    path="/today",
    response_model=VisitPlanResponse,
)
async def get_today_plan(
    employee: Annotated[AuthenticatedEmployee, Depends(get_current_employee)],
    service: Annotated[VisitPlanService, Depends(get_visit_plans_service)],
):
    return await service.get_today_plan_dto(employee.id)


@router.get(
    path="/{plan_date}",
    response_model=VisitPlanResponse,
)
async def get_plan_by_date(
    plan_date: date,
    employee: Annotated[AuthenticatedEmployee, Depends(get_current_employee)],
    service: Annotated[VisitPlanService, Depends(get_visit_plans_service)],
):
    return await service.get_plan_by_date_dto(employee.id, plan_date)


@router.post(
    path="/generate",
    response_model=VisitPlanResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(allow_admin)],
)
async def generate_visit_plan(
    dto: GenerateVisitPlanRequest,
    service: Annotated[VisitPlanService, Depends(get_visit_plans_service)],
):
    return await service.generate_for_employee_dto(dto.employee_id, dto.plan_date)


@router.post(
    path="/generate-routes",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(allow_admin)],
)
async def generate_routes(
    service: Annotated[IRouteGenerationService, Depends(get_routes_generator_service)],
    from_date: Annotated[
        RouteGenerationStart | None,
        Query(
            alias="from",
            description="Start boundary for route generation: today, tomorrow, or next_week",
        ),
    ] = None,
    start: Annotated[
        RouteGenerationStart | None,
        Query(
            description="Alias for 'from' parameter: today, tomorrow, or next_week",
        ),
    ] = None,
) -> None:
    target_start = from_date or start or RouteGenerationStart.NEXT_WEEK
    await service.generate(start=target_start)


@router.post(
    path="/clear-routes",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(allow_admin)],
)
async def clear_routes(
    service: Annotated[IRouteGenerationService, Depends(get_routes_generator_service)],
) -> None:
    await service.clear_all()
