from database.models import ScheduledJob
from repositories.base_repository import BaseRepository


class ScheduledJobRepository(BaseRepository):

    def create(
        self,
        operation_item_id,
        job_id,
        fecha_programada
    ):

        job = ScheduledJob(
            operation_item_id=operation_item_id,
            job_id=job_id,
            fecha_programada=fecha_programada
        )

        self.db.add(job)
        self.commit()

        return job

    def get_all(self):
        return (
            self.db.query(ScheduledJob)
            .order_by(ScheduledJob.fecha_programada)
            .all()
        )

    def get_by_id(self, job_id):
        return (
            self.db.query(ScheduledJob)
            .filter(ScheduledJob.id == job_id)
            .first()
        )

    def get_pending(self):
        return (
            self.db.query(ScheduledJob)
            .filter(ScheduledJob.estado == "PENDIENTE")
            .all()
        )

    def update_status(self, job_id, estado, resultado=None):

        job = self.get_by_id(job_id)

        if not job:
            return None

        job.estado = estado
        job.ultimo_resultado = resultado

        self.commit()

        return job

    def delete(self, job_id):

        job = self.get_by_id(job_id)

        if not job:
            return False

        self.db.delete(job)
        self.commit()

        return True