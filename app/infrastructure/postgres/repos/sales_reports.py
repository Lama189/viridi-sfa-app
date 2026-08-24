from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Numeric, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto.dashboard import (
    CategoryReportDTO,
    DailyReportDTO,
    ProductReportDTO,
)
from app.application.interfaces.repos.sales_reports import ISalesReportRepository
from app.domain.enums import OrderStatus
from app.infrastructure.postgres.models.categories import Category
from app.infrastructure.postgres.models.order_items import OrderItem
from app.infrastructure.postgres.models.orders import Order
from app.infrastructure.postgres.models.products import Product
from app.infrastructure.postgres.models.retail_point_assignments import (
    RetailPointAssignment,
)
from app.infrastructure.postgres.models.visit_plans import VisitPlan
from app.infrastructure.postgres.models.visits import Visit


class SalesReportRepository(ISalesReportRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_agent_daily_report(
        self,
        agent_id: UUID | None,
        date_from: datetime,
        date_to: datetime,
    ) -> DailyReportDTO:
        volume_boxes = cast(OrderItem.quantity, Numeric) / func.nullif(
            Product.items_in_box, 0
        )
        total_amount = func.sum(OrderItem.quantity * OrderItem.price_at_order)
        order_statuses = (
            OrderStatus.CONFIRMED,
            OrderStatus.ASSEMBLY_STARTED,
            OrderStatus.ASSEMBLED,
            OrderStatus.LOADED,
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
        )

        order_employee_id = func.coalesce(
            Visit.employee_id,
            VisitPlan.employee_id,
            RetailPointAssignment.employee_id,
        )
        order_date = func.coalesce(
            Visit.started_at,
            cast(VisitPlan.plan_date, DateTime(timezone=True)),
        )

        filters = [
            Order.status.in_(order_statuses),
            order_date >= date_from,
            order_date <= date_to,
        ]
        if agent_id is not None:
            filters.append(order_employee_id == agent_id)

        products_stmt = (
            select(
                Category.id.label("category_id"),
                Category.name.label("category_name"),
                Product.id.label("product_id"),
                Product.name.label("product_name"),
                func.sum(OrderItem.quantity).label("quantity_pcs"),
                func.round(func.sum(volume_boxes), 1).label("volume_boxes"),
                total_amount.label("total_amount"),
            )
            .select_from(OrderItem)
            .join(Product, OrderItem.product_id == Product.id)
            .join(Category, Product.category_id == Category.id)
            .join(Order, OrderItem.order_id == Order.id)
            .outerjoin(Visit, Order.actual_visit_id == Visit.id)
            .outerjoin(VisitPlan, Order.planned_visit_id == VisitPlan.id)
            .outerjoin(
                RetailPointAssignment,
                Order.retail_point_id == RetailPointAssignment.retail_point_id,
            )
            .where(*filters)
            .group_by(Category.id, Category.name, Product.id, Product.name)
            .order_by(Category.name, total_amount.desc())
        )

        products_result = await self._session.execute(products_stmt)

        categories_map: dict[UUID, dict[str, Any]] = {}
        for row in products_result.all():
            cat_id = row.category_id
            if cat_id not in categories_map:
                categories_map[cat_id] = {
                    "category_id": cat_id,
                    "category_name": row.category_name,
                    "quantity_pcs": 0,
                    "volume_boxes": Decimal("0.0"),
                    "total_amount": Decimal("0.00"),
                    "products": [],
                }

            prod_dto = ProductReportDTO(
                product_id=row.product_id,
                product_name=row.product_name,
                quantity_pcs=int(row.quantity_pcs or 0),
                volume_boxes=Decimal(str(row.volume_boxes or "0.0")),
                total_amount=Decimal(str(row.total_amount or "0.00")),
            )
            categories_map[cat_id]["products"].append(prod_dto)
            categories_map[cat_id]["quantity_pcs"] += int(row.quantity_pcs or 0)
            categories_map[cat_id]["volume_boxes"] += Decimal(
                str(row.volume_boxes or "0.0")
            )
            categories_map[cat_id]["total_amount"] += Decimal(
                str(row.total_amount or "0.00")
            )

        categories = [
            CategoryReportDTO(
                category_id=info["category_id"],
                category_name=info["category_name"],
                quantity_pcs=info["quantity_pcs"],
                volume_boxes=round(info["volume_boxes"], 1),
                total_amount=info["total_amount"],
                products=info["products"],
            )
            for info in categories_map.values()
        ]
        categories.sort(key=lambda c: c.total_amount, reverse=True)

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
            .outerjoin(Visit, Order.actual_visit_id == Visit.id)
            .outerjoin(VisitPlan, Order.planned_visit_id == VisitPlan.id)
            .outerjoin(
                RetailPointAssignment,
                Order.retail_point_id == RetailPointAssignment.retail_point_id,
            )
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
