from aio_pika import connect_robust
from aio_pika.abc import AbstractChannel, AbstractConnection

from app.core.observability.logging import logger


class RabbitMQConnection:
    def __init__(self, url: str) -> None:
        self._url = url
        self._connection: AbstractConnection | None = None
        self._channel: AbstractChannel | None = None

    async def connect(self) -> None:
        if self._connection and not self._connection.is_closed:
            return

        logger.info("Connecting to RabbitMQ")

        self._connection = await connect_robust(self._url)
        self._channel = await self._connection.channel(publisher_confirms=True)

        logger.info("RabbitMQ connected")

    async def channel(self) -> AbstractChannel:
        if not self._channel:
            await self.connect()

        assert self._channel is not None
        return self._channel

    async def get_channel(self) -> AbstractChannel:
        return await self.channel()

    async def close(self) -> None:
        if self._channel:
            await self._channel.close()

        if self._connection:
            await self._connection.close()

        logger.info("RabbitMQ connections closed")


RabbitMQConnectionManager = RabbitMQConnection
