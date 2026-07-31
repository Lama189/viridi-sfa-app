import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.observability.logging import logger
from app.core.context import get_request_id


class LoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        started = time.perf_counter()

        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            request_id=get_request_id()
        )

        response = await call_next(request)

        clapsed = round((time.perf_counter() - started) * 1000, 2)

        logger.info(
            "Request finished",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=clapsed,
            request_id=get_request_id()
        )

        return response
