from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.extensions import UserNotFoundError, InvalidPasswordError, UserNotActiveError
from app.application.services.employees import EmployeesService, EmployeesAuthService
from app.api.dependencies import get_employees_service, get_employees_auth_service, allow_admin
from app.api.v1.schemas.employees import (
    EmployeeUpdate, 
    EmployeeResponse, 
    EmployeeWithTokensResponse, 
    EmployeeLoginDTO
)



router = APIRouter(prefix="/api/v1/employees", tags=["Employees"])


@router.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    response_model=EmployeeResponse,
)
async def register(
    dto: EmployeeLoginDTO,
    service: Annotated[EmployeesService, Depends(get_employees_service)],
):
    try:
        return await service.create_employee(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    

@router.post(
    path="/login",
    status_code=status.HTTP_200_OK,
    response_model=EmployeeWithTokensResponse
)
async def login(
    dto: EmployeeLoginDTO,
    service: Annotated[EmployeesAuthService, Depends(get_employees_auth_service)],
):
    try:
        return await service.login(dto)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee with this phone number not found."
        )
    except InvalidPasswordError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password."
        )
    except UserNotActiveError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is inactive. Please contact your administrator."
        )


@router.patch(
    path="/{employee_id}",
    status_code=status.HTTP_200_OK,
    response_model=EmployeeResponse,
    dependencies=[Depends(allow_admin)]
)
async def update_employee(
    employee_id: UUID,
    dto: EmployeeUpdate,
    service: Annotated[EmployeesService, Depends(get_employees_service)],
):
    try:
        return await service.update_employee(employee_id, dto)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(e)
        )
    

@router.delete(
    path="/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(allow_admin)]
)
async def delete_employee(
    employee_id: UUID,
    service: Annotated[EmployeesService, Depends(get_employees_service)],
):
    try:
        await service.delete_employee(employee_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=str(e)
        )