import asyncio
import signal

from app.core.container import container
from app.core.observability.logging import logger
from app.workers.order_events.worker import OrderEventsWorker


async def run() -> None:
    uow = container.uow()
    channel = await container.rabbitmq.get_channel()
    assignment_service = container.delivery_assignment_service(uow)

    worker = OrderEventsWorker(
        channel=channel,
        delivery_assignment_service=assignment_service,
    )
    await worker.start()

    stop_event = asyncio.Event()

    def _on_shutdown() -> None:
        logger.info("Stopping order events worker...")
        asyncio.create_task(worker.stop())
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _on_shutdown)

    try:
        await stop_event.wait()
    finally:
        await container.close()


if __name__ == "__main__":
    asyncio.run(run())
