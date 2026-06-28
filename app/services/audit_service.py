from app.services.audit_worker import AuditWorker
from app.services.audit_event import AuditEvent


class AuditService:

    def __init__(self):
        self.worker = AuditWorker.get_instance()

    def log(self, action, status, message=None, entity=None, server=None):

        event = AuditEvent(
            action=action,
            status=status,
            message=message,
            entity=entity,
            server=server
        )

        self.worker.emit(event)

    def log_success(self, action, message=None, entity=None, server=None):
        self.log(action, "SUCCESS", message, entity, server)

    def log_error(self, action, message=None, entity=None, server=None):
        self.log(action, "ERROR", message, entity, server)