from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.exceptions_handlers import register_exception_handlers
from app.api.middlewares import (
    ExceptionLoggingMiddleware,
    LoggingMiddleware,
    RequestMiddleware,
    SecurityHeadersMiddleWare,
    TimingMiddleWare,
)
from app.api.v1.routers.categories import router as categories_router
from app.api.v1.routers.clients import router as clients_router
from app.api.v1.routers.dashboard import router as dashboard_router
from app.api.v1.routers.employees import router as employees_router
from app.api.v1.routers.media import router as media_router
from app.api.v1.routers.orders import router as orders_router
from app.api.v1.routers.products import router as products_router
from app.api.v1.routers.retail_points import router as retail_points_router
from app.api.v1.routers.stocks import router as stocks_router
from app.api.v1.routers.visit_plans import router as visit_plans_router
from app.api.v1.routers.visits import router as visits_router
from app.api.v1.routers.warehouses import router as inventory_router
from app.core.observability.logging import configure_logging
from app.infrastructure.minio.bucket_initializer import ensure_buckets
from app.infrastructure.minio.client import get_minio_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = get_minio_client()

    ensure_buckets(client)

    yield


configure_logging()

app = FastAPI(title="Viridi SFA API", version="0.1.0", lifespan=lifespan)

app.add_middleware(SecurityHeadersMiddleWare)
app.add_middleware(TimingMiddleWare)
app.add_middleware(LoggingMiddleware)
app.add_middleware(ExceptionLoggingMiddleware)
app.add_middleware(RequestMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
app.include_router(dashboard_router)
