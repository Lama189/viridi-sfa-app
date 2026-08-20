from collections.abc import AsyncGenerator

from redis.asyncio import Redis

from app.application.interfaces.cache.rate_limiter import IRateLimiter
from app.application.interfaces.services.delivery_proposals import (
    IDeliveryProposalService,
)
from app.application.interfaces.services.employee_devices import (
    IEmployeeDeviceService,
)
from app.application.interfaces.services.notifications import INotificationsService
from app.application.interfaces.services.push_notifications import (
    IPushNotificationService,
)
from app.application.interfaces.services.retail_point_assignments import (
    IRetailPointAssignmentService,
)
from app.application.interfaces.services.routes_generator import IRouteGenerationService
from app.application.interfaces.services.territories import ITerritoryClusteringService
from app.application.interfaces.services.visit_plans import IVisitPlanService
from app.application.interfaces.uow import IUnitOfWork
from app.application.services.delivery_proposals import DeliveryProposalService
from app.application.services.employee_devices import EmployeeDeviceService
from app.application.services.notifications import NotificationsService
from app.application.services.retail_point_assignments import (
    RetailPointAssignmentService,
)
from app.application.services.routes_generator import RouteGenerationService
from app.application.services.territories import TerritoryClusteringService
from app.application.services.visit_plans import VisitPlanService
from app.core.config import get_settings
from app.infrastructure.firebase.push_service import (
    FirebasePushNotificationService,
)
from app.infrastructure.postgres.session import create_session_factory
from app.infrastructure.postgres.uow import PostgresUnitOfWork
from app.infrastructure.rabbitmq.connection import RabbitMQConnectionManager
from app.infrastructure.rabbitmq.publisher import RabbitMQPublisher
from app.infrastructure.redis.client import get_redis_client
from app.infrastructure.redis.repos.rate_limiter import RedisRateLimiter


class Container:
    def __init__(self) -> None:
        settings = get_settings()
        self._session_factory = create_session_factory(
            database_url=settings.database_url,
            echo=settings.debug,
        )
        self._rabbitmq = RabbitMQConnectionManager(settings.rabbitmq_url)

    @property
    def session_factory(self):
        return self._session_factory

    @property
    def rabbitmq(self):
        return self._rabbitmq

    def uow(self) -> IUnitOfWork:
        return PostgresUnitOfWork(session_factory=self._session_factory)

    async def rabbitmq_publisher(self) -> RabbitMQPublisher:
        channel = await self._rabbitmq.get_channel()

        return RabbitMQPublisher(channel)

    def territory_clustering_service(self) -> ITerritoryClusteringService:
        return TerritoryClusteringService()

    def retail_point_assignment_service(
        self, uow: IUnitOfWork
    ) -> IRetailPointAssignmentService:
        return RetailPointAssignmentService(uow)

    def visit_plan_service(self, uow: IUnitOfWork) -> IVisitPlanService:
        return VisitPlanService(uow)

    def route_generator_service(self, uow: IUnitOfWork) -> IRouteGenerationService:
        return RouteGenerationService(
            uow=uow,
            clustering_service=self.territory_clustering_service(),
            assignments_service=self.retail_point_assignment_service(uow),
            visit_plans_service=self.visit_plan_service(uow),
        )

    def notifications_service(self, uow: IUnitOfWork) -> INotificationsService:
        return NotificationsService(uow)

    def push_notification_service(self, uow: IUnitOfWork) -> IPushNotificationService:
        return FirebasePushNotificationService(uow)

    def delivery_proposal_service(self, uow: IUnitOfWork) -> IDeliveryProposalService:
        return DeliveryProposalService(
            uow=uow,
            notifications_service=self.notifications_service(uow),
            push_service=self.push_notification_service(uow),
        )

    def employee_device_service(self, uow: IUnitOfWork) -> IEmployeeDeviceService:
        return EmployeeDeviceService(uow)

    def redis_client(self) -> AsyncGenerator[Redis]:
        return get_redis_client()

    def rate_limiter(self, redis_client: Redis) -> IRateLimiter:
        return RedisRateLimiter(client=redis_client)

    async def close(self) -> None:
        await self._rabbitmq.close()


container = Container()
