from uuid import UUID

from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select, tuple_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repos.retail_points import IRetailPointRepository
from app.domain.entities.retail_points import RetailPoint, RetailPointIdentity
from app.domain.enums import Weekday
from app.infrastructure.postgres.models.retail_point_assignments import (
    RetailPointAssignment as RetailPointAssignmentModel,
)
from app.infrastructure.postgres.models.retail_points import (
    RetailPoint as RetailPointModel,
)
from app.infrastructure.postgres.models.visit_schedule_rules import (
    VisitScheduleRule as VisitScheduleRuleModel,
)


class PostgresRetailPointRepository(IRetailPointRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, retail_point: RetailPoint) -> None:
        model = self._to_model(retail_point)
        self._session.add(model)
        await self._session.flush()

    async def add_many(self, retail_points: list[RetailPoint]) -> None:
        models = [self._to_model(rp) for rp in retail_points]
        self._session.add_all(models)
        await self._session.flush()

    async def find_existing_by_identity(
        self,
        identities: list[RetailPointIdentity],
    ) -> dict[RetailPointIdentity, UUID]:
        if not identities:
            return {}

        criteria = [(i.name, i.address) for i in identities]

        result = await self._session.execute(
            select(
                RetailPointModel.id,
                RetailPointModel.name,
                RetailPointModel.address,
            ).where(
                tuple_(
                    func.lower(RetailPointModel.name),
                    func.lower(RetailPointModel.address),
                ).in_(criteria)
            )
        )

        rows = result.all()
        identity_map = {
            RetailPointIdentity(name=row.name, address=row.address): row.id
            for row in rows
        }

        return identity_map

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

    async def list_by(self, **kwargs) -> list[RetailPoint]:
        stmt = select(RetailPointModel).filter_by(**kwargs)

        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

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

    async def list_by_employee_and_weekday(
        self,
        employee_id: UUID,
        weekday: Weekday,
        only_active: bool = True,
    ) -> list[RetailPoint]:
        weekday_val = weekday.value if isinstance(weekday, Weekday) else int(weekday)
        stmt = (
            select(RetailPointModel)
            .join(
                RetailPointAssignmentModel,
                RetailPointAssignmentModel.retail_point_id == RetailPointModel.id,
            )
            .join(
                VisitScheduleRuleModel,
                VisitScheduleRuleModel.retail_point_id == RetailPointModel.id,
            )
            .where(
                RetailPointAssignmentModel.employee_id == employee_id,
                VisitScheduleRuleModel.weekday == weekday_val,
                VisitScheduleRuleModel.is_active.is_(True),
            )
        )

        if only_active:
            stmt = stmt.where(RetailPointModel.is_active.is_(True))

        result = await self._session.execute(stmt)

        return [self._to_domain(model) for model in result.scalars().all()]

    async def list_paginated(
        self,
        employee_id: UUID,
        limit: int,
        offset: int,
    ) -> list[RetailPoint]:
        stmt = select(RetailPointModel).limit(limit).offset(offset)
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
            created_by_employee_id=retail_point.created_by_employee_id,
            is_active=retail_point.is_active,
        )
