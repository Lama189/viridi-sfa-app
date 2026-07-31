from datetime import datetime, UTC, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.postgres.models.categories import Category
from app.infrastructure.postgres.models.enums import OrderStatus, VisitStatus
from app.infrastructure.postgres.models.order_items import OrderItem
from app.infrastructure.postgres.models.orders import Order
from app.infrastructure.postgres.models.products import Product
from app.infrastructure.postgres.models.visits import Visit
from app.infrastructure.postgres.repos.sales_reports import SalesReportRepository


@pytest.mark.asyncio
async def test_get_agent_daily_report_empty(session: AsyncSession):
    repo = SalesReportRepository(session)
    agent_id = uuid4()
    now = datetime.now(UTC)
    date_from = now - timedelta(days=1)
    date_to = now + timedelta(days=1)

    report = await repo.get_agent_daily_report(agent_id, date_from, date_to)

    assert report.total_amount == Decimal("0.00")
    assert report.acb_count == 0
    assert report.total_quantity_pcs == 0
    assert report.total_volume_boxes == Decimal("0.0")
    assert report.categories == []


@pytest.mark.asyncio
async def test_get_agent_daily_report_with_data(session: AsyncSession):
    repo = SalesReportRepository(session)
    agent_id = uuid4()

    now = datetime.now(UTC)
    date_from = now - timedelta(hours=1)
    date_to = now + timedelta(hours=1)

    # 1. Setup Categories
    cat_drinks = Category(id=uuid4(), name="Drinks", is_active=True)
    cat_snacks = Category(id=uuid4(), name="Snacks", is_active=True)
    session.add_all([cat_drinks, cat_snacks])

    # 2. Setup Products
    prod_soda = Product(
        id=uuid4(),
        category_id=cat_drinks.id,
        name="Soda 1L",
        price=Decimal("10.00"),
        items_in_box=10,
    )
    prod_chips = Product(
        id=uuid4(),
        category_id=cat_snacks.id,
        name="Chips 100g",
        price=Decimal("5.00"),
        items_in_box=20,
    )
    session.add_all([prod_soda, prod_chips])

    # 3. Setup Retail Points & Visits
    rp1_id = uuid4()
    rp2_id = uuid4()

    visit1 = Visit(
        id=uuid4(),
        employee_id=agent_id,
        retail_point_id=rp1_id,
        status=VisitStatus.COMPLETED,
        started_at=now,
    )
    visit2 = Visit(
        id=uuid4(),
        employee_id=agent_id,
        retail_point_id=rp2_id,
        status=VisitStatus.COMPLETED,
        started_at=now,
    )
    session.add_all([visit1, visit2])

    # 4. Setup Orders & OrderItems
    wh_id = uuid4()
    client_id = uuid4()

    order1 = Order(
        id=uuid4(),
        warehouse_id=wh_id,
        created_by_id=client_id,
        retail_point_id=rp1_id,
        visit_id=visit1.id,
        status=OrderStatus.CONFIRMED,
        total_amount=Decimal("500.00"),
    )
    order2 = Order(
        id=uuid4(),
        warehouse_id=wh_id,
        created_by_id=client_id,
        retail_point_id=rp2_id,
        visit_id=visit2.id,
        status=OrderStatus.SHIPPED,
        total_amount=Decimal("200.00"),
    )
    session.add_all([order1, order2])

    # Order 1 items: 30 Soda (3 boxes @ 10 = 300) + 40 Chips (2 boxes @ 5 = 200)
    item1_1 = OrderItem(
        id=uuid4(),
        order_id=order1.id,
        product_id=prod_soda.id,
        quantity=30,
        price_at_order=Decimal("10.00"),
        total_volume=Decimal("3.0"),
    )
    item1_2 = OrderItem(
        id=uuid4(),
        order_id=order1.id,
        product_id=prod_chips.id,
        quantity=40,
        price_at_order=Decimal("5.00"),
        total_volume=Decimal("2.0"),
    )

    # Order 2 items: 20 Soda (2 boxes @ 10 = 200)
    item2_1 = OrderItem(
        id=uuid4(),
        order_id=order2.id,
        product_id=prod_soda.id,
        quantity=20,
        price_at_order=Decimal("10.00"),
        total_volume=Decimal("2.0"),
    )
    session.add_all([item1_1, item1_2, item2_1])
    await session.commit()

    report = await repo.get_agent_daily_report(agent_id, date_from, date_to)

    # Total Soda: 50 pcs (5.0 boxes) @ 10 = 500.00
    # Total Chips: 40 pcs (2.0 boxes) @ 5 = 200.00
    # Total Amount: 700.00
    assert report.total_amount == Decimal("700.00")
    assert report.acb_count == 2
    assert report.total_quantity_pcs == 90
    assert report.total_volume_boxes == Decimal("7.0")

    assert len(report.categories) == 2
    # Drinks should be first because 500 > 200
    assert report.categories[0].category_name == "Drinks"
    assert report.categories[0].quantity_pcs == 50
    assert report.categories[0].volume_boxes == Decimal("5.0")
    assert report.categories[0].total_amount == Decimal("500.00")

    assert report.categories[1].category_name == "Snacks"
    assert report.categories[1].quantity_pcs == 40
    assert report.categories[1].volume_boxes == Decimal("2.0")
    assert report.categories[1].total_amount == Decimal("200.00")


