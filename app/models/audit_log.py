from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from app.database.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    action = Column(String(100), nullable=False)        # ej: SSH_EXEC, GROUP_MOD
    entity = Column(String(255), nullable=True)         # ej: usuario, servidor
    status = Column(String(50), nullable=False)         # SUCCESS / ERROR

    message = Column(Text, nullable=True)               # detalle
    server = Column(String(255), nullable=True)        # servidor afectado

    created_at = Column(DateTime, default=datetime.utcnow)