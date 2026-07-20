from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis

from app.core.config import get_settings
from app.core.security import SecurityUtils
from app.domain.enums import EmployeeRole
from app.domain.entities.employees import Employee
from app.domain.entities.clients import Client

from app.application.interfaces.cache.clients_cache import IClientsCacheRepository
from app.application.interfaces.cache.employees_cache import IEmployeesCacheRepository
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

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    clients_service: Annotated[ClientsService, Depends(get_clients_service)],
    employees_service: Annotated[EmployeesService, Depends(get_employees_service)],
    clients_cache: Annotated[IClientsCacheRepository, Depends(get_clients_redis_repo)],
    employees_cache: Annotated[IEmployeesCacheRepository, Depends(get_employees_redis_repo)],
):
    payload = SecurityUtils.verify_token(token)

    user_type = payload["user_type"]
    user_id = payload["sub"]

    if user_type == "client":
        client_id_ctx_var.set(str(user_id))

        if client := await clients_cache.get_user(user_id):
            return client

        client = await clients_service.get_client(user_id)
        if client is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found",
            )

        return client

    if user_type == "employee":
        employee_id_ctx_var.set(str(user_id))

        if employee := await employees_cache.get_employee(user_id):
            if not employee.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Employee account is inactive",
                )
            return employee

        employee = await employees_service.get_employee(user_id)
        if employee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found",
            )

        if not employee.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Employee account is inactive",
            )

        return employee

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Unknown user type",
    )

async def get_current_employee(
    user: Annotated[Employee | Client, Depends(get_current_user)],
) -> Employee:
    if not isinstance(user, Employee):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employees only",
        )
    return user

async def get_current_client(
    user: Annotated[Employee | Client, Depends(get_current_user)],
) -> Client:
    if not isinstance(user, Client):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clients only",
        )
    return user


# ======================================================================
# 5. USER ROLES DEPENDENCIES
# ======================================================================


class RequireEmployee:
    async def __call__(
        self,
        user: Annotated[Employee | Client, Depends(get_current_user)],
    ) -> Employee:
        if not isinstance(user, Employee):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Employees only.",
            )

        return user
    

class RequireEmployeeRoles:
    def __init__(self, *roles: EmployeeRole):
        self.roles = set(roles)

    async def __call__(
        self,
        employee: Annotated[Employee, Depends(RequireEmployee())],
    ) -> Employee:
        if employee.role not in self.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

        return employee
    

class RequireOwner:
    def __init__(self, param_name: str = "client_id"):
        self.param_name = param_name

    async def __call__(
        self,
        request: Request,
        user: Annotated[Employee | Client, Depends(get_current_user)],
    ) -> Client:
        if not isinstance(user, Client):
            raise HTTPException(
                status_code=403,
                detail="Clients only.",
            )

        owner_id = request.path_params[self.param_name]

        if str(user.id) != owner_id:
            raise HTTPException(
                status_code=403,
                detail="Not your resource.",
            )

        return user
    

def allow_staff_or_owner(
    *roles: EmployeeRole,
    owner_param: str = "client_id",
):
    role_set = set(roles)

    async def dependency(
        request: Request,
        user: Annotated[Employee | Client, Depends(get_current_user)],
    ) -> Employee | Client:

        if isinstance(user, Employee):
            if user.role not in role_set:
                raise HTTPException(403, "Forbidden")
            return user

        owner_id = request.path_params[owner_param]

        if str(user.id) != owner_id:
            raise HTTPException(403, "Forbidden")

        return user

    return dependency

allow_all_staff = RequireEmployeeRoles(
    EmployeeRole.ADMIN,
    EmployeeRole.AGENT,
)

allow_admin = RequireEmployeeRoles(
    EmployeeRole.ADMIN
)

allow_retail_points_view = allow_staff_or_owner(
    EmployeeRole.ADMIN,
    EmployeeRole.AGENT,
    owner_param="owner_id",
)