@pytest.mark.asyncio
async def test_get_agent_daily_report_filters_unconfirmed_other_agents_outside_date(session: AsyncSession):
    repo = SalesReportRepository(session)
    target_agent_id = uuid4()
    other_agent_id = uuid4()

    now = datetime.now(UTC)
    date_from = now - timedelta(hours=2)
    date_to = now + timedelta(hours=2)

    cat = Category(id=uuid4(), name="General", is_active=True)
    session.add(cat)

    prod = Product(
        id=uuid4(),
        category_id=cat.id,
        name="Item 1",
        price=Decimal("100.00"),
        items_in_box=1,
    )
    session.add(prod)

    rp_id = uuid4()
    wh_id = uuid4()
    client_id = uuid4()

    # 1. Unconfirmed order (status PENDING) for target agent -> Should be ignored
    visit_unconfirmed = Visit(
        id=uuid4(), employee_id=target_agent_id, retail_point_id=rp_id, started_at=now
    )
    order_unconfirmed = Order(
        id=uuid4(),
        warehouse_id=wh_id,
        created_by_id=client_id,
        retail_point_id=rp_id,
        visit_id=visit_unconfirmed.id,
        status=OrderStatus.PENDING,
    )
    item_unconfirmed = OrderItem(
        id=uuid4(), order_id=order_unconfirmed.id, product_id=prod.id, quantity=10, price_at_order=Decimal("100.00"), total_volume=Decimal("10.0")
    )
    session.add_all([visit_unconfirmed, order_unconfirmed, item_unconfirmed])

    # 2. Visit outside date range (started 10 hours ago) -> Should be ignored
    visit_old = Visit(
        id=uuid4(), employee_id=target_agent_id, retail_point_id=rp_id, started_at=now - timedelta(hours=10)
    )
    order_old = Order(
        id=uuid4(),
        warehouse_id=wh_id,
        created_by_id=client_id,
        retail_point_id=rp_id,
        visit_id=visit_old.id,
        status=OrderStatus.CONFIRMED,
    )
    item_old = OrderItem(
        id=uuid4(), order_id=order_old.id, product_id=prod.id, quantity=10, price_at_order=Decimal("100.00"), total_volume=Decimal("10.0")
    )
    session.add_all([visit_old, order_old, item_old])

    # 3. Visit for different agent -> Should be ignored
    visit_other_agent = Visit(
        id=uuid4(), employee_id=other_agent_id, retail_point_id=rp_id, started_at=now
    )
    order_other_agent = Order(
        id=uuid4(),
        warehouse_id=wh_id,
        created_by_id=client_id,
        retail_point_id=rp_id,
        visit_id=visit_other_agent.id,
        status=OrderStatus.CONFIRMED,
    )
    item_other_agent = OrderItem(
        id=uuid4(), order_id=order_other_agent.id, product_id=prod.id, quantity=10, price_at_order=Decimal("100.00"), total_volume=Decimal("10.0")
    )
    session.add_all([visit_other_agent, order_other_agent, item_other_agent])

    await session.commit()

    report = await repo.get_agent_daily_report(target_agent_id, date_from, date_to)

    assert report.total_amount == Decimal("0.00")
    assert report.acb_count == 0
    assert report.total_quantity_pcs == 0
    assert report.total_volume_boxes == Decimal("0.0")
    assert report.categories == []
