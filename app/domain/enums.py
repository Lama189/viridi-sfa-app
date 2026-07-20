from enum import Enum


class EmployeeRole(str, Enum):
    ADMIN = "admin"
    AGENT = "agent"


class ClientType(str, Enum):
    B = "B"
    C = "C"


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"


class VisitStatus(str, Enum):
    COMPLETED = "completed"
    SKIPPED = "skipped"


class StockTransactionType(str, Enum):
    RECEIPT = "receipt"
    RESERVATION = "reservation"
    CANCEL_RESERVATION = "cancel_reservation"
    SALE = "sale"
    WRITEOFF = "writeoff"
    RETURN = "return"
    ADJUSTMENT = "adjustment"


class TransactionActorType(str, Enum):
    EMPLOYEE = "employee"
    CLIENT = "client"
    SYSTEM = "system"
