import time
from pathlib import Path
from uuid import uuid4

from redis.asyncio import Redis, RedisError

from app.application.interfaces.cache.rate_limiter import IRateLimiter
from app.core.context import get_request_id
from app.core.observability.logging import logger

_LUA_SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "sliding_window.lua"
_SLIDING_WINDOW_LUA_SCRIPT = _LUA_SCRIPT_PATH.read_text(encoding="utf-8")


class RadisRateLimiter(IRateLimiter):

    def __init__(self, client: Redis) -> None:
        self._client = client
        self._script = self._client.register_script(_SLIDING_WINDOW_LUA_SCRIPT)

    async def allow(self, key: str, limit: int, window: int) -> bool:
        if limit <= 0:
            return True

        if window <= 0:
            raise ValueError("Window must be greater than zero")

        now = time.time()
        request_id = get_request_id() or uuid4().hex

        try:
            result = await self._script(
                keys=[f"rate_limit:{key}"],
                args=[now, window, limit, request_id]
            )
            return bool(result)
        except RedisError as e:
            logger.error(f"Failed to check rate limit for key {key}: {e}")
            return False
    
