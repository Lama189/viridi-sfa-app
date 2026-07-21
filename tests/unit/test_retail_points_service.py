from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.api.v1.schemas.retail_points import CreateRetailPointRequest, UpdateRetailPointRequest
from app.application.services.retail_points import RetailPointsService
from app.domain.entities.retail_points import RetailPoint
from app.domain.enums import ClientType


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.retail_points = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def service(mock_uow):
    return RetailPointsService(mock_uow)


@pytest.mark.asyncio
async def test_create_retail_point_success(service, mock_uow):
    agent_id = uuid4()
    dto = CreateRetailPointRequest(name="Store-1", address="ul. Test 1")

    result = await service.create_retail_point(dto, agent_id)

    assert result.name == "Store-1"
    assert result.address == "ul. Test 1"
    assert result.created_by_employee_id == agent_id
    assert result.is_active is True
    mock_uow.retail_points.add.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_retail_point_with_optional_fields(service, mock_uow):
    agent_id = uuid4()
    dto = CreateRetailPointRequest(
        name="Store-2",
        address="ul. Test 2",
        legal_name="OOO Test",
        client_type=ClientType.B,
        landmark="near park",
        contact_person="John",
        phone_number="+998901234567",
        inn="123456789",
        latitude=Decimal("41.311081"),
        longitude=Decimal("69.240562"),
        visit_mon=True,
        visit_wed=True,
        visit_fri=True,
    )

    result = await service.create_retail_point(dto, agent_id)

    assert result.legal_name == "OOO Test"
    assert result.client_type == ClientType.B
    assert result.landmark == "near park"
    assert result.inn == "123456789"
    assert result.latitude == Decimal("41.311081")
    assert result.visit_mon is True
    assert result.visit_wed is True
    assert result.visit_fri is True
    assert result.visit_tue is False


@pytest.mark.asyncio
async def test_get_by_id_found(service, mock_uow):
    uid = uuid4()
    mock_uow.retail_points.get_by_id.return_value = RetailPoint(
        name="X", address="Addr", id=uid,
    )

    result = await service.get_by_id(uid)
    assert result is not None
    assert result.name == "X"


@pytest.mark.asyncio
async def test_get_by_id_not_found(service, mock_uow):
    mock_uow.retail_points.get_by_id.return_value = None

    result = await service.get_by_id(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_update_retail_point_success(service, mock_uow):
    uid = uuid4()
    point = RetailPoint(name="Old", address="Old Addr", id=uid)
    mock_uow.retail_points.get_by_id.return_value = point

    dto = UpdateRetailPointRequest(name="New", address="New Addr")
    result = await service.update_retail_point(uid, dto)

    assert result.name == "New"
    assert result.address == "New Addr"
    mock_uow.retail_points.update.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_retail_point_partial(service, mock_uow):
    uid = uuid4()
    point = RetailPoint(name="Keep", address="Keep Addr", id=uid)
    mock_uow.retail_points.get_by_id.return_value = point

    dto = UpdateRetailPointRequest(name="Changed")
    result = await service.update_retail_point(uid, dto)

    assert result.name == "Changed"
    assert result.address == "Keep Addr"


@pytest.mark.asyncio
async def test_update_retail_point_visit_schedule(service, mock_uow):
    uid = uuid4()
    point = RetailPoint(name="X", address="A", id=uid, visit_mon=False)
    mock_uow.retail_points.get_by_id.return_value = point

    dto = UpdateRetailPointRequest(visit_mon=True, visit_sun=True)
    result = await service.update_retail_point(uid, dto)

    assert result.visit_mon is True
    assert result.visit_sun is True


@pytest.mark.asyncio
async def test_update_retail_point_toggle_active(service, mock_uow):
    uid = uuid4()
    point = RetailPoint(name="X", address="A", id=uid, is_active=True)
    mock_uow.retail_points.get_by_id.return_value = point

    dto = UpdateRetailPointRequest(is_active=False)
    result = await service.update_retail_point(uid, dto)

    assert result.is_active is False


@pytest.mark.asyncio
async def test_update_retail_point_not_found(service, mock_uow):
    mock_uow.retail_points.get_by_id.return_value = None

    dto = UpdateRetailPointRequest(name="X")
    with pytest.raises(ValueError, match="not found"):
        await service.update_retail_point(uuid4(), dto)


@pytest.mark.asyncio
async def test_delete_retail_point_success(service, mock_uow):
    uid = uuid4()
    mock_uow.retail_points.get_by_id.return_value = RetailPoint(
        name="Del", address="D", id=uid,
    )

    await service.delete_retail_point(uid)

    mock_uow.retail_points.delete.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_retail_point_not_found(service, mock_uow):
    mock_uow.retail_points.get_by_id.return_value = None

    with pytest.raises(ValueError, match="not found"):
        await service.delete_retail_point(uuid4())

    mock_uow.retail_points.delete.assert_not_awaited()
