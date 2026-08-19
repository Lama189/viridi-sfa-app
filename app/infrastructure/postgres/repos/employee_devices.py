from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repos.employee_devices import (
    IEmployeeDeviceRepository,
)
from app.domain.entities.employee_devices import EmployeeDevice
from app.infrastructure.postgres.models.employee_devices import (
    EmployeeDevice as EmployeeDeviceModel,
)


class PostgresEmployeeDeviceRepository(IEmployeeDeviceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_or_update(self, device: EmployeeDevice) -> None:
        result = await self._session.execute(
            select(EmployeeDeviceModel).where(
                EmployeeDeviceModel.fcm_token == device.fcm_token
            )
        )
        model = result.scalar_one_or_none()
        if model:
            model.employee_id = device.employee_id
            model.device_type = device.device_type
            model.updated_at = datetime.now(UTC)
        else:
            model = self._to_model(device)
            self._session.add(model)
        await self._session.flush()

    async def list_by_employee(self, employee_id: UUID) -> list[EmployeeDevice]:
        result = await self._session.execute(
            select(EmployeeDeviceModel).where(
                EmployeeDeviceModel.employee_id == employee_id
            )
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def delete_by_token(self, fcm_token: str) -> None:
        await self._session.execute(
            sa_delete(EmployeeDeviceModel).where(
                EmployeeDeviceModel.fcm_token == fcm_token
            )
        )
        await self._session.flush()

    async def delete_by_tokens(self, tokens: list[str]) -> None:
        if not tokens:
            return
        await self._session.execute(
            sa_delete(EmployeeDeviceModel).where(
                EmployeeDeviceModel.fcm_token.in_(tokens)
            )
        )
        await self._session.flush()

    async def delete_by_employee(self, employee_id: UUID) -> None:
        await self._session.execute(
            sa_delete(EmployeeDeviceModel).where(
                EmployeeDeviceModel.employee_id == employee_id
            )
        )
        await self._session.flush()

    def _to_domain(self, model: EmployeeDeviceModel) -> EmployeeDevice:
        return EmployeeDevice(
            id=model.id,
            employee_id=model.employee_id,
            fcm_token=model.fcm_token,
            device_type=model.device_type,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, device: EmployeeDevice) -> EmployeeDeviceModel:
        return EmployeeDeviceModel(
            id=device.id,
            employee_id=device.employee_id,
            fcm_token=device.fcm_token,
            device_type=device.device_type,
            created_at=device.created_at,
            updated_at=device.updated_at,
        )
