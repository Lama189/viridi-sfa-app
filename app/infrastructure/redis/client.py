from redis import asyncio as aioredis
from redis.asyncio import Redis
from collections.abc import AsyncGenerator

from app.core.config import get_settings


settings = get_settings()


async def get_refis_client() -> AsyncGenerator[Redis, None]:
    client = aioredis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)

    try:
        yield client
    finally:
        await client.aclose()