from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_current_user, get_orders_service
from app.domain.entities.auth import AuthenticatedClient, AuthenticatedEmployee
from app.domain.entities.orders import (
    Order,
    OrderItem,
    ProductShort,
    RetailPointShort,
    UserShort,
    WarehouseShort,
)
from app.domain.enums import EmployeeRole as PGEmployeeRole
from app.domain.enums import OrderStatus
from app.main import app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_service():
    service = AsyncMock()
    service._uow.retail_point_members.exists = AsyncMock(return_value=True)
    return service


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
    wid = uuid4()
    rpid = uuid4()
    now = datetime.now(UTC)
    return Order(
        id=oid,
        warehouse_id=wid,
        created_by_id=cid,
        retail_point_id=rpid,
        status=status,
        total_amount=Decimal("150000.00"),
        total_volume=Decimal("0.500"),
        created_at=now,
        updated_at=now,
        retail_point=RetailPointShort(
            id=rpid, name="Test Point", address="Test Address"
        ),
        warehouse=WarehouseShort(id=wid, name="Test Warehouse"),
        created_by=UserShort(id=cid, full_name="Test Client"),
    )


def _order_with_item(order_id=None, client_id=None, status=OrderStatus.PENDING):
    oid = order_id or uuid4()
    cid = client_id or uuid4()
    wid = uuid4()
    rpid = uuid4()
    pid = uuid4()
    now = datetime.now(UTC)
    order = Order(
        id=oid,
        warehouse_id=wid,
        created_by_id=cid,
        retail_point_id=rpid,
        status=status,
        total_amount=Decimal("150000.00"),
        total_volume=Decimal("0.500"),
        created_at=now,
        updated_at=now,
        retail_point=RetailPointShort(
            id=rpid, name="Test Point", address="Test Address"
        ),
        warehouse=WarehouseShort(id=wid, name="Test Warehouse"),
        created_by=UserShort(id=cid, full_name="Test Client"),
    )
    item = OrderItem(
        order_id=oid,
        product_id=pid,
        quantity=10,
        price_at_order=Decimal("15000.00"),
        total_volume=Decimal("0.050"),
        product_name="Test Product",
        product=ProductShort(id=pid, name="Test Product"),
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
    async def test_create_order_client_forbidden_not_member(
        self, client, mock_service, mock_client_entity
    ):
        mock_service._uow.retail_point_members.exists = AsyncMock(return_value=False)

        resp = await client.post(
            "/api/v1/orders",
            json={
                "warehouse_id": str(uuid4()),
                "retail_point_id": str(uuid4()),
                "items": [{"product_id": str(uuid4()), "quantity": 10}],
            },
        )
        assert resp.status_code == 403
        assert resp.json()["detail"] == "Not your retail point"

    @pytest.mark.asyncio
    async def test_create_order_by_employee_success(
        self, client, mock_service, mock_admin_employee
    ):
        app.dependency_overrides[get_current_user] = lambda: mock_admin_employee
        client_id = uuid4()
        from app.domain.entities.retail_point_members import RetailPointMember

        mock_service._uow.retail_point_members.get_by_retail_point = AsyncMock(
            return_value=[
                RetailPointMember(retail_point_id=uuid4(), client_id=client_id)
            ]
        )
        order = _order_response(client_id=client_id)
        mock_service.create.return_value = order

        resp = await client.post(
            "/api/v1/orders",
            json={
                "warehouse_id": str(uuid4()),
                "retail_point_id": str(uuid4()),
                "items": [{"product_id": str(uuid4()), "quantity": 5}],
            },
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == OrderStatus.PENDING.value
        mock_service.create.assert_awaited_once()

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
        order.planned_delivery_date = date(2026, 8, 26)
        order.delivery_agent_name = "Жасур Каримов"
        mock_service.get_by_id = AsyncMock(return_value=order)

        resp = await client.get(f"/api/v1/orders/{order.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == str(order.id)
        assert resp.json()["planned_delivery_date"] == "2026-08-26"
        assert resp.json()["delivery_agent_name"] == "Жасур Каримов"

    @pytest.mark.asyncio
    async def test_get_order_not_found(self, client, mock_service):

        mock_service.get_by_id = AsyncMock(side_effect=ValueError("Order not found"))

        resp = await client.get(f"/api/v1/orders/{uuid4()}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_order_forbidden(self, client, mock_service):
        order = _order_response(client_id=uuid4())
        mock_service.get_by_id = AsyncMock(return_value=order)
        mock_service._uow.retail_point_members.exists = AsyncMock(return_value=False)

        resp = await client.get(f"/api/v1/orders/{order.id}")
        assert resp.status_code == 403

    # --- DELETE /api/v1/orders/{order_id} ---

    @pytest.mark.asyncio
    async def test_cancel_order_by_client_success(
        self, client, mock_service, mock_client_entity
    ):
        order = _order_response(client_id=mock_client_entity.id)
        mock_service.get_by_id = AsyncMock(return_value=order)
        mock_service.cancel = AsyncMock()

        resp = await client.delete(f"/api/v1/orders/{order.id}")
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_cancel_order_by_client_not_found(self, client, mock_service):
        mock_service.get_by_id = AsyncMock(side_effect=ValueError("Order not found"))

        resp = await client.delete(f"/api/v1/orders/{uuid4()}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_cancel_order_by_client_forbidden(self, client, mock_service):
        order = _order_response(client_id=uuid4())
        mock_service.get_by_id = AsyncMock(return_value=order)
        mock_service._uow.retail_point_members.exists = AsyncMock(return_value=False)

        resp = await client.delete(f"/api/v1/orders/{order.id}")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_cancel_order_by_client_value_error(
        self, client, mock_service, mock_client_entity
    ):
        order = _order_response(client_id=mock_client_entity.id)
        mock_service.get_by_id = AsyncMock(return_value=order)
        mock_service.cancel.side_effect = ValueError("Cannot confirm order")

        resp = await client.delete(f"/api/v1/orders/{order.id}")
        assert resp.status_code == 400

    # --- POST /api/v1/orders/{order_id}/deliver (by client) ---

    @pytest.mark.asyncio
    async def test_deliver_order_by_client_success(
        self, client, mock_service, mock_client_entity
    ):
        order = _order_response(
            client_id=mock_client_entity.id, status=OrderStatus.DELIVERED
        )
        mock_service.get_by_id = AsyncMock(return_value=order)
        mock_service.deliver = AsyncMock(return_value=order)

        resp = await client.post(f"/api/v1/orders/{order.id}/deliver")
        assert resp.status_code == 200
        assert resp.json()["status"] == OrderStatus.DELIVERED.value
        mock_service.deliver.assert_awaited_once_with(
            order.id, employee_id=None, visit_id=None
        )

    @pytest.mark.asyncio
    async def test_deliver_order_by_client_forbidden(self, client, mock_service):
        order = _order_response(client_id=uuid4())
        mock_service.get_by_id = AsyncMock(return_value=order)
        mock_service._uow.retail_point_members.exists = AsyncMock(return_value=False)

        resp = await client.post(f"/api/v1/orders/{order.id}/deliver")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_deliver_order_by_client_not_found(self, client, mock_service):
        mock_service.get_by_id = AsyncMock(side_effect=ValueError("Order not found"))

        resp = await client.post(f"/api/v1/orders/{uuid4()}/deliver")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Staff endpoints: GET /api/v1/orders, GET /counters, POST /{id}/confirm...
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

    # --- GET /api/v1/orders ---

    @pytest.mark.asyncio
    async def test_list_orders_success(self, client, mock_service):
        order = _order_response()
        mock_service.list_orders.return_value = [order]

        resp = await client.get("/api/v1/orders")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        mock_service.list_orders.assert_awaited_once_with(
            statuses=None, limit=50, offset=0
        )

    @pytest.mark.asyncio
    async def test_list_orders_with_valid_statuses_filter(self, client, mock_service):
        order1 = _order_response(status=OrderStatus.PENDING)
        order2 = _order_response(status=OrderStatus.CONFIRMED)
        mock_service.list_orders.return_value = [order1, order2]

        resp = await client.get("/api/v1/orders?statuses=pending&statuses=confirmed")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        mock_service.list_orders.assert_awaited_once_with(
            statuses=[OrderStatus.PENDING, OrderStatus.CONFIRMED],
            limit=50,
            offset=0,
        )

    @pytest.mark.asyncio
    async def test_list_orders_invalid_status_error(self, client, mock_service):
        resp = await client.get("/api/v1/orders?statuses=invalid_status_value")
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Invalid order status"

    @pytest.mark.asyncio
    async def test_get_orders_counters_success(
        self, client, mock_service, mock_admin_employee
    ):
        expected_counters = {
            OrderStatus.PENDING: 3,
            OrderStatus.CONFIRMED: 2,
            OrderStatus.ASSEMBLY_STARTED: 5,
            OrderStatus.ASSEMBLED: 4,
            OrderStatus.SHIPPED: 3,
            OrderStatus.DELIVERED: 45,
            OrderStatus.CANCELLED: 1,
        }
        mock_service.get_counts_by_status.return_value = expected_counters

        resp = await client.get("/api/v1/orders/counters")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pending"] == 3
        assert data["confirmed"] == 2
        assert data["delivered"] == 45
        mock_service.get_counts_by_status.assert_awaited_once()

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

    # --- POST /api/v1/orders/{order_id}/start-assembly ---

    @pytest.mark.asyncio
    async def test_start_assembly_success(self, client, mock_service):
        order = _order_with_item(status=OrderStatus.ASSEMBLY_STARTED)
        mock_service.start_assembly.return_value = order

        resp = await client.post(f"/api/v1/orders/{order.id}/start-assembly")
        assert resp.status_code == 200
        assert resp.json()["status"] == OrderStatus.ASSEMBLY_STARTED.value

    @pytest.mark.asyncio
    async def test_start_assembly_not_found(self, client, mock_service):
        mock_service.start_assembly.side_effect = ValueError("not found")

        resp = await client.post(f"/api/v1/orders/{uuid4()}/start-assembly")
        assert resp.status_code == 400

    # --- POST /api/v1/orders/{order_id}/load ---

    @pytest.mark.asyncio
    async def test_load_order_success(self, client, mock_service):
        order = _order_with_item(status=OrderStatus.LOADED)
        mock_service.load_order.return_value = order

        resp = await client.post(f"/api/v1/orders/{order.id}/load")
        assert resp.status_code == 200
        assert resp.json()["status"] == OrderStatus.LOADED.value
        mock_service.load_order.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_load_order_not_found(self, client, mock_service):
        mock_service.load_order.side_effect = ValueError("not found")

        resp = await client.post(f"/api/v1/orders/{uuid4()}/load")
        assert resp.status_code == 404

    # --- POST /api/v1/orders/load-today ---

    @pytest.mark.asyncio
    async def test_load_today_orders_success(self, client, mock_service):
        order = _order_with_item(status=OrderStatus.LOADED)
        mock_service.load_today_orders.return_value = [order]

        resp = await client.post("/api/v1/orders/load-today")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["status"] == OrderStatus.LOADED.value
        mock_service.load_today_orders.assert_awaited_once()
