from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import (
    allow_admin,
    get_current_employee,
    get_employee_device_service,
    get_employees_auth_service,
    get_employees_service,
)
from app.api.v1.schemas.employee_devices import (
    DeviceResponse,
    RegisterDeviceRequest,
)
from app.api.v1.schemas.employees import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
    EmployeeWithTokensResponse,
)
from app.api.v1.schemas.employees import (
    EmployeeLoginDTO as SchemaEmployeeLoginDTO,
)
from app.api.v1.schemas.tokens import RefreshTokenDTO, TokenResponseDTO
from app.application.dto.employee_devices import RegisterDeviceDTO
from app.application.dto.employees import (
    EmployeeCreateDTO,
    EmployeeLoginDTO,
    EmployeeUpdateDTO,
)
from app.application.services.employee_devices import EmployeeDeviceService
from app.application.services.employees import EmployeesAuthService, EmployeesService
from app.domain.entities.auth import AuthenticatedEmployee
from app.domain.enums import EmployeeRole

router = APIRouter(prefix="/api/v1/employees", tags=["Employees"])


@router.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    response_model=EmployeeResponse,
    dependencies=[Depends(allow_admin)],
)
async def register(
    dto: EmployeeCreate,
    service: Annotated[EmployeesService, Depends(get_employees_service)],
):
    try:
        app_dto = EmployeeCreateDTO(
            phone=dto.phone,
            password=dto.password,
            full_name=dto.full_name,
            role=dto.role,
        )
        return await service.create_employee(app_dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    path="",
    status_code=status.HTTP_200_OK,
    response_model=list[EmployeeResponse],
    dependencies=[Depends(allow_admin)],
)
async def list_employees(
    service: Annotated[EmployeesService, Depends(get_employees_service)],
    role: EmployeeRole | None = Query(
        None, description="Фильтр по роли сотрудника (agent, admin, warehouse_worker)"
    ),
    is_active: bool | None = Query(None, description="Фильтр по активности"),
):
    filters: dict[str, Any] = {}
    if role is not None:
        filters["role"] = role
    if is_active is not None:
        filters["is_active"] = is_active
    return await service.list_employees(**filters)




@router.post(
    path="/login",
    status_code=status.HTTP_200_OK,
    response_model=EmployeeWithTokensResponse,
)
async def login(
    dto: SchemaEmployeeLoginDTO,
    service: Annotated[EmployeesAuthService, Depends(get_employees_auth_service)],
):
    app_dto = EmployeeLoginDTO(phone=dto.phone, password=dto.password)
    return await service.login(app_dto)


@router.post(
    path="/refresh",
    status_code=status.HTTP_200_OK,
    response_model=TokenResponseDTO,
)
async def refresh(
    dto: RefreshTokenDTO,
    service: Annotated[EmployeesAuthService, Depends(get_employees_auth_service)],
):
    try:
        return await service.refresh(dto.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


# ======================================================================
# FCM DEVICE TOKENS
# ======================================================================


@router.post(
    path="/fcm-token",
    status_code=status.HTTP_200_OK,
    response_model=DeviceResponse,
)
async def register_fcm_token(
    dto: RegisterDeviceRequest,
    employee: Annotated[AuthenticatedEmployee, Depends(get_current_employee)],
    device_service: Annotated[
        EmployeeDeviceService, Depends(get_employee_device_service)
    ],
):
    app_dto = RegisterDeviceDTO(
        employee_id=employee.id,
        fcm_token=dto.fcm_token,
        device_type=dto.device_type,
    )
    return await device_service.register_device(app_dto)


@router.delete(
    path="/fcm-token",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_fcm_token(
    employee: Annotated[AuthenticatedEmployee, Depends(get_current_employee)],
    device_service: Annotated[
        EmployeeDeviceService, Depends(get_employee_device_service)
    ],
    fcm_token: str = Query(..., min_length=10, max_length=512),
):
    await device_service.remove_device(fcm_token)


@router.get(
    path="/devices",
    status_code=status.HTTP_200_OK,
    response_model=list[DeviceResponse],
)
async def list_my_devices(
    employee: Annotated[AuthenticatedEmployee, Depends(get_current_employee)],
    device_service: Annotated[
        EmployeeDeviceService, Depends(get_employee_device_service)
    ],
):
    return await device_service.list_by_employee(employee.id)


@router.get(
    path="/{employee_id}",
    status_code=status.HTTP_200_OK,
    response_model=EmployeeResponse,
    dependencies=[Depends(allow_admin)],
)
async def get_employee(
    employee_id: UUID,
    service: Annotated[EmployeesService, Depends(get_employees_service)],
):
    employee = await service.get_employee(employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {employee_id} not found",
        )
    return employee


@router.patch(
    path="/{employee_id}",
    status_code=status.HTTP_200_OK,
    response_model=EmployeeResponse,
    dependencies=[Depends(allow_admin)],
)
async def update_employee(
    employee_id: UUID,
    dto: EmployeeUpdate,
    service: Annotated[EmployeesService, Depends(get_employees_service)],
):
    try:
        app_dto = EmployeeUpdateDTO(
            phone=dto.phone,
            password_hash=dto.password_hash,
            full_name=dto.full_name,
            role=dto.role,
            is_active=dto.is_active,
        )
        return await service.update_employee(employee_id, app_dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    path="/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(allow_admin)],
)
async def delete_employee(
    employee_id: UUID,
    service: Annotated[EmployeesService, Depends(get_employees_service)],
):
    try:
        await service.delete_employee(employee_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
