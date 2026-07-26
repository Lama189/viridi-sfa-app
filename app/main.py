from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.infrastructure.minio.client import get_minio_client
from app.infrastructure.minio.bucket_initializer import ensure_buckets

from app.api.exceptions_handlers import register_exception_handlers

from app.api.v1.routers.categories import router as categories_router
from app.api.v1.routers.clients import router as clients_router
from app.api.v1.routers.employees import router as employees_router
from app.api.v1.routers.orders import router as orders_router
from app.api.v1.routers.warehouses import router as inventory_router
from app.api.v1.routers.products import router as products_router
from app.api.v1.routers.retail_points import router as retail_points_router
from app.api.v1.routers.media import router as media_router
from app.api.v1.routers.visits import router as visits_router
from app.api.v1.routers.visit_plans import router as visit_plans_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = get_minio_client()

    ensure_buckets(client)

    yield


app = FastAPI(
    title="Viridi SFA API",
    version="0.1.0",
    lifespan=lifespan
)

register_exception_handlers(app)

@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Welcome to Viridi SFA API! Database and migrations are ready."
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


app.include_router(categories_router)
app.include_router(clients_router)
app.include_router(employees_router)
app.include_router(orders_router)
app.include_router(inventory_router)
app.include_router(products_router)
app.include_router(retail_points_router)
app.include_router(media_router)
app.include_router(visits_router)
app.include_router(visit_plans_router)