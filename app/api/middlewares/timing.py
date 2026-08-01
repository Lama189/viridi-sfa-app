from time import perf_counter

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.api.middlewares.get_route_path import get_route_path

from app.core.observability.metrics import (
    http_request_duration_seconds,
    http_requests_in_progress,
    http_requests_total
)


class TimingMiddleWare(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        http_requests_in_progress.inc()

        start = perf_counter()

        try:
            respose = await call_next(request)
            return respose
        finally:
            duration = perf_counter() - start
            
            path = get_route_path(request)

            http_requests_total.labels(
                method=request.method,
                path=path,
                status_code=(respose.status_code if "respose" in locals() else 500)
            ).inc()

            http_request_duration_seconds.labels(
                method=request.method,
                path=path,
            ).observe(duration)

            http_requests_in_progress.dec()
    