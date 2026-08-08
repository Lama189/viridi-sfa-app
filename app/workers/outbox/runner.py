import asyncio

from app.core.container import container
from app.workers.outbox.worker import OutboxWorker


async def run() -> None:
    try:
        uow = container.uow()
        publisher = await container.rabbitmq_publisher()

        worker = OutboxWorker(uow=uow, publisher=publisher)

        await worker.run()

    finally:
        await container.close()


if __name__ == "__main__":
    asyncio.run(run())
