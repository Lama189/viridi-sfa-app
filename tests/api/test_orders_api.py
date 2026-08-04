from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_current_user, get_orders_service
from app.domain.entities.auth import AuthenticatedClient, AuthenticatedEmployee
from app.domain.entities.orders import Order, OrderItem
from app.domain.enums import OrderStatus
from app.infrastructure.postgres.models.enums import EmployeeRole as PGEmployeeRole
from app.main import app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_service():
    return AsyncMock()


@pytest.fixture
def mock_client_entity():
    return AuthenticatedClient(
        phone="+998901111111",
        full_name="Test Client",
        id=uuid4(),
        is_active=True,
    )


@pytest.fixture
def mock_admin_employee():
    return AuthenticatedEmployee(
        id=uuid4(),
        phone="+998900000000",
        role=PGEmployeeRole.ADMIN,
        full_name="Mock Admin",
        is_active=True,
    )


def _order_response(order_id=None, client_id=None, status=OrderStatus.PENDING):
    oid = order_id or uuid4()
    cid = client_id or uuid4()
    now = datetime.now(UTC)
    return Order(
        id=oid,
        warehouse_id=uuid4(),
        created_by_id=cid,
        retail_point_id=uuid4(),
        status=status,
        total_amount=Decimal("150000.00"),
        total_volume=Decimal("0.500"),
        created_at=now,
        updated_at=now,
    )


def _order_with_item(order_id=None, client_id=None, status=OrderStatus.PENDING):
    oid = order_id or uuid4()
    cid = client_id or uuid4()
    now = datetime.now(UTC)
    order = Order(
        id=oid,
        warehouse_id=uuid4(),
        created_by_id=cid,
        retail_point_id=uuid4(),
        status=status,
        total_amount=Decimal("150000.00"),
        total_volume=Decimal("0.500"),
        created_at=now,
        updated_at=now,
    )
    item = OrderItem(
        order_id=oid,
        product_id=uuid4(),
        quantity=10,
        price_at_order=Decimal("15000.00"),
        total_volume=Decimal("0.050"),
    )
    order.items.append(item)
    return order


# ---------------------------------------------------------------------------
# Client endpoints: POST /api/v1/orders, GET /{id}, DELETE /{id}
# ---------------------------------------------------------------------------


