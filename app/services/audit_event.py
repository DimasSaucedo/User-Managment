from dataclasses import dataclass
from datetime import datetime


@dataclass
class AuditEvent:
    action: str
    status: str
    message: str = None
    entity: str = None
    server: str = None
    created_at: datetime = datetime.utcnow()