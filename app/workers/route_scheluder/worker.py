from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.application.interfaces.services.routes_generator import IRouteGenerationService
from app.core.config import RouteScheluderWorkerConfig
from app.core.observability.logging import logger


class RouteScheluderWorker:
    def __init__(
        self, config: RouteScheluderWorkerConfig, route_service: IRouteGenerationService
    ) -> None:
        self._config = config
        self._route_service = route_service
        self._scheluder = AsyncIOScheduler()

    async def _run_route_generation(self) -> None:
        logger.info("Starting scheduled route generation job...")
        try:
            await self._route_service.generate()
            logger.info("Scheduled route generation completed successfully")
        except Exception as exc:
            logger.exception("Scheduled route generation failed", error=str(exc))

    def start(self) -> None:
        trigger = CronTrigger(
            day_of_week=self._config.day_of_week,
            hour=self._config.hour,
            minute=self._config.minute,
        )

        self._scheluder.add_job(
            self._run_route_generation,
            trigger=trigger,
            id="route_generation_job",
            replace_existing=True,
            misfire_grace_time=3600,
        )

        self._scheluder.start()
        logger.info("Route scheluder worker started")

    def stop(self) -> None:
        if self._scheluder.running:
            self._scheluder.shutdown(wait=False)
            logger.info("Route scheluder worker stopped")