class TestOrdersClientEndpoints:
    @pytest.fixture(autouse=True)
    def override_deps(self, mock_service, mock_client_entity):
        app.dependency_overrides[get_current_user] = lambda: mock_client_entity
        app.dependency_overrides[get_orders_service] = lambda: mock_service
        yield
        app.dependency_overrides.clear()

    @pytest_asyncio.fixture
    async def client(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    # --- POST /api/v1/orders ---

    @pytest.mark.asyncio
    async def test_create_order_success(self, client, mock_service, mock_client_entity):
        order = _order_response(client_id=mock_client_entity.id)
        mock_service.create.return_value = order

        resp = await client.post(
            "/api/v1/orders",
            json={
                "warehouse_id": str(uuid4()),
                "retail_point_id": str(uuid4()),
                "items": [{"product_id": str(uuid4()), "quantity": 10}],
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == OrderStatus.PENDING.value
        assert Decimal(data["total_amount"]) == Decimal("150000.00")

    @pytest.mark.asyncio
    async def test_create_order_client_not_found(self, client, mock_service):
        from app.core.exceptions import UserNotFoundError

        mock_service.create.side_effect = UserNotFoundError()

        resp = await client.post(
            "/api/v1/orders",
            json={
                "warehouse_id": str(uuid4()),
                "retail_point_id": str(uuid4()),
                "items": [{"product_id": str(uuid4()), "quantity": 1}],
            },
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_create_order_validation_error(self, client, mock_service):
        mock_service.create.side_effect = ValueError("Warehouse is inactive")

        resp = await client.post(
            "/api/v1/orders",
            json={
                "warehouse_id": str(uuid4()),
                "retail_point_id": str(uuid4()),
                "items": [{"product_id": str(uuid4()), "quantity": 1}],
            },
        )
        assert resp.status_code == 400

    # --- GET /api/v1/orders/{order_id} ---

    @pytest.mark.asyncio
    async def test_get_order_success(self, client, mock_service, mock_client_entity):
        order = _order_response(client_id=mock_client_entity.id)
        mock_service._uow = MagicMock()
        mock_service._uow.orders.get_by_id = AsyncMock(return_value=order)

        resp = await client.get(f"/api/v1/orders/{order.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == str(order.id)

    @pytest.mark.asyncio
    async def test_get_order_not_found(self, client, mock_service):
        mock_service._uow = MagicMock()
        mock_service._uow.orders.get_by_id = AsyncMock(return_value=None)

        resp = await client.get(f"/api/v1/orders/{uuid4()}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_order_forbidden(self, client, mock_service):
        order = _order_response(client_id=uuid4())
        mock_service._uow = MagicMock()
        mock_service._uow.orders.get_by_id = AsyncMock(return_value=order)

        resp = await client.get(f"/api/v1/orders/{order.id}")
        assert resp.status_code == 403

    # --- DELETE /api/v1/orders/{order_id} ---

    @pytest.mark.asyncio
    async def test_cancel_order_by_client_success(
        self, client, mock_service, mock_client_entity
    ):
        order = _order_response(client_id=mock_client_entity.id)
        mock_service._uow = MagicMock()
        mock_service._uow.orders.get_by_id = AsyncMock(return_value=order)
        mock_service.cancel = AsyncMock()

        resp = await client.delete(f"/api/v1/orders/{order.id}")
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_cancel_order_by_client_not_found(self, client, mock_service):
        mock_service._uow = MagicMock()
        mock_service._uow.orders.get_by_id = AsyncMock(return_value=None)

        resp = await client.delete(f"/api/v1/orders/{uuid4()}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_cancel_order_by_client_forbidden(self, client, mock_service):
        order = _order_response(client_id=uuid4())
        mock_service._uow = MagicMock()
        mock_service._uow.orders.get_by_id = AsyncMock(return_value=order)

        resp = await client.delete(f"/api/v1/orders/{order.id}")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_cancel_order_by_client_value_error(
        self, client, mock_service, mock_client_entity
    ):
        order = _order_response(client_id=mock_client_entity.id)
        mock_service._uow = MagicMock()
        mock_service._uow.orders.get_by_id = AsyncMock(return_value=order)
        mock_service.cancel.side_effect = ValueError("Cannot confirm order")

        resp = await client.delete(f"/api/v1/orders/{order.id}")
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Staff endpoints: POST /{id}/confirm, POST /{id}/cancel, POST /{id}/ship
# ---------------------------------------------------------------------------


class TestOrdersStaffEndpoints:
    @pytest.fixture(autouse=True)
    def override_deps(self, mock_service, mock_admin_employee):
        app.dependency_overrides[get_current_user] = lambda: mock_admin_employee
        app.dependency_overrides[get_orders_service] = lambda: mock_service
        yield
        app.dependency_overrides.clear()

    @pytest_asyncio.fixture
    async def client(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    # --- POST /api/v1/orders/{order_id}/confirm ---

    @pytest.mark.asyncio
    async def test_confirm_order_success(self, client, mock_service):
        order = _order_with_item(status=OrderStatus.CONFIRMED)
        mock_service.confirm.return_value = order

        resp = await client.post(f"/api/v1/orders/{order.id}/confirm")
        assert resp.status_code == 200
        assert resp.json()["status"] == OrderStatus.CONFIRMED.value

    @pytest.mark.asyncio
    async def test_confirm_order_not_found(self, client, mock_service):
        mock_service.confirm.side_effect = ValueError("not found")

        resp = await client.post(f"/api/v1/orders/{uuid4()}/confirm")
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_confirm_order_wrong_status(self, client, mock_service):
        mock_service.confirm.side_effect = ValueError("Cannot confirm order")

        resp = await client.post(f"/api/v1/orders/{uuid4()}/confirm")
        assert resp.status_code == 400

    # --- POST /api/v1/orders/{order_id}/cancel ---

    @pytest.mark.asyncio
    async def test_cancel_order_by_staff_success(self, client, mock_service):
        order = _order_with_item(status=OrderStatus.CANCELLED)
        mock_service.cancel.return_value = order

        resp = await client.post(f"/api/v1/orders/{order.id}/cancel")
        assert resp.status_code == 200
        assert resp.json()["status"] == OrderStatus.CANCELLED.value

    @pytest.mark.asyncio
    async def test_cancel_order_by_staff_not_found(self, client, mock_service):
        mock_service.cancel.side_effect = ValueError("not found")

        resp = await client.post(f"/api/v1/orders/{uuid4()}/cancel")
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_cancel_order_by_staff_wrong_status(self, client, mock_service):
        mock_service.cancel.side_effect = ValueError("Cannot confirm order")

        resp = await client.post(f"/api/v1/orders/{uuid4()}/cancel")
        assert resp.status_code == 400

    # --- POST /api/v1/orders/{order_id}/ship ---

    @pytest.mark.asyncio
    async def test_ship_order_success(self, client, mock_service):
        order = _order_with_item(status=OrderStatus.SHIPPED)
        mock_service.ship.return_value = order

        resp = await client.post(f"/api/v1/orders/{order.id}/ship")
        assert resp.status_code == 200
        assert resp.json()["status"] == OrderStatus.SHIPPED.value

    @pytest.mark.asyncio
    async def test_ship_order_not_found(self, client, mock_service):
        mock_service.ship.side_effect = ValueError("not found")

        resp = await client.post(f"/api/v1/orders/{uuid4()}/ship")
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_ship_order_wrong_status(self, client, mock_service):
        mock_service.ship.side_effect = ValueError("Cannot confirm order")

        resp = await client.post(f"/api/v1/orders/{uuid4()}/ship")
        assert resp.status_code == 400
