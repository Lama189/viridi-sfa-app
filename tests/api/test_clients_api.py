from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import (
    get_clients_auth_service,
    get_clients_service,
    get_current_user,
    get_orders_service,
)
from app.api.v1.schemas.clients import ClientResponse, ClientWithTokensResponse
from app.domain.entities.auth import AuthenticatedClient, AuthenticatedEmployee
from app.domain.entities.clients import Client
from app.domain.entities.orders import (
    Order,
    OrderItem,
    ProductShort,
    RetailPointShort,
    UserShort,
    WarehouseShort,
)
from app.domain.enums import EmployeeRole, OrderStatus
from app.main import app


@pytest.fixture
def mock_service():
    return AsyncMock()


@pytest.fixture
def mock_auth_service():
    return AsyncMock()


@pytest.fixture
def mock_orders_service():
    return AsyncMock()


@pytest.fixture
def mock_admin_employee():
    return AuthenticatedEmployee(
        id=uuid4(),
        phone="+998900000000",
        role=EmployeeRole.ADMIN,
        full_name="Mock Admin",
        is_active=True,
    )


@pytest.fixture(autouse=True)
def override_deps(mock_service, mock_auth_service, mock_orders_service, mock_admin_employee):
    app.dependency_overrides[get_clients_service] = lambda: mock_service
    app.dependency_overrides[get_clients_auth_service] = lambda: mock_auth_service
    app.dependency_overrides[get_orders_service] = lambda: mock_orders_service
    app.dependency_overrides[get_current_user] = lambda: mock_admin_employee
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _sample_order(client_id, order_id=None):
    oid = order_id or uuid4()
    return Order(
        warehouse_id=uuid4(),
        created_by_id=client_id,
        retail_point_id=uuid4(),
        id=oid,
        status=OrderStatus.PENDING,
        total_amount=Decimal("150000.00"),
        total_volume=Decimal("0.050"),
        retail_point=RetailPointShort(id=uuid4(), name="RP 1", address="Tashkent"),
        warehouse=WarehouseShort(id=uuid4(), name="WH 1"),
        created_by=UserShort(id=client_id, full_name="Client 1"),
        items=[
            OrderItem(
                order_id=oid,
                product_id=uuid4(),
                quantity=2,
                price_at_order=Decimal("75000.00"),
                total_volume=Decimal("0.050"),
                id=uuid4(),
                product=ProductShort(id=uuid4(), name="Test Prod"),
            )
        ],
    )


@pytest.mark.asyncio
async def test_register_success(client, mock_auth_service):
    uid = uuid4()
    mock_auth_service.register.return_value = ClientWithTokensResponse(
        access_token="acc",
        refresh_token="ref",
        client=ClientResponse(
            id=uid,
            phone="+998901234567",
            full_name="Test",
            telegram_chat_id=None,
            is_active=True,
        ),
    )

    resp = await client.post(
        "/api/v1/clients/register",
        json={
            "invite_code": "ABC123",
            "phone": "+998901234567",
            "full_name": "Test",
            "telegram_chat_id": 123,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["access_token"] == "acc"
    assert data["refresh_token"] == "ref"
    assert data["client"]["phone"] == "+998901234567"


@pytest.mark.asyncio
async def test_register_existing_phone_returns_201(client, mock_auth_service):
    mock_auth_service.register.return_value = ClientWithTokensResponse(
        access_token="acc",
        refresh_token="ref",
        client=ClientResponse(
            id=uuid4(),
            phone="+998901234567",
            full_name="Existing Client",
            telegram_chat_id=111,
            is_active=True,
        ),
    )

    resp = await client.post(
        "/api/v1/clients/register",
        json={
            "invite_code": "ABC123",
            "phone": "+998901234567",
            "full_name": "Existing Client",
            "telegram_chat_id": 111,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["access_token"] == "acc"


@pytest.mark.asyncio
async def test_list_client_orders_as_staff_success(
    client, mock_service, mock_orders_service
):
    cid = uuid4()
    mock_service.get_client.return_value = Client(
        id=cid,
        phone="+998901234567",
        full_name="Test Client",
        is_active=True,
    )
    mock_orders_service.list_by_client.return_value = [_sample_order(cid)]

    resp = await client.get(f"/api/v1/clients/{cid}/orders")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert Decimal(data[0]["total_amount"]) == Decimal("150000.00")
    assert data[0]["status"] == OrderStatus.PENDING.value
    mock_orders_service.list_by_client.assert_awaited_once_with(
        client_id=cid,
        statuses=None,
    )


@pytest.mark.asyncio
async def test_list_client_orders_with_statuses_filter(
    client, mock_service, mock_orders_service
):
    cid = uuid4()
    mock_service.get_client.return_value = Client(
        id=cid,
        phone="+998901234567",
        full_name="Test Client",
        is_active=True,
    )
    mock_orders_service.list_by_client.return_value = []

    resp = await client.get(
        f"/api/v1/clients/{cid}/orders?statuses=pending&statuses=confirmed"
    )
    assert resp.status_code == 200
    mock_orders_service.list_by_client.assert_awaited_once_with(
        client_id=cid,
        statuses=[OrderStatus.PENDING, OrderStatus.CONFIRMED],
    )


@pytest.mark.asyncio
async def test_list_client_orders_as_own_client(
    client, mock_service, mock_orders_service
):
    cid = uuid4()
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedClient(
        id=cid,
        phone="+998901234567",
        full_name="Client User",
        is_active=True,
    )

    mock_service.get_client.return_value = Client(
        id=cid,
        phone="+998901234567",
        full_name="Client User",
        is_active=True,
    )
    mock_orders_service.list_by_client.return_value = [_sample_order(cid)]

    resp = await client.get(f"/api/v1/clients/{cid}/orders")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_list_client_orders_forbidden_for_other_client(
    client, mock_service, mock_orders_service
):
    other_cid = uuid4()
    my_cid = uuid4()
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedClient(
        id=my_cid,
        phone="+998901234567",
        full_name="My User",
        is_active=True,
    )

    resp = await client.get(f"/api/v1/clients/{other_cid}/orders")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_client_orders_not_found(client, mock_service):
    cid = uuid4()
    mock_service.get_client.return_value = None

    resp = await client.get(f"/api/v1/clients/{cid}/orders")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_client_retail_point_orders(
    client, mock_service, mock_orders_service
):
    cid = uuid4()
    mock_service.get_client.return_value = Client(
        id=cid,
        phone="+998901234567",
        full_name="Test Client",
        is_active=True,
    )
    mock_orders_service.list_by_client_retail_point.return_value = [_sample_order(cid)]

    resp = await client.get(f"/api/v1/clients/{cid}/retail-point/orders")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert Decimal(data[0]["total_amount"]) == Decimal("150000.00")
    mock_orders_service.list_by_client_retail_point.assert_awaited_once_with(
        client_id=cid,
        statuses=None,
    )


@pytest.mark.asyncio
async def test_list_client_retail_point_orders_forbidden(
    client, mock_service, mock_orders_service
):
    other_cid = uuid4()
    my_cid = uuid4()
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedClient(
        id=my_cid,
        phone="+998901234567",
        full_name="My User",
        is_active=True,
    )

    resp = await client.get(f"/api/v1/clients/{other_cid}/retail-point/orders")
    assert resp.status_code == 403
