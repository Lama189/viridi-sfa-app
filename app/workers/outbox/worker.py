import asyncio

from app.application.interfaces.publisher import IPublisher
from app.application.interfaces.uow import IUnitOfWork
from app.core.observability.logging import logger
from app.domain.entities.outbox_messages import OutboxMessage


class OutboxWorker:
    def __init__(self, uow: IUnitOfWork, publisher: IPublisher) -> None:
        self._uow = uow
        self._publisher = publisher

        self._running = True

    async def run(self) -> None:
        logger.info("Outbox worker started")

        while self._running:
            try:
                async with self._uow as uow:
                    messages = await uow.outbox.list_unprocessed(limit=100)
                    if not messages:
                        await asyncio.sleep(1)
                        continue

                    for message in messages:
                        await self._process(message, uow)

            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.exception("Outbox worker failed", error=str(exc))
                await asyncio.sleep(5)

    async def _process(self, message: OutboxMessage, uow: IUnitOfWork) -> None:
        await self._publisher.publish(message)

        message.mark_processed()

        await uow.outbox.mark_processed(message.id)
        await uow.commit()

        logger.info(
            "Outbox message processed",
            message_id=str(message.id),
            event_type=message.event_type,
            aggregate_type=message.aggregate_type,
        )
