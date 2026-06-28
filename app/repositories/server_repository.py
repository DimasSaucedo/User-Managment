from app.database.database import SessionLocal
from app.models.server import Server


class ServerRepository:

    def __init__(self):
        self.db = SessionLocal()

    def get_all(self):
        return self.db.query(Server).all()

    def get_by_id(self, server_id: int):
        return self.db.query(Server).filter(Server.id == server_id).first()

    def create(self, server: Server):
        self.db.add(server)
        self.db.commit()
        self.db.refresh(server)
        return server

    def delete(self, server: Server):
        self.db.delete(server)
        self.db.commit()

    def update(self):
        self.db.commit()