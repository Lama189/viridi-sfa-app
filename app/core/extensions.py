class DomainError(Exception):
    pass


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


class MembershipNotFoundError(DomainError):
    pass


class MembershipAlreadyExistsError(DomainError):
    pass


class MediaNotFoundError(DomainError):
    pass


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


class RetailPointAssignmentAlreadyExistsError(DomainError):
    pass


class RetailPointAssignmentNotFoundError(DomainError):
    pass


class DuplicateRetailPointError(DomainError):
    pass


class BulkCreateRetailPointsRequestIsEmptyError(DomainError):
    pass


class VisitPlanNotFoundError(DomainError):
    pass


class VisitPlanAlreadyExistsError(DomainError):
    pass


class InvalidEmployeesCountError(DomainError):
    pass

class NoActiveAgentsFoundError(DomainError):
    pass

class NoActiveRetailPointsError(DomainError):
    pass

class TerritoryClustersNotBuiltError(DomainError):
    pass