from collections.abc import Callable, Sequence

from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.application.interfaces.cache.rate_limiter import IRateLimiter
from app.core.observability.logging import logger


class RateLimitMiddleware(BaseHTTPMiddleware):

    def __init__(
        self,
        app: Callable,
        rate_limiter: IRateLimiter,
        default_limit: int = 100,
        default_window: int = 60,
        custom_rules: Sequence[tuple[str, int, int]] | None = None
    ) -> None:
        super().__init__(app)
        self._rate_limiter = rate_limiter
        self._default_limit = default_limit
        self._default_window = default_window
        self._custom_rules = sorted(custom_rules or [], key=lambda r: len(r[0]), reverse=True)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in ("/health", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)

        client_identifier = self._resolve_client_identifier(request)
        limit, window = self._resolve_rate_rules(request.url.path)
        redis_key = f"{client_identifier}:{request.url.path}"

        is_limited = await self._rate_limiter.allow(
            redis_key, 
            limit=limit,
            window=window
        )
        if is_limited:
            logger.warning(
                "Rate limit exceeded",
                client_id=client_identifier,
                path=request.url.path,
                limit=limit,
                window=window,
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Too Many Requests",
                    "message": f"Rate limit exceeded. Maximum {limit} requests per {window} seconds."
                },
                headers={
                    "Retry-After": str(window),
                },
            )

        return await call_next(request)

    def _resolve_client_identifier(self, request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarder-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        return request.client.host if request.client else "unknown"

    def _resolve_rate_rules(self, path: str) -> tuple[int, int]:
        for prefix, limit, window in self._custom_rules:
            if path.startswith(prefix):
                return limit, window

        return self._default_limit, self._default_window