from database.models import Operation
from repositories.base_repository import BaseRepository


class OperationRepository(BaseRepository):

    def create(
        self,
        ticket,
        operador,
        tipo,
        observaciones=None
    ):

        operation = Operation(
            ticket=ticket,
            operador=operador,
            tipo=tipo,
            observaciones=observaciones
        )

        self.db.add(operation)
        self.commit()

        return operation

    def get_all(self):
        return (
            self.db.query(Operation)
            .order_by(Operation.created_at.desc())
            .all()
        )

    def get_by_id(self, operation_id):
        return (
            self.db.query(Operation)
            .filter(Operation.id == operation_id)
            .first()
        )

    def update_status(self, operation_id, estado):

        operation = self.get_by_id(operation_id)

        if not operation:
            return None

        operation.estado = estado

        self.commit()

        return operation

    def delete(self, operation_id):

        operation = self.get_by_id(operation_id)

        if not operation:
            return False

        self.db.delete(operation)

        self.commit()

        return True