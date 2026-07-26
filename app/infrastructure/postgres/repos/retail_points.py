from uuid import UUID

from sqlalchemy import select, update, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repos.retail_points import IRetailPointRepository
from app.domain.entities.retail_points import RetailPoint
from app.infrastructure.postgres.models.retail_points import RetailPoint as RetailPointModel
from app.infrastructure.postgres.models.retail_point_assignments import RetailPointAssignment as RetailPointAssignmentModel


class PostgresRetailPointRepository(IRetailPointRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, retail_point: RetailPoint) -> None:
        model = self._to_model(retail_point)
        self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, retail_point_id: UUID) -> RetailPoint | None:
        result = await self._session.execute(
            select(RetailPointModel).where(RetailPointModel.id == retail_point_id)
        )

        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def exists_by(self, **kwargs) -> bool:
        stmt = select(select(RetailPointModel).filter_by(**kwargs).exists())
        result = await self._session.execute(stmt)
        return bool(result.scalar())

    async def list_all(self, only_active: bool = True) -> list[RetailPoint]:
        stmt = select(RetailPointModel)
        if only_active:
            stmt = stmt.where(RetailPointModel.is_active.is_(True))

        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def update(self, retail_point: RetailPoint) -> None:
        await self._session.execute(
            update(RetailPointModel)
            .where(RetailPointModel.id == retail_point.id)
            .values(
                name=retail_point.name,
                legal_name=retail_point.legal_name,
                client_type=retail_point.client_type,
                address=retail_point.address,
                landmark=retail_point.landmark,
                contact_person=retail_point.contact_person,
                phone_number=retail_point.phone_number,
                inn=retail_point.inn,
                checking_account=retail_point.checking_account,
                bank_name=retail_point.bank_name,
                mfo=retail_point.mfo,
                oked=retail_point.oked,
                latitude=retail_point.latitude,
                longitude=retail_point.longitude,
                photo_id=retail_point.photo_id,
                visit_mon=retail_point.visit_mon,
                visit_tue=retail_point.visit_tue,
                visit_wed=retail_point.visit_wed,
                visit_thu=retail_point.visit_thu,
                visit_fri=retail_point.visit_fri,
                visit_sat=retail_point.visit_sat,
                visit_sun=retail_point.visit_sun,
                created_by_employee_id=retail_point.created_by_employee_id,
                is_active=retail_point.is_active,
            )
        )
        await self._session.flush()

    async def delete(self, retail_point: RetailPoint) -> None:
        await self._session.execute(
            sa_delete(RetailPointModel).where(RetailPointModel.id == retail_point.id)
        )
        await self._session.flush()

    async def list_by_employee(
        self,
        employee_id: UUID,
        only_active: bool = True,
    ) -> list[RetailPoint]:
        stmt = (
            select(RetailPointModel)
            .join(
                RetailPointAssignmentModel,
                RetailPointAssignmentModel.retail_point_id == RetailPointModel.id,
            )
            .where(
                RetailPointAssignmentModel.employee_id == employee_id,
            )
        )

        if only_active:
            stmt = stmt.where(RetailPointModel.is_active.is_(True))

        result = await self._session.execute(stmt)

        return [self._to_domain(model) for model in result.scalars().all()]
    
    def _to_domain(self, model: RetailPointModel) -> RetailPoint:
        return RetailPoint(
            id=model.id,
            name=model.name,
            legal_name=model.legal_name,
            client_type=model.client_type,
            address=model.address,
            landmark=model.landmark,
            contact_person=model.contact_person,
            phone_number=model.phone_number,
            inn=model.inn,
            checking_account=model.checking_account,
            bank_name=model.bank_name,
            mfo=model.mfo,
            oked=model.oked,
            latitude=model.latitude,
            longitude=model.longitude,
            photo_id=model.photo_id,
            visit_mon=model.visit_mon,
            visit_tue=model.visit_tue,
            visit_wed=model.visit_wed,
            visit_thu=model.visit_thu,
            visit_fri=model.visit_fri,
            visit_sat=model.visit_sat,
            visit_sun=model.visit_sun,
            created_by_employee_id=model.created_by_employee_id,
            is_active=model.is_active,
        )

    def _to_model(self, retail_point: RetailPoint) -> RetailPointModel:
        return RetailPointModel(
            id=retail_point.id,
            name=retail_point.name,
            legal_name=retail_point.legal_name,
            client_type=retail_point.client_type,
            address=retail_point.address,
            landmark=retail_point.landmark,
            contact_person=retail_point.contact_person,
            phone_number=retail_point.phone_number,
            inn=retail_point.inn,
            checking_account=retail_point.checking_account,
            bank_name=retail_point.bank_name,
            mfo=retail_point.mfo,
            oked=retail_point.oked,
            latitude=retail_point.latitude,
            longitude=retail_point.longitude,
            photo_id=retail_point.photo_id,
            visit_mon=retail_point.visit_mon,
            visit_tue=retail_point.visit_tue,
            visit_wed=retail_point.visit_wed,
            visit_thu=retail_point.visit_thu,
            visit_fri=retail_point.visit_fri,
            visit_sat=retail_point.visit_sat,
            visit_sun=retail_point.visit_sun,
            created_by_employee_id=retail_point.created_by_employee_id,
            is_active=retail_point.is_active,
        )
