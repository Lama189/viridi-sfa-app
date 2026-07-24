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
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class StockTransactionType(str, Enum):
    RECEIPT = "receipt"          # Приход от поставщика / Пополнение
    RESERVATION = "reservation"  # Бронь под заказ
    CANCEL_RESERVATION = "cancel_reservation" # Отмена брони
    SALE = "sale"                # Фактическое списание при отгрузке
    WRITEOFF = "writeoff"        # Списание (брак, порча)
    RETURN = "return"            # Возврат от клиента
    ADJUSTMENT = "adjustment"    # Инвентаризация / Корректировка


class TransactionActorType(str, Enum):
    EMPLOYEE = "employee"
    CLIENT = "client"
    SYSTEM = "system"
