from abc import ABC


class IRateLimiter(ABC):

    async def allow(self, key: str, limit: int, window: int) -> bool:
        raise NotImplementedError