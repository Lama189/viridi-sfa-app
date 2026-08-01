from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.observability.logging import logger
from app.core.observability.metrics import http_exceptions_total

from app.api.middlewares.get_route_path import get_route_path


class ExceptionLoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)

        except Exception as exc:
            path = get_route_path(request)

            http_exceptions_total.labels(
                method=request.method,
                path=path,
                exception=exc.__class__.__name__
            )

            logger.exception(
                "Unhandled exception",
                path=request.url.path,
                method=request.method,
            )
            
            raise
