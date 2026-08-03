from prometheus_client import Counter, Histogram, Gauge


# ============================================================================
# HTTP
# ============================================================================


http_requests_total = Counter(
    name="http_requests_total",
    documentation="Total number of HTTP requests.",
    labelnames=(
        "method",
        "path",
        "status_code"
    )
)

http_request_duration_seconds = Histogram(
    name="http_request_duration_seconds",
    documentation="HTTP request duration",
    labelnames=(
        "method",
        "path"
    )
)

http_requests_in_progress = Gauge(
    name="http_requests_in_progress",
    documentation="Current HTTP requests in progress"
)

http_exceptions_total = Counter(
    name="http_exceptions_total",
    documentation="Total number of unhandled exceptions.",
    labelnames=(
        "method",
        "path",
        "exception"
    )
)


# ============================================================================
# Business
# ============================================================================


retail_point_operations_total = Counter(
    name="retail_point_operations_total",
    documentation="Total number of retail point operations.",
    labelnames=("action",)
)

invite_code_operations_total = Counter(
    name="invite_code_operations_total",
    documentation="Total number of invite code operations.",
    labelnames=("action",)
)

media_operations_total = Counter(
    name="media_operations_total",
    documentation="Total number of media operations.",
    labelnames=("action",)
)

category_operations_total = Counter(
    name="category_operations_total",
    documentation="Total number of category operations.",
    labelnames=("action",)
)

product_operations_total = Counter(
    name="product_operations_total",
    documentation="Total number of product operations.",
    labelnames=("action",)
)

warehouse_operations_total = Counter(
    name="warehouse_operations_total",
    documentation="Total number of warehouse operations.",
    labelnames=("action",)
)

employee_operations_total = Counter(
    name="employee_operations_total",
    documentation="Total number of employee operations.",
    labelnames=("action",)
)

client_operations_total = Counter(
    name="client_operations_total",
    documentation="Total number of client operations.",
    labelnames=("action",)
)

retail_point_member_operations_total = Counter(
    name="retail_point_member_operations_total",
    documentation="Total number of retail point member operations.",
    labelnames=("action",)
)

retail_point_assignment_operations_total = Counter(
    name="retail_point_assignment_operations_total",
    documentation="Total number of retail point assignment operations.",
    labelnames=("action",)
)

visit_schedule_operations_total = Counter(
    name="visit_schedule_operations_total",
    documentation="Total number of visit schedule operations.",
    labelnames=("action",)
)


# ============================================================================
# Stock Operations Metrics
# ============================================================================


stock_operations_total = Counter(
    name="stock_operations_total",
    documentation="Total number of successful stock operations.",
    labelnames=("operation",),
)

stock_operation_units_total = Counter(
    name="stock_operation_units_total",
    documentation="Total number of physical product units involved in stock operations.",
    labelnames=("operation",),
)

stock_operation_failures_total = Counter(
    name="stock_operation_failures_total",
    documentation="Total number of failed stock operations.",
    labelnames=("operation", "reason"),
)

stock_operation_duration_seconds = Histogram(
    name="stock_operation_duration_seconds",
    documentation="Stock operation duration in seconds.",
    labelnames=("operation",),
)
