import threading
import queue

from app.repositories.audit_repository import AuditRepository
from app.models.audit_log import AuditLog


class AuditWorker(threading.Thread):

    _instance = None
    _queue = queue.Queue()

    def __init__(self):
        super().__init__(daemon=True)
        self.repo = AuditRepository()
        self.running = True

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = AuditWorker()
            cls._instance.start()
        return cls._instance

    @classmethod
    def emit(cls, event):
        cls._queue.put(event)

    def run(self):
        while self.running:
            try:
                event = self._queue.get()

                log = AuditLog(
                    action=event.action,
                    status=event.status,
                    message=event.message,
                    entity=event.entity,
                    server=event.server,
                )

                self.repo.create(log)

            except Exception as e:
                print(f"[AuditWorker Error] {e}")