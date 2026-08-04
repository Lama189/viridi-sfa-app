from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.container import Container, container
from app.infrastructure.postgres.uow import PostgresUnitOfWork


def test_container_singleton_instance():
    assert container is not None
    assert isinstance(container, Container)


@patch("app.container.create_session_factory")
@patch("app.container.RabbitMQConnectionManager")
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
@patch("app.container.create_session_factory")
@patch("app.container.RabbitMQConnectionManager")
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
