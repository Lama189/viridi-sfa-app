from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    AGENT = "agent"
    CLIENT = "client"


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
