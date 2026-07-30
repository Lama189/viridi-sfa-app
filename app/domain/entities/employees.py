from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.enums import EmployeeRole  


@dataclass(slots=True)
class Employee:
    phone: str
    password_hash: str
    full_name: str
    
    id: UUID = field(default_factory=uuid4)
    role: EmployeeRole = EmployeeRole.AGENT
    is_active: bool = True
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)