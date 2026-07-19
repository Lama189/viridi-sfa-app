from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis

from app.core.config import get_settings
from app.core.security import SecurityUtils
from app.domain.enums import EmployeeRole
from app.domain.entities.employees import Employee

from app.application.interfaces.clients_cache import IClientsCacheRepository
from app.application.interfaces.employees_cache import IEmployeesCacheRepository
from app.application.interfaces.uow import IUnitOfWork

from app.application.services.categories import CategoriesService
from app.application.services.clients import ClientsService, ClientsAuthService
from app.application.services.employees import EmployeesService, EmployeesAuthService
from app.application.services.products import ProductsService
from app.application.services.retail_points import RetailPointsService
from app.application.services.warehouses import WarehousesService

from app.infrastructure.context import client_id_ctx_var, employee_id_ctx_var
from app.infrastructure.postgres.uow import PostgresUnitOfWork
from app.infrastructure.redis.client import get_redis_client
from app.infrastructure.redis.repos.clients import ClientsRedisRepository
from app.infrastructure.redis.repos.employees import EmployeesRedisRepository

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/users/login")


# ======================================================================
# 1. DATABASE & UOW DEPENDENCIES
# ======================================================================

async def get_uow() -> AsyncGenerator[IUnitOfWork, None]:
    async with PostgresUnitOfWork() as uow:
        yield uow


# ======================================================================
# 3. REDIS REPOSITORIES DEPENDENCIES
# ======================================================================

async def get_clients_redis_repo(
    client: Annotated[Redis, Depends(get_redis_client)]
) -> IClientsCacheRepository:
    return ClientsRedisRepository(client)


async def get_employees_redis_repo(
    client: Annotated[Redis, Depends(get_redis_client)]
) -> IEmployeesCacheRepository:
    return EmployeesRedisRepository(client)


# ======================================================================
# 2. CORE BUSINESS SERVICES DEPENDENCIES
# ======================================================================

async def get_categories_service(uow: Annotated[IUnitOfWork, Depends(get_uow)]) -> CategoriesService:
    return CategoriesService(uow)


async def get_warehouses_service(uow: Annotated[IUnitOfWork, Depends(get_uow)]) -> WarehousesService:
    return WarehousesService(uow)


async def get_retail_points_service(uow: Annotated[IUnitOfWork, Depends(get_uow)]) -> RetailPointsService:
    return RetailPointsService(uow)


async def get_products_service(uow: Annotated[IUnitOfWork, Depends(get_uow)]) -> ProductsService:
    return ProductsService(uow)


async def get_clients_service(uow: Annotated[IUnitOfWork, Depends(get_uow)]) -> ClientsService:
    return ClientsService(uow)

async def get_clients_auth_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
    redis: Annotated[IClientsCacheRepository, Depends(get_clients_redis_repo)]
) -> ClientsAuthService:
    return ClientsAuthService(uow, redis)

async def get_employees_service(uow: Annotated[IUnitOfWork, Depends(get_uow)]) -> EmployeesService:
    return EmployeesService(uow)

async def get_employees_auth_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
    redis: Annotated[IEmployeesCacheRepository, Depends(get_employees_redis_repo)]
) -> EmployeesAuthService:
    return EmployeesAuthService(uow, redis)

# ======================================================================
# 4. AUTHENTICATION & CURRENT USER DEPENDENCIES
# ======================================================================

async def get_current_client(
    service: Annotated[ClientsService, Depends(get_clients_service)],
    redis: Annotated[IClientsCacheRepository, Depends(get_clients_redis_repo)],
    token: str = Depends(oauth2_scheme),
):
    payload = SecurityUtils.verify_token(token)

    client_id = payload.get("sub")
    client_id_ctx_var.set(str(client_id))

    cached_client = await redis.get_user(client_id)
    if cached_client:
        return cached_client
    
    db_client = await service.get_client(client_id)
    if not db_client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return db_client

async def get_current_employee(
    service: Annotated[EmployeesService, Depends(get_employees_service)],
    redis: Annotated[IEmployeesCacheRepository, Depends(get_employees_redis_repo)],
    token: str = Depends(oauth2_scheme),
):
    payload = SecurityUtils.verify_token(token)
    
    if payload.get("user_type") != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token type for this resource"
        )
        
    employee_id = payload.get("sub")
    employee_id_ctx_var.set(str(employee_id))

    cached_employee = await redis.get_employee(employee_id)
    if cached_employee:
        return cached_employee

    db_employee = await service.get_employee(employee_id)
    if not db_employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
        
    if not db_employee.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employee account is inactive"
        )
        
    return db_employee


# ======================================================================
# 5. USER ROLES DEPENDENCIES
# ======================================================================


class RoleChecker:
    def __init__(self, allowed_roles: list[EmployeeRole]) -> None:
        self.allowed_roles = allowed_roles

    async def __call__(
        self, 
        current_employee: Annotated[Employee, Depends(get_current_employee)]
    ) -> Employee:
        if current_employee.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You do not have the required permissions."
            )
        return current_employee
    
allow_admin = RoleChecker([EmployeeRole.ADMIN])
allow_agent = RoleChecker([EmployeeRole.AGENT])
allow_all_staff = RoleChecker([EmployeeRole.ADMIN, EmployeeRole.AGENT])