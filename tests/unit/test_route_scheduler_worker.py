from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from apscheduler.triggers.cron import CronTrigger

from app.workers.route_scheluder.worker import RouteScheluderWorker


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.day_of_week = "mon"
    config.hour = 2
    config.minute = 0
    return config


@pytest.fixture
def mock_route_service():
    return AsyncMock()


@pytest.mark.asyncio
async def test_worker_run_route_generation_success(mock_config, mock_route_service):
    worker = RouteScheluderWorker(config=mock_config, route_service=mock_route_service)

    await worker._run_route_generation()

    mock_route_service.generate.assert_awaited_once()


@pytest.mark.asyncio
async def test_worker_run_route_generation_handles_exception(
    mock_config, mock_route_service
):
    mock_route_service.generate.side_effect = Exception("Generation failed")
    worker = RouteScheluderWorker(config=mock_config, route_service=mock_route_service)

    # Should handle exception internally and log without raising
    await worker._run_route_generation()

    mock_route_service.generate.assert_awaited_once()


def test_worker_start(mock_config, mock_route_service):
    worker = RouteScheluderWorker(config=mock_config, route_service=mock_route_service)

    with (
        patch.object(worker._scheluder, "add_job") as mock_add_job,
        patch.object(worker._scheluder, "start") as mock_start,
    ):
        worker.start()

        mock_add_job.assert_called_once()
        args, kwargs = mock_add_job.call_args
        assert args[0] == worker._run_route_generation
        assert kwargs["id"] == "route_generation_job"
        assert kwargs["replace_existing"] is True
        assert kwargs["misfire_grace_time"] == 3600
        assert isinstance(kwargs["trigger"], CronTrigger)

        mock_start.assert_called_once()


def test_worker_stop(mock_config, mock_route_service):
    worker = RouteScheluderWorker(config=mock_config, route_service=mock_route_service)

    with (
        patch.object(
            type(worker._scheluder),
            "running",
            new_callable=PropertyMock,
            return_value=True,
        ),
        patch.object(worker._scheluder, "shutdown") as mock_shutdown,
    ):
        worker.stop()
        mock_shutdown.assert_called_once_with(wait=False)


def test_worker_stop_when_not_running(mock_config, mock_route_service):
    worker = RouteScheluderWorker(config=mock_config, route_service=mock_route_service)

    with (
        patch.object(
            type(worker._scheluder),
            "running",
            new_callable=PropertyMock,
            return_value=False,
        ),
        patch.object(worker._scheluder, "shutdown") as mock_shutdown,
    ):
        worker.stop()
        mock_shutdown.assert_not_called()
