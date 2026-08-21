from collections.abc import AsyncGenerator
from typing import Annotated

import structlog
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from minio import Minio
from redis.asyncio import Redis

from app.application.interfaces.cache.clients_cache import IClientsCacheRepository
from app.application.interfaces.cache.employees_cache import IEmployeesCacheRepository
from app.application.interfaces.object_storage import IObjectStorage
from app.application.interfaces.services.retail_point_assignments import (
    IRetailPointAssignmentService,
)
from app.application.interfaces.services.routes_generator import IRouteGenerationService
from app.application.interfaces.services.stocks import IStockService
from app.application.interfaces.services.territories import ITerritoryClusteringService
from app.application.interfaces.services.visit_debts import IVisitDebtService
from app.application.interfaces.services.visit_media import IVisitMediaService
from app.application.interfaces.services.visit_schedule_rules import (
    IVisitScheduleService,
)
from app.application.interfaces.uow import IUnitOfWork
from app.application.services.categories import CategoriesService
from app.application.services.clients import ClientsAuthService, ClientsService
from app.application.services.dashboard import DashboardService
from app.application.services.delivery_assignments import (
    DeliveryAssignmentService,
)
from app.application.services.employee_devices import EmployeeDeviceService
from app.application.services.employees import EmployeesAuthService, EmployeesService
from app.application.services.invite_codes import ClientInviteCodesService
from app.application.services.media import MediaService
from app.application.services.members import RetailPointMembersService
from app.application.services.notifications import NotificationsService
from app.application.services.orders import OrdersService
from app.application.services.products import ProductsService
from app.application.services.retail_point_assignments import (
    RetailPointAssignmentService,
)
from app.application.services.retail_points import RetailPointsService
from app.application.services.routes_generator import RouteGenerationService
from app.application.services.stocks import StockService
from app.application.services.territories import TerritoryClusteringService
from app.application.services.visit_debts import VisitDebtService
from app.application.services.visit_media import VisitMediaService
from app.application.services.visit_plans import VisitPlanService
from app.application.services.visit_schedule_rules import VisitScheduleService
from app.application.services.visits import VisitService
from app.application.services.warehouses import WarehousesService
from app.core.config import get_settings
from app.core.security import SecurityUtils
from app.domain.entities.auth import AuthenticatedClient, AuthenticatedEmployee
from app.domain.enums import EmployeeRole
from app.infrastructure.firebase.push_service import (
    FirebasePushNotificationService,
)
from app.infrastructure.minio.client import get_minio_client
from app.infrastructure.minio.storage import MinioStorage
from app.infrastructure.postgres.uow import PostgresUnitOfWork
from app.infrastructure.redis.client import get_redis_client
from app.infrastructure.redis.repos.clients import ClientsRedisRepository
from app.infrastructure.redis.repos.employees import EmployeesRedisRepository

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/users/login")


# ======================================================================
# 1. DATABASE & UOW DEPENDENCIES
# ======================================================================


async def get_uow() -> AsyncGenerator[IUnitOfWork]:
    async with PostgresUnitOfWork() as uow:
        yield uow


# ======================================================================
# 3. INFRASTRUCTURE DEPENDENCIES
# ======================================================================


async def get_clients_redis_repo(
    client: Annotated[Redis, Depends(get_redis_client)],
) -> IClientsCacheRepository:
    return ClientsRedisRepository(client)


async def get_employees_redis_repo(
    client: Annotated[Redis, Depends(get_redis_client)],
) -> IEmployeesCacheRepository:
    return EmployeesRedisRepository(client)


def get_minio_storage(
    client: Annotated[Minio, Depends(get_minio_client)],
) -> IObjectStorage:
    return MinioStorage(client)


# ======================================================================
# 2. CORE BUSINESS SERVICES DEPENDENCIES
# ======================================================================


async def get_categories_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> CategoriesService:
    return CategoriesService(uow)


async def get_warehouses_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> WarehousesService:
    return WarehousesService(uow)


async def get_invite_codes_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> ClientInviteCodesService:
    return ClientInviteCodesService(uow)


async def get_retail_point_members_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
    invite_codes: Annotated[
        ClientInviteCodesService, Depends(get_invite_codes_service)
    ],
) -> RetailPointMembersService:
    return RetailPointMembersService(uow, invite_codes)


async def get_retail_point_assignment_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> IRetailPointAssignmentService:
    return RetailPointAssignmentService(uow)


async def get_visit_schedule_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> IVisitScheduleService:
    return VisitScheduleService(uow)


async def get_retail_points_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
    invite_codes: Annotated[
        ClientInviteCodesService, Depends(get_invite_codes_service)
    ],
    assignments: Annotated[
        IRetailPointAssignmentService, Depends(get_retail_point_assignment_service)
    ],
    visits_rules: Annotated[IVisitScheduleService, Depends(get_visit_schedule_service)],
) -> RetailPointsService:
    return RetailPointsService(uow, invite_codes, assignments, visits_rules)


async def get_products_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> ProductsService:
    return ProductsService(uow)


async def get_stocks_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> IStockService:
    return StockService(uow)


async def get_push_notification_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> FirebasePushNotificationService:
    return FirebasePushNotificationService(uow)


async def get_delivery_assignment_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
    push_service: Annotated[
        FirebasePushNotificationService, Depends(get_push_notification_service)
    ],
) -> DeliveryAssignmentService:
    return DeliveryAssignmentService(
        uow=uow,
        push_service=push_service,
        min_delivery_days_offset=settings.min_delivery_days_offset,
    )


