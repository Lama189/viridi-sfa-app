import logging

from redis.asyncio import Redis, RedisError

from app.core.config import get_settings
from app.api.v1.schemas.users import UserCachedDTO
from app.application.interfaces.clients_cache import IClientsCacheRepository


settings = get_settings()
logger = logging.getLogger(__name__)


class ClientsRedisRepository(IClientsCacheRepository):
    def __init__(self, client: Redis) -> None:
        self._client = client

    async def get_refresh_token(self, client_id: str) -> str | None:
        try:
            token = await self._client.get(f"refresh_token:{client_id}")
            return str(token) if token else None
        except RedisError as e:
            logger.error(f"Failed to get refresh_token for {client_id}: {e}")
            return None

    async def set_refresh_token(
        self,
        client_id: str,
        token: str,
        expire_days: int = settings.refresh_token_expire_days,
    ) -> None:
        try:
            await self._client.set(
                f"refresh_token:{client_id}",
                token,
                ex=expire_days * 24 * 60 * 60,
            )
        except RedisError as e:
            logger.error(f"Failed to set refresh_token for {client_id}: {e}")

    async def delete_refresh_token(self, client_id: str) -> None:
        try:
            await self._client.delete(f"refresh_token:{client_id}")
        except RedisError as e:
            logger.error(f"Failed to delete refresh_token for {client_id}: {e}")

    async def set_user(
        self,
        client_id: str,
        user: UserCachedDTO,
        expire_seconds: int = 900,
    ) -> None:
        try:
            await self._client.set(
                f"user:{client_id}",
                user.model_dump_json(),
                ex=expire_seconds,
            )
        except RedisError as e:
            logger.error(f"Failed to set user for {client_id}: {e}")

    async def get_user(self, client_id: str) -> UserCachedDTO | None:
        try:
            user_json = await self._client.get(f"user:{client_id}")
            if not user_json:
                return None
            return UserCachedDTO.model_validate_json(user_json)
        except RedisError as e:
            logger.error(f"Failed to get user for {client_id}: {e}")
            return None

    async def delete_user(self, client_id: str) -> None:
        try:
            await self._client.delete(f"user:{client_id}")
        except RedisError as e:
            logger.error(f"Failed to delete user for {client_id}: {e}")
