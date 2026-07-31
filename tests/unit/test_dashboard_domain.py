from decimal import Decimal
from uuid import uuid4

from app.domain.entities.dashboard import CategoryReport, DailyReport, EmployeeDashboard


def test_employee_dashboard_creation():
    dashboard = EmployeeDashboard(
        total_points=10,
        completed_points=5,
        remaining_points=5,
        completion_percentage=Decimal("50.0"),
        orders_count=3,
        orders_amount=Decimal("150000.00"),
        debts_count=1,
    )

    assert dashboard.total_points == 10
    assert dashboard.completed_points == 5
    assert dashboard.remaining_points == 5
    assert dashboard.completion_percentage == Decimal("50.0")
    assert dashboard.orders_count == 3
    assert dashboard.orders_amount == Decimal("150000.00")
    assert dashboard.debts_count == 1


def test_category_report_creation():
    cat_id = uuid4()
    cat_report = CategoryReport(
        category_id=cat_id,
        category_name="Beverages",
        quantity_pcs=120,
        volume_boxes=Decimal("10.0"),
        total_amount=Decimal("500000.00"),
    )

    assert cat_report.category_id == cat_id
    assert cat_report.category_name == "Beverages"
    assert cat_report.quantity_pcs == 120
    assert cat_report.volume_boxes == Decimal("10.0")
    assert cat_report.total_amount == Decimal("500000.00")


def test_daily_report_creation():
    cat_id1 = uuid4()
    cat_id2 = uuid4()
    cat1 = CategoryReport(
        category_id=cat_id1,
        category_name="Beverages",
        quantity_pcs=100,
        volume_boxes=Decimal("10.0"),
        total_amount=Decimal("400000.00"),
    )
    cat2 = CategoryReport(
        category_id=cat_id2,
        category_name="Snacks",
        quantity_pcs=50,
        volume_boxes=Decimal("5.0"),
        total_amount=Decimal("100000.00"),
    )

    daily_report = DailyReport(
        total_amount=Decimal("500000.00"),
        acb_count=4,
        total_quantity_pcs=150,
        total_volume_boxes=Decimal("15.0"),
        categories=[cat1, cat2],
    )

    assert daily_report.total_amount == Decimal("500000.00")
    assert daily_report.acb_count == 4
    assert daily_report.total_quantity_pcs == 150
    assert daily_report.total_volume_boxes == Decimal("15.0")
    assert len(daily_report.categories) == 2
    assert daily_report.categories[0].category_name == "Beverages"
    assert daily_report.categories[1].category_name == "Snacks"


def test_daily_report_empty_categories():
    daily_report = DailyReport(
        total_amount=Decimal("0.00"),
        acb_count=0,
        total_quantity_pcs=0,
        total_volume_boxes=Decimal("0.0"),
        categories=[],
    )

    assert daily_report.total_amount == Decimal("0.00")
    assert daily_report.acb_count == 0
    assert daily_report.total_quantity_pcs == 0
    assert daily_report.total_volume_boxes == Decimal("0.0")
    assert daily_report.categories == []
