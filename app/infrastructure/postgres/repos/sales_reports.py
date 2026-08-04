from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Numeric, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.dashboard import CategoryReportDTO, DailyReportDTO
from app.application.interfaces.repos.sales_reports import ISalesReportRepository
from app.infrastructure.postgres.models.categories import Category
from app.infrastructure.postgres.models.enums import OrderStatus
from app.infrastructure.postgres.models.order_items import OrderItem
from app.infrastructure.postgres.models.orders import Order
from app.infrastructure.postgres.models.products import Product
from app.infrastructure.postgres.models.visits import Visit


class SalesReportRepository(ISalesReportRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_agent_daily_report(
        self,
        agent_id: UUID,
        date_from: datetime,
        date_to: datetime,
    ) -> DailyReportDTO:
        volume_boxes = cast(OrderItem.quantity, Numeric) / func.nullif(
            Product.items_in_box, 0
        )
        total_amount = func.sum(OrderItem.quantity * OrderItem.price_at_order)
        order_statuses = (OrderStatus.CONFIRMED, OrderStatus.SHIPPED)
        filters = (
            Visit.employee_id == agent_id,
            Visit.started_at >= date_from,
            Visit.started_at < date_to,
            Order.status.in_(order_statuses),
        )

        categories_stmt = (
            select(
                Category.id.label("category_id"),
                Category.name.label("category_name"),
                func.sum(OrderItem.quantity).label("quantity_pcs"),
                func.round(func.sum(volume_boxes), 1).label("volume_boxes"),
                total_amount.label("total_amount"),
            )
            .select_from(OrderItem)
            .join(Product, OrderItem.product_id == Product.id)
            .join(Category, Product.category_id == Category.id)
            .join(Order, OrderItem.order_id == Order.id)
            .join(Visit, Order.visit_id == Visit.id)
            .where(*filters)
            .group_by(Category.id, Category.name)
            .order_by(total_amount.desc())
        )

        categories_result = await self._session.execute(categories_stmt)
        categories = [
            CategoryReportDTO(**row._asdict()) for row in categories_result.all()
        ]

        summary_stmt = (
            select(
                func.coalesce(total_amount, Decimal("0.00")).label("total_amount"),
                func.count(func.distinct(Order.retail_point_id)).label("acb_count"),
                func.coalesce(func.sum(OrderItem.quantity), 0).label(
                    "total_quantity_pcs"
                ),
                func.round(
                    func.coalesce(func.sum(volume_boxes), Decimal("0.0")),
                    1,
                ).label("total_volume_boxes"),
            )
            .select_from(OrderItem)
            .join(Product, OrderItem.product_id == Product.id)
            .join(Order, OrderItem.order_id == Order.id)
            .join(Visit, Order.visit_id == Visit.id)
            .where(*filters)
        )

        summary = (await self._session.execute(summary_stmt)).one()
        return DailyReportDTO(
            total_amount=summary.total_amount,
            acb_count=summary.acb_count,
            total_quantity_pcs=summary.total_quantity_pcs,
            total_volume_boxes=summary.total_volume_boxes,
            categories=categories,
        )
