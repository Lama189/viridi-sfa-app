import asyncio
import signal

from app.core.config import get_scheluder_worker_config
from app.core.container import container
from app.core.observability.logging import logger
from app.workers.route_scheluder.worker import RouteScheluderWorker


async def run() -> None:
    config = get_scheluder_worker_config()

    worker = RouteScheluderWorker(
        config=config,
        uow_factory=container.uow,
        service_factory=container.route_generator_service,
    )
    worker.start()

    stop_event = asyncio.Event()

    def _on_shutdown() -> None:
        logger.info("Stopping route scheduler worker...")
        worker.stop()
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
