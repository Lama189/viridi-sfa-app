from app.core.config import get_settings
from app.infrastructure.postgres.session import create_session_factory
from app.infrastructure.postgres.uow import PostgresUnitOfWork
from app.infrastructure.rabbitmq.connection import RabbitMQConnectionManager
from app.infrastructure.rabbitmq.publisher import RabbitMQPublisher


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

    def uow(self) -> PostgresUnitOfWork:
        return PostgresUnitOfWork(session_factory=self._session_factory)

    async def rabbitmq_publisher(self) -> RabbitMQPublisher:
        channel = await self._rabbitmq.get_channel()

        return RabbitMQPublisher(channel)

    async def close(self) -> None:
        await self._rabbitmq.close()


container = Container()
