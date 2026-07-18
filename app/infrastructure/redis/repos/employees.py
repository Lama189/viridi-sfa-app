import logging
from uuid import UUID

from redis.asyncio import Redis, RedisError

from app.core.config import get_settings
from app.api.v1.schemas.employees import EmployeeCachedDTO
from app.application.interfaces.employees_cache import IEmployeesCacheRepository


settings = get_settings()
logger = logging.getLogger(__name__)


class EmployeesRedisRepository(IEmployeesCacheRepository):
    def __init__(self, client: Redis) -> None:
        self._client = client

    async def get_refresh_token(self, employee_id: UUID) -> str | None:
        try:
            token = await self._client.get(f"refresh_token:{employee_id}")
            return str(token) if token else None
        except RedisError as e:
            logger.error(f"Failed to get refresh_token for {employee_id}: {e}")
            return None

    async def set_refresh_token(
        self,
        employee_id: UUID,
        token: str,
        expire_days: int = settings.refresh_token_expire_days,
    ) -> None:
        try:
            await self._client.set(
                f"refresh_token:{employee_id}",
                token,
                ex=expire_days * 24 * 60 * 60,
            )
        except RedisError as e:
            logger.error(f"Failed to set refresh_token for {employee_id}: {e}")

    async def delete_refresh_token(self, employee_id: UUID) -> None:
        try:
            await self._client.delete(f"refresh_token:{employee_id}")
        except RedisError as e:
            logger.error(f"Failed to delete refresh_token for {employee_id}: {e}")

    async def set_employee(
        self,
        employee_id: UUID,
        employee: EmployeeCachedDTO,
        expire_seconds: int = 900,
    ) -> None:
        try:
            await self._client.set(
                f"employee:{employee_id}",
                employee.model_dump_json(),
                ex=expire_seconds,
            )
        except RedisError as e:
            logger.error(f"Failed to set employee for {employee_id}: {e}")

    async def get_employee(self, employee_id: UUID) -> EmployeeCachedDTO | None:
        try:
            employee_json = await self._client.get(f"employee:{employee_id}")
            if not employee_json:
                return None
            return EmployeeCachedDTO.model_validate_json(employee_json)
        except RedisError as e:
            logger.error(f"Failed to get employee for {employee_id}: {e}")
            return None

    async def delete_employee(self, employee_id: UUID) -> None:
        try:
            await self._client.delete(f"employee:{employee_id}")
        except RedisError as e:
            logger.error(f"Failed to delete employee for {employee_id}: {e}")
