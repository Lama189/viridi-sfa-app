from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.exceptions_handlers import register_exception_handlers
from app.api.middlewares import (
    ExceptionLoggingMiddleware,
    LoggingMiddleware,
    RateLimitMiddleware,
    RequestMiddleware,
    SecurityHeadersMiddleWare,
    TimingMiddleWare,
)
from app.api.v1.routers.categories import router as categories_router
from app.api.v1.routers.clients import router as clients_router
from app.api.v1.routers.dashboard import router as dashboard_router
from app.api.v1.routers.employees import router as employees_router
from app.api.v1.routers.media import router as media_router
from app.api.v1.routers.notifications import router as notifications_router
from app.api.v1.routers.orders import router as orders_router
from app.api.v1.routers.products import router as products_router
from app.api.v1.routers.retail_points import router as retail_points_router
from app.api.v1.routers.stocks import router as stocks_router
from app.api.v1.routers.visit_plans import router as visit_plans_router
from app.api.v1.routers.visits import router as visits_router
from app.api.v1.routers.warehouses import router as inventory_router
from app.core.config import get_settings
from app.core.observability.logging import configure_logging
from app.infrastructure.minio.bucket_initializer import ensure_buckets
from app.infrastructure.minio.client import get_minio_client
from app.infrastructure.redis.client import create_redis_client
from app.infrastructure.redis.repos.rate_limiter import RedisRateLimiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = get_minio_client()
    ensure_buckets(client)
    yield


configure_logging()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Viridi SFA API", version="0.1.0", lifespan=lifespan)

    redis_client = create_redis_client()
    redis_rate_limiter = RedisRateLimiter(client=redis_client)

    custum_rules = [
        ("/api/v1/employees/login", 5, 60),
        ("/api/v1/visit-plans/generate-routes", 2, 60),
    ]

    app.add_middleware(
        RateLimitMiddleware,
        rate_limiter=redis_rate_limiter,
        default_limit=100,
        default_window=60,
        custom_rules=custum_rules,
    )

    app.add_middleware(SecurityHeadersMiddleWare)
    app.add_middleware(TimingMiddleWare)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(ExceptionLoggingMiddleware)
    app.add_middleware(RequestMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    @app.get("/")
    async def root():
        return {
            "status": "ok",
            "message": "Welcome to Viridi SFA API! Database and migrations are ready.",
        }

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    app.include_router(categories_router)
    app.include_router(clients_router)
    app.include_router(employees_router)
    app.include_router(orders_router)
    app.include_router(inventory_router)
    app.include_router(stocks_router)
    app.include_router(products_router)
    app.include_router(retail_points_router)
    app.include_router(media_router)
    app.include_router(visits_router)
    app.include_router(visit_plans_router)
    app.include_router(notifications_router)
    app.include_router(dashboard_router)

    return app


app = create_app()
