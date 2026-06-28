from app.services.audit_service import AuditService


class AuditLogController:

    def __init__(self):
        self.service = AuditService()

    def get_logs(self, limit=100):
        return self.service.repo.list_all(limit)

    def get_filtered_logs(self, action=None, status=None, server=None):

        logs = self.service.repo.list_all(500)

        if action:
            logs = [l for l in logs if l.action == action]

        if status:
            logs = [l for l in logs if l.status == status]

        if server:
            logs = [l for l in logs if l.server == server]

        return logs