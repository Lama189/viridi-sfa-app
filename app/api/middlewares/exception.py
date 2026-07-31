from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.observability.logging import logger


class ExceptionLoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)

        except Exception:
            logger.exception(
                "Unhandled exception",
                path=request.url.path,
                method=request.method,
            )
            raise
