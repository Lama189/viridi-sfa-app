import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class TimingMiddleWare(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        started = time.perf_counter()

        response = call_next(request)

        duration = time.perf_counter() - started

        request.state.duration = duration

        return response
    