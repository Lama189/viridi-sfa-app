from uuid import UUID

from sqlalchemy import select, update, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repos.retail_point_assignments import IRetailPointAssignmentRepository
from app.domain.entities.retail_point_assignments import RetailPointAssignment
from app.infrastructure.postgres.models.retail_point_assignments import RetailPointAssignment as RetailPointAssignmentModel


class PostgresRetailPointAssignmentRepository(IRetailPointAssignmentRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, assignment: RetailPointAssignment) -> None:
        model = self._to_model(assignment)
        self._session.add(model)
        await self._session.flush()

    async def add_many(self, assignments: list[RetailPointAssignment]) -> None:
        models = [self._to_model(a) for a in assignments]
        self._session.add_all(models)
        await self._session.flush()

    async def get_by_id(self, assignment_id: UUID) -> RetailPointAssignment | None:
        result = await self._session.execute(
            select(RetailPointAssignmentModel).where(
                RetailPointAssignmentModel.id == assignment_id,
            )
        )

        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def get_by_retail_point_id(self, retail_point_id: UUID) -> RetailPointAssignment | None:
        result = await self._session.execute(
            select(RetailPointAssignmentModel).where(
                RetailPointAssignmentModel.retail_point_id == retail_point_id,
            )
        )

        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def list_by_employee_id(self, employee_id: UUID) -> list[RetailPointAssignment]:
        result = await self._session.execute(
            select(RetailPointAssignmentModel).where(
                RetailPointAssignmentModel.employee_id == employee_id,
            )
        )

        return [self._to_domain(m) for m in result.scalars().all()]

    async def exists_by_retail_point_id(self, retail_point_id: UUID) -> bool:
        stmt = select(
            select(RetailPointAssignmentModel).where(
                RetailPointAssignmentModel.retail_point_id == retail_point_id,
            ).exists()
        )
        result = await self._session.execute(stmt)
        return bool(result.scalar())

    async def update(self, assignment: RetailPointAssignment) -> None:
        await self._session.execute(
            update(RetailPointAssignmentModel)
            .where(RetailPointAssignmentModel.id == assignment.id)
            .values(
                employee_id=assignment.employee_id,
            )
        )
        await self._session.flush()

    async def delete(self, assignment: RetailPointAssignment) -> None:
        await self._session.execute(
            sa_delete(RetailPointAssignmentModel).where(
                RetailPointAssignmentModel.id == assignment.id,
            )
        )
        await self._session.flush()

    def _to_domain(self, model: RetailPointAssignmentModel) -> RetailPointAssignment:
        return RetailPointAssignment(
            id=model.id,
            retail_point_id=model.retail_point_id,
            employee_id=model.employee_id,
        )

    def _to_model(self, assignment: RetailPointAssignment) -> RetailPointAssignmentModel:
        return RetailPointAssignmentModel(
            id=assignment.id,
            retail_point_id=assignment.retail_point_id,
            employee_id=assignment.employee_id,
        )
