from database.models import OperationItem
from repositories.base_repository import BaseRepository


class OperationItemRepository(BaseRepository):

    def create(
        self,
        operation_id,
        server_id,
        usuario,
        grupo,
        tipo,
        inicio=None,
        fin=None
    ):

        item = OperationItem(
            operation_id=operation_id,
            server_id=server_id,
            usuario=usuario,
            grupo=grupo,
            tipo=tipo,
            inicio=inicio,
            fin=fin
        )

        self.db.add(item)
        self.commit()

        return item

    def get_all(self):
        return (
            self.db.query(OperationItem)
            .order_by(OperationItem.created_at.desc())
            .all()
        )

    def get_by_id(self, item_id):
        return (
            self.db.query(OperationItem)
            .filter(OperationItem.id == item_id)
            .first()
        )

    def get_by_operation(self, operation_id):
        return (
            self.db.query(OperationItem)
            .filter(OperationItem.operation_id == operation_id)
            .all()
        )

    def update_status(self, item_id, estado, mensaje=None):

        item = self.get_by_id(item_id)

        if not item:
            return None

        item.estado = estado
        item.mensaje = mensaje

        self.commit()

        return item

    def delete(self, item_id):

        item = self.get_by_id(item_id)

        if not item:
            return False

        self.db.delete(item)
        self.commit()

        return True