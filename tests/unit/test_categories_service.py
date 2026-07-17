from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.api.v1.schemas.inventory import CategoryCreate, CategoryUpdate
from app.application.services.categories import CategoriesService
from app.domain.entities.inventory import Category


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.categories = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def service(mock_uow):
    return CategoriesService(mock_uow)


# --- create_category ---

@pytest.mark.asyncio
async def test_create_category_success(service, mock_uow):
    mock_uow.categories.exists_by.return_value = False
    mock_uow.categories.add.return_value = None

    dto = CategoryCreate(name="Fertilizers")
    result = await service.create_category(dto)

    assert result.name == "Fertilizers"
    assert result.is_active is True
    mock_uow.categories.add.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_category_duplicate_name(service, mock_uow):
    mock_uow.categories.exists_by.return_value = True

    dto = CategoryCreate(name="Seeds")
    with pytest.raises(ValueError, match="already exists"):
        await service.create_category(dto)

    mock_uow.categories.add.assert_not_awaited()


# --- get_by_id ---

@pytest.mark.asyncio
async def test_get_by_id_found(service, mock_uow):
    uid = uuid4()
    mock_uow.categories.get_by_id.return_value = Category(name="X", id=uid)

    result = await service.get_by_id(uid)
    assert result is not None
    assert result.name == "X"


@pytest.mark.asyncio
async def test_get_by_id_not_found(service, mock_uow):
    mock_uow.categories.get_by_id.return_value = None

    result = await service.get_by_id(uuid4())
    assert result is None


# --- get_all_categories ---

@pytest.mark.asyncio
async def test_get_all_categories(service, mock_uow):
    mock_uow.categories.list_all.return_value = [
        Category(name="A"),
        Category(name="B"),
    ]

    result = await service.get_all_categories(only_active=True)
    assert len(result) == 2
    mock_uow.categories.list_all.assert_awaited_once_with(True)


# --- update_category ---

@pytest.mark.asyncio
async def test_update_category_success(service, mock_uow):
    uid = uuid4()
    cat = Category(name="Old", id=uid)
    mock_uow.categories.get_by_id.return_value = cat
    mock_uow.categories.update.return_value = None

    dto = CategoryUpdate(name="New")
    result = await service.update_category(uid, dto)

    assert result.name == "New"
    mock_uow.categories.update.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_category_toggle_active(service, mock_uow):
    uid = uuid4()
    cat = Category(name="X", id=uid, is_active=True)
    mock_uow.categories.get_by_id.return_value = cat

    dto = CategoryUpdate(is_active=False)
    result = await service.update_category(uid, dto)

    assert result.is_active is False


@pytest.mark.asyncio
async def test_update_category_not_found(service, mock_uow):
    mock_uow.categories.get_by_id.return_value = None

    dto = CategoryUpdate(name="X")
    with pytest.raises(ValueError, match="not found"):
        await service.update_category(uuid4(), dto)


# --- delete_category ---

@pytest.mark.asyncio
async def test_delete_category_success(service, mock_uow):
    uid = uuid4()
    mock_uow.categories.get_by_id.return_value = Category(name="Del", id=uid)

    await service.delete_category(uid)

    mock_uow.categories.delete.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_category_not_found(service, mock_uow):
    mock_uow.categories.get_by_id.return_value = None

    with pytest.raises(ValueError, match="not found"):
        await service.delete_category(uuid4())

    mock_uow.categories.delete.assert_not_awaited()
