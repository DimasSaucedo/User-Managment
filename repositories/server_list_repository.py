from database.models import ServerList
from repositories.base_repository import BaseRepository


class ServerListRepository(BaseRepository):

    def create(self, nombre, descripcion=None):
        item = ServerList(
            nombre=nombre,
            descripcion=descripcion
        )

        self.db.add(item)
        self.commit()

        return item

    def get_all(self):
        return self.db.query(ServerList).order_by(ServerList.nombre).all()

    def get_by_id(self, id):
        return self.db.query(ServerList).filter(
            ServerList.id == id
        ).first()

    def update(self, id, nombre, descripcion):

        item = self.get_by_id(id)

        if not item:
            return None

        item.nombre = nombre
        item.descripcion = descripcion

        self.commit()

        return item

    def delete(self, id):

        item = self.get_by_id(id)

        if not item:
            return False

        self.db.delete(item)

        self.commit()

        return True
    
    def update(self, id, nombre, descripcion):

        item = self.get_by_id(id)

        if not item:
            return None

        item.nombre = nombre
        item.descripcion = descripcion

        self.commit()

        return item