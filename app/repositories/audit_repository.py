from app.database.database import SessionLocal
from app.models.audit_log import AuditLog

class AuditRepository:

    def __init__(self):
        self.db = SessionLocal()

    def create(self, log: AuditLog):
        try:
            self.db.add(log)
            self.db.commit()
            self.db.refresh(log)
            return log
        except Exception as e:
            self.db.rollback()
            raise e

    def list_all(self, limit=100):
        return self.db.query(AuditLog)\
            .order_by(AuditLog.created_at.desc())\
            .limit(limit)\
            .all()