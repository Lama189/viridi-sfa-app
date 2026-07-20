from fastapi import FastAPI

from app.api.v1.routers.categories import router as categories_router
from app.api.v1.routers.clients import router as clients_router
from app.api.v1.routers.employees import router as employees_router
from app.api.v1.routers.warehouses import router as inventory_router
from app.api.v1.routers.products import router as products_router

app = FastAPI(
    title="Viridi SFA API",
    version="0.1.0",
)


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
app.include_router(inventory_router)
app.include_router(products_router)