import json
from uuid import UUID

from aio_pika import ExchangeType
from aio_pika.abc import AbstractChannel, AbstractIncomingMessage, AbstractQueue

from app.application.interfaces.services.delivery_proposals import (
    IDeliveryProposalService,
)
from app.core.observability.logging import logger


class OrderEventsWorker:
    def __init__(
        self,
        channel: AbstractChannel,
        proposal_service: IDeliveryProposalService,
        queue_name: str = "delivery_proposals_order_events",
        exchange_name: str = "orders",
    ) -> None:
        self._channel = channel
        self._proposal_service = proposal_service
        self._queue_name: str = queue_name
        self._exchange_name: str = exchange_name
        self._queue: AbstractQueue | None = None
        self._consumer_tag: str | None = None

    async def start(self) -> None:
        exchange = await self._channel.declare_exchange(
            name=self._exchange_name,
            type=ExchangeType.TOPIC,
            durable=True,
        )

        queue = await self._channel.declare_queue(
            name=self._queue_name,
            durable=True,
        )

        await queue.bind(exchange=exchange, routing_key="order.assembled")
        self._consumer_tag = await queue.consume(self._handle_message)
        self._queue = queue
        logger.info(
            "OrderEventsWorker started, subscribed to order.assembled",
            queue=self._queue_name,
        )

    async def stop(self) -> None:
        if self._queue and self._consumer_tag:
            await self._queue.cancel(self._consumer_tag)
            logger.info("OrderEventsWorker stopped")

    async def _handle_message(self, message: AbstractIncomingMessage) -> None:
        async with message.process():
            await self._process_message_payload(message)

    async def _process_message_payload(self, message: AbstractIncomingMessage) -> None:
        try:
            data = json.loads(message.body.decode())
            order_id_str = data.get("order_id")
            if not order_id_str and message.headers:
                order_id_str = message.headers.get("aggregate_id")

            if not order_id_str:
                logger.warning("No order_id found in order.assembled message")
                return

            order_id = UUID(str(order_id_str))
            logger.info("Processing order.assembled event", order_id=str(order_id))

            await self._proposal_service.process_assembled_order(order_id)

        except Exception as exc:
            logger.exception("Failed to handle order.assembled message", error=str(exc))
            raise
