from prometheus_client import Counter, Histogram, Gauge


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