from uuid import UUID

from app.domain.entities.employees import Employee
from app.core.extensions import UserNotFoundError, InvalidPasswordError, UserNotActiveError
from app.core.security import SecurityUtils

from app.application.interfaces.uow import IUnitOfWork
from app.application.interfaces.cache.employees_cache import IEmployeesCacheRepository
from app.api.v1.schemas.tokens import TokenResponseDTO
from app.api.v1.schemas.employees import (
    EmployeeCreate, 
    EmployeeUpdate, 
    EmployeeCachedDTO, 
    EmployeeLoginDTO,
    EmployeeResponse,
    EmployeeWithTokensResponse,
)

from app.infrastructure.context import employee_id_ctx_var


class EmployeesService:

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def create_employee(self, dto: EmployeeCreate) -> Employee:
        if await self._uow.employees.exists_by(phone=dto.phone):
            raise ValueError(f"An employee with phone number '{dto.phone}' already exists.")

        employee = Employee(
            phone=dto.phone,
            password_hash=SecurityUtils.hash_password(dto.password),
            full_name=dto.full_name,
            role=dto.role,
            is_active=False
        )

        await self._uow.employees.add(employee)
        await self._uow.commit()
        return employee

    async def get_employee(self, employee_id: UUID) -> Employee | None:
        return await self._uow.employees.get_by_id(employee_id)

    async def get_employee_by(self, **kwargs) -> Employee | None:
        return await self._uow.employees.get_by(**kwargs)

    async def list_employees(self, **kwargs) -> list[Employee]:
        return await self._uow.employees.list_by(**kwargs)

    async def update_employee(self, employee_id: UUID, dto: EmployeeUpdate) -> Employee:
        employee = await self._uow.employees.get_by_id(employee_id)
        if not employee:
            raise ValueError(f"Employee {employee_id} not found")

        if dto.phone is not None:
            existing = await self._uow.employees.get_by(phone=dto.phone)
            if existing and existing.id != employee_id:
                raise ValueError(f"Phone '{dto.phone}' is already in use")
            employee.phone = dto.phone

        if dto.password_hash is not None:
            employee.password_hash = dto.password_hash

        if dto.full_name is not None:
            employee.full_name = dto.full_name

        if dto.role is not None:
            employee.role = dto.role

        if dto.is_active is not None:
            employee.is_active = bool(dto.is_active)

        await self._uow.employees.update(employee)
        await self._uow.commit()
        return employee

    async def delete_employee(self, employee_id: UUID) -> None:
        employee = await self._uow.employees.get_by_id(employee_id)
        if not employee:
            raise ValueError(f"Employee {employee_id} not found")

        await self._uow.employees.delete(employee)
        await self._uow.commit()


class EmployeesAuthService:

    def __init__(self, uow: IUnitOfWork, cache: IEmployeesCacheRepository) -> None:
        self._uow = uow
        self._cache = cache

    async def _generate_auth_session(self, employee: Employee) -> TokenResponseDTO:
        employee_id_str = str(employee.id)
        employee_id_ctx_var.set(employee_id_str)

        payload = {
            "sub": employee_id_str,
            "role": employee.role.value,           
            "phone": employee.phone, 
            "user_type": "employee"             
        }
        access_token = SecurityUtils.generate_access_token(payload)
        refresh_token = SecurityUtils.generate_refresh_token(payload)

        await self._cache.set_refresh_token(
            employee_id=employee_id_str,
            token=refresh_token
        )

        await self._cache.set_employee(
            employee_id=employee_id_str,
            employee=EmployeeCachedDTO.model_validate(employee)
        )

        return TokenResponseDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=employee.id
        )
    
    async def login(self, dto: EmployeeLoginDTO) -> EmployeeWithTokensResponse:
        employee = await self._uow.employees.get_by(phone=dto.phone)
        if not employee:
            raise UserNotFoundError()
        
        if not SecurityUtils.verify_password(dto.password, employee.password_hash):
            raise InvalidPasswordError()
        
        if not employee.is_active:
            raise UserNotActiveError()
        
        tokens = await self._generate_auth_session(employee)

        return EmployeeWithTokensResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            employee=EmployeeResponse.model_validate(employee)
        )

    async def refresh(self, refresh_token: str) -> TokenResponseDTO:
        payload = SecurityUtils.verify_token(refresh_token, expected_type="refresh")
        employee_id = payload.get("sub")

        employee_id_ctx_var.set(str(employee_id))

        stored_token = await self._cache.get_refresh_token(employee_id)
        if not stored_token or stored_token != refresh_token:
            raise ValueError("Refresh token is invalid")
        
        new_access = SecurityUtils.generate_access_token({
            "sub": employee_id,
            "role": payload.get("role"),
            "phone": payload.get("phone"),
            "user_type": "employee"
        })

        return TokenResponseDTO(
            access_token=new_access,
            refresh_token=refresh_token,
            user_id=UUID(employee_id)
        )
    
    async def logout(self, employee_id: str) -> None:
        await self._cache.delete_refresh_token(employee_id)
        await self._cache.delete_employee(employee_id)