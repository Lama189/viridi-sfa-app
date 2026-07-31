from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.context import req_id_ctx_var


class RequestMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())

        token = req_id_ctx_var.set(request_id)

        try:
            response = await call_next(request)
        finally:
            req_id_ctx_var.reset(token)

        response.headers["X-Request-ID"] = request_id

        return response