from app.core.extensions import DomainError


class WarehouseNotFoundError(DomainError):
    pass


class WarehouseInactiveError(DomainError):
    pass


class ProductNotFoundError(DomainError):
    pass


class ProductInactiveError(DomainError):
    pass


class StockNotFoundError(DomainError):
    pass


class StockAlreadyExistsError(DomainError):
    pass


class InsufficientStockError(DomainError):
    pass


class InsufficientReservedStockError(DomainError):
    pass


class InsufficientReservationError(DomainError):
    pass
