from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.extensions import (
    DomainError,
    UserNotFoundError,
    UserAlreadyExistsError,
    InvalidPasswordError,
    UserNotActiveError,
    InvalidInviteCodeError,
    MembershipNotFoundError,
    MembershipAlreadyExistsError,
    MediaNotFoundError,
    RetailPointNotFoundError,
    RetailPointAlreadyExistsError,
    RetailPointInactiveError,
    RetailPointImageNotFoundError,
    RetailPointImageAlreadyExistsError,
    VisitNotFoundError,
    VisitNotActiveError,
    VisitDebtNotFoundError,
    VisitMediaNotFoundError,
    VisitMediaAlreadyAttachedError,
    EmployeeHasActiveVisitError,
    RetailPointAssignmentAlreadyExistsError,
    RetailPointAssignmentNotFoundError,
    DuplicateRetailPointError,
    BulkCreateRetailPointsRequestIsEmptyError,
    VisitPlanNotFoundError,
    VisitPlanAlreadyExistsError,
)
from app.core.exceptions import (
    WarehouseNotFoundError,
    WarehouseInactiveError,
    ProductNotFoundError,
    ProductInactiveError,
    StockNotFoundError,
    StockAlreadyExistsError,
    InsufficientStockError,
    InsufficientReservedStockError,
    InsufficientReservationError,
)

ERROR_MAPPING = {
    UserNotFoundError: (404, "User not found"),
    UserAlreadyExistsError: (409, "User already exists"),
    InvalidPasswordError: (401, "Invalid password"),
    UserNotActiveError: (403, "User is not active"),
    InvalidInviteCodeError: (400, "Invalid invite code"),
    MembershipNotFoundError: (404, "Membership not found"),
    MembershipAlreadyExistsError: (409, "Membership already exists"),
    MediaNotFoundError: (404, "Media not found"),
    RetailPointNotFoundError: (404, "Retail point not found"),
    RetailPointAlreadyExistsError: (409, "Retail point already exists"),
    RetailPointInactiveError: (409, "Retail point is inactive"),
    RetailPointImageNotFoundError: (404, "Retail point image not found"),
    RetailPointImageAlreadyExistsError: (409,"Retail point already has an image"),
    VisitNotFoundError: (404, "Visit not found"),
    VisitNotActiveError: (409, "Visit is not active"),
    VisitDebtNotFoundError: (404, "Visit debt not found"),
    VisitMediaNotFoundError: (404, "Visit media not found"),
    VisitMediaAlreadyAttachedError: (409,"Media is already attached to visit"),
    EmployeeHasActiveVisitError: (409,"Employee already has an active visit"),
    RetailPointAssignmentAlreadyExistsError: (409, "Retail point assignment already exists"),
    RetailPointAssignmentNotFoundError: (404, "Retail point assignment not found"),
    DuplicateRetailPointError: (409, "Duplicate retail point in request"),
    BulkCreateRetailPointsRequestIsEmptyError: (400, "Bulk create request is empty"),
    VisitPlanNotFoundError: (404, "Visit plan not found"),
    VisitPlanAlreadyExistsError: (409, "Visit plan already exists for this date"),
    WarehouseNotFoundError: (404, "Warehouse not found"),
    WarehouseInactiveError: (409, "Warehouse is inactive"),
    ProductNotFoundError: (404, "Product not found"),
    ProductInactiveError: (409, "Product is inactive"),
    StockNotFoundError: (404, "Stock not found"),
    StockAlreadyExistsError: (409, "Stock already exists"),
    InsufficientStockError: (400, "Insufficient stock"),
    InsufficientReservedStockError: (400, "Insufficient reserved stock"),
    InsufficientReservationError: (400, "Insufficient reservation"),
}


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(DomainError)
    async def exception_handler(
        request: Request,
        exc: Exception,
    ):
        error = ERROR_MAPPING.get(type(exc))

        if error is None:
            raise exc

        status_code, detail = error

        return JSONResponse(
            status_code=status_code,
            content={
                "detail": detail,
            },
        )