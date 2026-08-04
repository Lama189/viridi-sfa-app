class DomainError(Exception):
    pass


# User / Auth Exceptions
class UserNotFoundError(DomainError):
    pass


class UserAlreadyExistsError(DomainError):
    pass


class InvalidPasswordError(DomainError):
    pass


class UserNotActiveError(DomainError):
    pass


class InvalidInviteCodeError(DomainError):
    pass


# Membership Exceptions
class MembershipNotFoundError(DomainError):
    pass


class MembershipAlreadyExistsError(DomainError):
    pass


# Media Exceptions
class MediaNotFoundError(DomainError):
    pass


# Retail Point Exceptions
class RetailPointNotFoundError(DomainError):
    pass


class RetailPointAlreadyExistsError(DomainError):
    pass


class RetailPointInactiveError(DomainError):
    pass


class RetailPointImageNotFoundError(DomainError):
    pass


class RetailPointImageAlreadyExistsError(DomainError):
    pass


class RetailPointAssignmentAlreadyExistsError(DomainError):
    pass


class RetailPointAssignmentNotFoundError(DomainError):
    pass


class DuplicateRetailPointError(DomainError):
    pass


class BulkCreateRetailPointsRequestIsEmptyError(DomainError):
    pass


# Warehouse & Product & Stock Exceptions
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


# Visit Exceptions
class VisitNotFoundError(DomainError):
    pass


class VisitNotActiveError(DomainError):
    pass


class VisitDebtNotFoundError(DomainError):
    pass


class VisitMediaNotFoundError(DomainError):
    pass


class VisitMediaAlreadyAttachedError(DomainError):
    pass


class EmployeeHasActiveVisitError(DomainError):
    pass


class VisitPlanNotFoundError(DomainError):
    pass


class VisitPlanAlreadyExistsError(DomainError):
    pass


# Territory & Route Generator Exceptions
class InvalidEmployeesCountError(DomainError):
    pass


class NoActiveAgentsFoundError(DomainError):
    pass


class NoActiveRetailPointsError(DomainError):
    pass


class TerritoryClustersNotBuiltError(DomainError):
    pass
