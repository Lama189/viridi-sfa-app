from enum import IntEnum, StrEnum


class Weekday(IntEnum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class EmployeeRole(StrEnum):
    ADMIN = "admin"
    AGENT = "agent"
    WAREHOUSE_WORKER = "warehouse_worker"


class ClientType(StrEnum):
    B = "B"
    C = "C"


class OrderStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    ASSEMBLY_STARTED = "assembly_started"
    ASSEMBLED = "assembled"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"



class StockTransactionType(StrEnum):
    RECEIPT = "receipt"
    RESERVATION = "reservation"
    CANCEL_RESERVATION = "cancel_reservation"
    SALE = "sale"
    WRITEOFF = "writeoff"
    RETURN = "return"
    ADJUSTMENT = "adjustment"


class TransactionActorType(StrEnum):
    EMPLOYEE = "employee"
    CLIENT = "client"
    SYSTEM = "system"


class StockReferenceType(StrEnum):
    ORDER = "order"
    RECEIPT = "receipt"
    TRANSFER = "transfer"
    INVENTORY = "inventory"
    RETURN = "return"
    WRITEOFF = "writeoff"


class VisitStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class VisitPlanStatus(StrEnum):
    PLANNED = "planned"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class VisitPlanItemStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MediaBucket(StrEnum):
    RETAIL_POINTS = "retail-point-images"
    VISITS = "visit-reports"
    DOCUMENTS = "documents"
    AVATARS = "avatars"


class OrderEventType(StrEnum):
    CREATED = "order.created"
    ASSEMBLY_STARTED = "order.assembly_started"
    ASSEMBLED = "order.assembled"
    TAKEN_BY_AGENT = "order.taken_by_agent"
    DELIVERED = "order.delivered"
    CANCELLED = "order.cancelled"


EventType = OrderEventType | str


class AggregateType(StrEnum):
    ORDER = "order"
    STOCK = "stock"
    CLIENT = "client"
    RETAIL_POINT = "retail_point"
