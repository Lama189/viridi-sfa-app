import os
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-api-tests-32bytes!")

from unittest.mock import AsyncMock

import pytest



@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.categories = AsyncMock()
    uow.products = AsyncMock()
    uow.warehouses = AsyncMock()
    uow.clients = AsyncMock()
    uow.employees = AsyncMock()
    uow.retail_points = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def mock_cache():
    return AsyncMock()
