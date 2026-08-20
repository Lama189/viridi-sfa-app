from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.container import Container, container
from app.infrastructure.postgres.uow import PostgresUnitOfWork


def test_container_singleton_instance():
    assert container is not None
    assert isinstance(container, Container)


@patch("app.core.container.create_session_factory")
@patch("app.core.container.RabbitMQConnectionManager")
def test_container_properties_and_uow(mock_rabbitmq_cls, mock_session_factory):
    dummy_factory = MagicMock()
    mock_session_factory.return_value = dummy_factory

    cont = Container()

    assert cont.session_factory == dummy_factory
    assert cont.rabbitmq is not None

    uow_instance = cont.uow()
    assert isinstance(uow_instance, PostgresUnitOfWork)
    assert uow_instance._session_factory == dummy_factory


@pytest.mark.asyncio
@patch("app.core.container.create_session_factory")
@patch("app.core.container.RabbitMQConnectionManager")
async def test_container_rabbitmq_publisher_and_close(
    mock_rabbitmq_cls, mock_session_factory
):
    mock_connection = AsyncMock()
    mock_channel = AsyncMock()
    mock_connection.get_channel.return_value = mock_channel
    mock_rabbitmq_cls.return_value = mock_connection

    cont = Container()

    publisher = await cont.rabbitmq_publisher()
    assert publisher._channel == mock_channel

    await cont.close()
    mock_connection.close.assert_called_once()


@patch("app.core.container.create_session_factory")
@patch("app.core.container.RabbitMQConnectionManager")
def test_container_route_generator_service(mock_rabbitmq_cls, mock_session_factory):
    cont = Container()
    mock_uow = MagicMock()

    service = cont.route_generator_service(mock_uow)
    assert service is not None
    assert service._uow == mock_uow


@patch("app.core.container.create_session_factory")
@patch("app.core.container.RabbitMQConnectionManager")
@patch("app.core.container.get_redis_client")
def test_container_redis_and_rate_limiter(
    mock_get_redis_client, mock_rabbitmq_cls, mock_session_factory
):
    cont = Container()

    redis_gen = cont.redis_client()
    assert redis_gen is not None

    mock_redis = MagicMock()
    rate_limiter = cont.rate_limiter(mock_redis)
    assert rate_limiter is not None
    assert rate_limiter._client == mock_redis


@patch("app.core.container.create_session_factory")
@patch("app.core.container.RabbitMQConnectionManager")
def test_container_delivery_assignment_service(mock_rabbitmq_cls, mock_session_factory):
    cont = Container()
    mock_uow = MagicMock()

    service = cont.delivery_assignment_service(mock_uow)
    assert service is not None
    assert service._uow == mock_uow
    assert service._push_service is not None
