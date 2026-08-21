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
    VisitPlanItemResponse,
    VisitPlanItemRetailPointResponse,
    VisitPlanResponse,
)
from app.application.interfaces.services.routes_generator import IRouteGenerationService
from app.application.services.visit_plans import VisitPlanService
from app.domain.entities.auth import AuthenticatedEmployee
from app.domain.entities.visit_plans import VisitPlan
from app.domain.enums import RouteGenerationStart

router = APIRouter(prefix="/api/v1/visit-plans", tags=["Visit Plans"])


async def _to_response(service: VisitPlanService, plan: VisitPlan) -> VisitPlanResponse:
    items: list[VisitPlanItemResponse] = []

    for item in plan.items:
        retail_point = await service._uow.retail_points.get_by_id(item.retail_point_id)

        items.append(
            VisitPlanItemResponse(
                order=item.order,
                status=item.status,
                retail_point_id=item.retail_point_id,
                retail_point=VisitPlanItemRetailPointResponse.model_validate(
                    retail_point
                ),
            )
        )

    return VisitPlanResponse(
        id=plan.id,
        employee_id=plan.employee_id,
        date=plan.plan_date,
        weekday=plan.weekday,
        status=plan.status,
        items=items,
    )


@router.get(
    path="/today",
    response_model=VisitPlanResponse,
)
async def get_today_plan(
    employee: Annotated[AuthenticatedEmployee, Depends(get_current_employee)],
    service: Annotated[VisitPlanService, Depends(get_visit_plans_service)],
):
    plan = await service.get_today_plan(employee.id)
    return await _to_response(service, plan)


@router.get(
    path="/{plan_date}",
    response_model=VisitPlanResponse,
)
async def get_plan_by_date(
    plan_date: date,
    employee: Annotated[AuthenticatedEmployee, Depends(get_current_employee)],
    service: Annotated[VisitPlanService, Depends(get_visit_plans_service)],
):
    plan = await service.get_by_employee_and_date(employee.id, plan_date)
    return await _to_response(service, plan)


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
    plan = await service.generate_for_employee(dto.employee_id, dto.plan_date)
    return await _to_response(service, plan)


@router.post(
    path="/generate-routes",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(allow_admin)],
)
async def generate_routes(
    service: Annotated[IRouteGenerationService, Depends(get_routes_generator_service)],
    from_date: Annotated[
        RouteGenerationStart,
        Query(
            alias="from",
            description="Start boundary for route generation: today, tomorrow, or next_week",
        ),
    ] = RouteGenerationStart.NEXT_WEEK,
) -> None:
    await service.generate(start=from_date)


@router.post(
    path="/clear-routes",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(allow_admin)],
)
async def clear_routes(
    service: Annotated[IRouteGenerationService, Depends(get_routes_generator_service)],
) -> None:
    await service.clear_all()
