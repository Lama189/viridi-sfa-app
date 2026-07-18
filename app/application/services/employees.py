from uuid import UUID

from app.domain.entities.employees import Employee

from app.application.interfaces.uow import IUnitOfWork
from app.api.v1.schemas.employees import EmployeeCreate, EmployeeUpdate


class EmployeesService:

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def create_employee(self, dto: EmployeeCreate) -> Employee:
        if await self._uow.employees.exists_by(phone=dto.phone):
            raise ValueError(f"An employee with phone number '{dto.phone}' already exists.")

        employee = Employee(
            phone=dto.phone,
            password_hash=dto.password_hash,
            full_name=dto.full_name,
            role=dto.role,
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
