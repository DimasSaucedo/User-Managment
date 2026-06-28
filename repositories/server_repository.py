from database.models import Server
from repositories.base_repository import BaseRepository


class ServerRepository(BaseRepository):

    def create(
        self,
        list_id,
        nombre,
        hostname,
        ip,
        puerto=22,
        descripcion=None
    ):

        server = Server(
            list_id=list_id,
            nombre=nombre,
            hostname=hostname,
            ip=ip,
            puerto=puerto,
            descripcion=descripcion
        )

        self.db.add(server)
        self.commit()

        return server

    def get_all(self):
        return self.db.query(Server).order_by(Server.nombre).all()

    def get_by_id(self, server_id):
        return self.db.query(Server).filter(
            Server.id == server_id
        ).first()

    def get_by_list(self, list_id):
        return (
            self.db.query(Server)
            .filter(Server.list_id == list_id)
            .order_by(Server.nombre)
            .all()
        )

    def update(
        self,
        server_id,
        nombre,
        hostname,
        ip,
        puerto,
        descripcion,
        activo
    ):

        server = self.get_by_id(server_id)

        if not server:
            return None

        server.nombre = nombre
        server.hostname = hostname
        server.ip = ip
        server.puerto = puerto
        server.descripcion = descripcion
        server.activo = activo

        self.commit()

        return server

    def update_os(self, server_id, sistema):

        server = self.get_by_id(server_id)

        if not server:
            return None

        server.sistema = sistema

        self.commit()

        return server

    def update_last_connection(self, server_id, fecha):

        server = self.get_by_id(server_id)

        if not server:
            return None

        server.ultima_conexion = fecha

        self.commit()

        return server

    def delete(self, server_id):

        server = self.get_by_id(server_id)

        if not server:
            return False

        self.db.delete(server)
        self.commit()

        return True