from contextvars import ContextVar


req_id_ctx_var: ContextVar[str | None] = ContextVar("request_id", default=None)
client_id_ctx_var: ContextVar[str | None] = ContextVar("client_id", default=None)
employee_id_ctx_var: ContextVar[str | None] = ContextVar("employee_id", default=None)


def get_request_id() -> str:
    return req_id_ctx_var.get() or "unknown"


def get_current_user_id() -> str:
    return client_id_ctx_var.get() or "anonymous"