async def get_orders_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
    stocks: Annotated[IStockService, Depends(get_stocks_service)],
    delivery_assignment_service: Annotated[
        DeliveryAssignmentService, Depends(get_delivery_assignment_service)
    ],
) -> OrdersService:
    return OrdersService(
        uow=uow,
        stocks=stocks,
        delivery_assignment_service=delivery_assignment_service,
    )


async def get_clients_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> ClientsService:
    return ClientsService(uow)


async def get_clients_auth_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
    redis: Annotated[IClientsCacheRepository, Depends(get_clients_redis_repo)],
    invite_codes: Annotated[
        ClientInviteCodesService, Depends(get_invite_codes_service)
    ],
    memberships: Annotated[
        RetailPointMembersService, Depends(get_retail_point_members_service)
    ],
) -> ClientsAuthService:
    return ClientsAuthService(uow, redis, invite_codes, memberships)


async def get_employees_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> EmployeesService:
    return EmployeesService(uow)


async def get_employees_auth_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
    redis: Annotated[IEmployeesCacheRepository, Depends(get_employees_redis_repo)],
) -> EmployeesAuthService:
    return EmployeesAuthService(uow, redis)


async def get_media_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
    storage: Annotated[IObjectStorage, Depends(get_minio_storage)],
) -> MediaService:
    return MediaService(uow, storage)


async def get_visit_media_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> IVisitMediaService:
    return VisitMediaService(uow)


async def get_visit_debts_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> IVisitDebtService:
    return VisitDebtService(uow)


async def get_visits_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
    visit_media: Annotated[IVisitMediaService, Depends(get_visit_media_service)],
    visit_debts: Annotated[IVisitDebtService, Depends(get_visit_debts_service)],
) -> VisitService:
    return VisitService(uow, visit_media, visit_debts)


async def get_visit_plans_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> VisitPlanService:
    return VisitPlanService(uow)


async def get_dashboard_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> DashboardService:
    return DashboardService(uow)


async def get_notifications_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> NotificationsService:
    return NotificationsService(uow)


async def get_employee_device_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> EmployeeDeviceService:
    return EmployeeDeviceService(uow)


def get_territory_clustering_service() -> ITerritoryClusteringService:
    return TerritoryClusteringService()


async def get_routes_generator_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
    clustering_service: Annotated[
        ITerritoryClusteringService, Depends(get_territory_clustering_service)
    ],
    assignments_service: Annotated[
        IRetailPointAssignmentService, Depends(get_retail_point_assignment_service)
    ],
    visit_plans_service: Annotated[VisitPlanService, Depends(get_visit_plans_service)],
) -> IRouteGenerationService:
    return RouteGenerationService(
        uow=uow,
        clustering_service=clustering_service,
        assignments_service=assignments_service,
        visit_plans_service=visit_plans_service,
        min_delivery_days_offset=settings.min_delivery_days_offset,
    )


# ======================================================================
# 4. AUTHENTICATION & CURRENT USER DEPENDENCIES
# ======================================================================


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    clients_service: Annotated[ClientsService, Depends(get_clients_service)],
    employees_service: Annotated[EmployeesService, Depends(get_employees_service)],
    clients_cache: Annotated[IClientsCacheRepository, Depends(get_clients_redis_repo)],
    employees_cache: Annotated[
        IEmployeesCacheRepository, Depends(get_employees_redis_repo)
    ],
) -> AuthenticatedEmployee | AuthenticatedClient:
    payload = SecurityUtils.verify_token(token)

    user_type = payload["user_type"]
    user_id = payload["sub"]

    if user_type == "client":
        structlog.contextvars.bind_contextvars(user_id=str(user_id), user_type="client")

        if cached_client := await clients_cache.get_user(user_id):
            return cached_client

        client = await clients_service.get_client(user_id)
        if client is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found",
            )

        return AuthenticatedClient.from_entity(client)

    if user_type == "employee":
        structlog.contextvars.bind_contextvars(
            employee_id=str(user_id), user_type="employee"
        )

        if cached_employee := await employees_cache.get_employee(user_id):
            if not cached_employee.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Employee account is inactive",
                )
            return cached_employee

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

        return AuthenticatedEmployee.from_entity(employee)

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Unknown user type",
    )


async def get_current_employee(
    user: Annotated[
        AuthenticatedEmployee | AuthenticatedClient, Depends(get_current_user)
    ],
) -> AuthenticatedEmployee:
    if not isinstance(user, AuthenticatedEmployee):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employees only",
        )
    return user


async def get_current_client(
    user: Annotated[
        AuthenticatedEmployee | AuthenticatedClient, Depends(get_current_user)
    ],
) -> AuthenticatedClient:
    if not isinstance(user, AuthenticatedClient):
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
        user: Annotated[
            AuthenticatedEmployee | AuthenticatedClient, Depends(get_current_user)
        ],
    ) -> AuthenticatedEmployee:
        if not isinstance(user, AuthenticatedEmployee):
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
        employee: Annotated[AuthenticatedEmployee, Depends(RequireEmployee())],
    ) -> AuthenticatedEmployee:
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
        user: Annotated[
            AuthenticatedEmployee | AuthenticatedClient, Depends(get_current_user)
        ],
    ) -> AuthenticatedClient:
        if not isinstance(user, AuthenticatedClient):
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
        user: Annotated[
            AuthenticatedEmployee | AuthenticatedClient, Depends(get_current_user)
        ],
    ) -> AuthenticatedEmployee | AuthenticatedClient:

        if isinstance(user, AuthenticatedEmployee):
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
    EmployeeRole.WAREHOUSE_WORKER,
)

allow_warehouse_worker = RequireEmployeeRoles(
    EmployeeRole.ADMIN,
    EmployeeRole.WAREHOUSE_WORKER,
)

allow_admin = RequireEmployeeRoles(EmployeeRole.ADMIN)
