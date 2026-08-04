from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.api.v1.schemas.inventory import WarehouseCreate, WarehouseUpdate
from app.application.services.warehouses import WarehousesService
from app.domain.entities.inventory import Warehouse


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.warehouses = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def service(mock_uow):
    return WarehousesService(mock_uow)


# --- create_warehouse ---


@pytest.mark.asyncio
async def test_create_warehouse_success(service, mock_uow):
    mock_uow.warehouses.exists_by.return_value = False

    dto = WarehouseCreate(name="Warehouse-1", address="ul. Test 1")
    result = await service.create_warehouse(dto)

    assert result.name == "Warehouse-1"
    assert result.address == "ul. Test 1"
    assert result.is_active is True
    mock_uow.warehouses.add.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_warehouse_without_address(service, mock_uow):
    mock_uow.warehouses.exists_by.return_value = False

    dto = WarehouseCreate(name="Warehouse-NoAddr")
    result = await service.create_warehouse(dto)

    assert result.name == "Warehouse-NoAddr"
    assert result.address is None


@pytest.mark.asyncio
async def test_create_warehouse_duplicate_name(service, mock_uow):
    mock_uow.warehouses.exists_by.return_value = True

    dto = WarehouseCreate(name="Duplicate")
    with pytest.raises(ValueError, match="already exists"):
        await service.create_warehouse(dto)

    mock_uow.warehouses.add.assert_not_awaited()


# --- get_by_id ---


@pytest.mark.asyncio
async def test_get_by_id_found(service, mock_uow):
    uid = uuid4()
    mock_uow.warehouses.get_by_id.return_value = Warehouse(name="X", id=uid)

    result = await service.get_by_id(uid)
    assert result is not None
    assert result.name == "X"


@pytest.mark.asyncio
async def test_get_by_id_not_found(service, mock_uow):
    mock_uow.warehouses.get_by_id.return_value = None

    result = await service.get_by_id(uuid4())
    assert result is None


# --- get_all_warehouses ---


@pytest.mark.asyncio
async def test_get_all_warehouses(service, mock_uow):
    mock_uow.warehouses.list_all.return_value = [
        Warehouse(name="A"),
        Warehouse(name="B"),
    ]

    result = await service.get_all_warehouses(only_active=True)
    assert len(result) == 2
    mock_uow.warehouses.list_all.assert_awaited_once_with(True)


# --- update_warehouse ---


@pytest.mark.asyncio
async def test_update_warehouse_success(service, mock_uow):
    uid = uuid4()
    wh = Warehouse(name="Old", address="Old Addr", id=uid)
    mock_uow.warehouses.get_by_id.return_value = wh

    dto = WarehouseUpdate(name="New", address="New Addr")
    result = await service.update_warehouse(uid, dto)

    assert result.name == "New"
    assert result.address == "New Addr"
    mock_uow.warehouses.update.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_warehouse_partial(service, mock_uow):
    uid = uuid4()
    wh = Warehouse(name="Keep", address="Keep Addr", id=uid)
    mock_uow.warehouses.get_by_id.return_value = wh

    dto = WarehouseUpdate(name="Changed")
    result = await service.update_warehouse(uid, dto)

    assert result.name == "Changed"
    assert result.address == "Keep Addr"


@pytest.mark.asyncio
async def test_update_warehouse_toggle_active(service, mock_uow):
    uid = uuid4()
    wh = Warehouse(name="X", id=uid, is_active=True)
    mock_uow.warehouses.get_by_id.return_value = wh

    dto = WarehouseUpdate(is_active=False)
    result = await service.update_warehouse(uid, dto)

    assert result.is_active is False


@pytest.mark.asyncio
async def test_update_warehouse_not_found(service, mock_uow):
    mock_uow.warehouses.get_by_id.return_value = None

    dto = WarehouseUpdate(name="X")
    with pytest.raises(ValueError, match="not found"):
        await service.update_warehouse(uuid4(), dto)
