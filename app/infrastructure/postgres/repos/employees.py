from uuid import UUID

from sqlalchemy import select, update, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repos.employees import IEmployeeRepository
from app.domain.entities.employees import Employee
from app.infrastructure.postgres.models.employees import Employee as EmployeeModel


class PostgresEmployeeRepository(IEmployeeRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, employee: Employee) -> None:
        model = self._to_model(employee)
        self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, employee_id: UUID) -> Employee | None:
        result = await self._session.execute(
            select(EmployeeModel).where(EmployeeModel.id == employee_id)
        )

        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def get_by(self, **kwargs) -> Employee | None:
        result = await self._session.execute(
            select(EmployeeModel).filter_by(**kwargs)
        )

        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def list_by(self, **kwargs) -> list[Employee]:
        stmt = select(EmployeeModel).filter_by(**kwargs)

        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def exists_by(self, **kwargs) -> bool:
        stmt = select(select(EmployeeModel).filter_by(**kwargs).exists())
        result = await self._session.execute(stmt)
        return bool(result.scalar())

    async def update(self, employee: Employee) -> None:
        await self._session.execute(
            update(EmployeeModel)
            .where(EmployeeModel.id == employee.id)
            .values(
                phone=employee.phone,
                password_hash=employee.password_hash,
                full_name=employee.full_name,
                role=employee.role,
                is_active=employee.is_active,
            )
        )
        await self._session.flush()

    async def delete(self, employee: Employee) -> None:
        await self._session.execute(
            sa_delete(EmployeeModel).where(EmployeeModel.id == employee.id)
        )
        await self._session.flush()

    def _to_domain(self, model: EmployeeModel) -> Employee:
        return Employee(
            id=model.id,
            phone=model.phone,
            password_hash=model.password_hash,
            full_name=model.full_name,
            role=model.role,
            is_active=model.is_active,
        )

    def _to_model(self, employee: Employee) -> EmployeeModel:
        return EmployeeModel(
            id=employee.id,
            phone=employee.phone,
            password_hash=employee.password_hash,
            full_name=employee.full_name,
            role=employee.role,
            is_active=employee.is_active,
        )
