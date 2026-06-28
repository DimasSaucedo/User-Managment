from app.repositories.server_repository import ServerRepository
from app.models.server import Server


class ServerController:

    def __init__(self):
        self.repo = ServerRepository()

    def list_servers(self):
        return self.repo.get_all()

    def create_server(self, data: dict):
        server = Server(**data)
        return self.repo.create(server)

    def delete_server(self, server_id: int):
        server = self.repo.get_by_id(server_id)

        if server:
            self.repo.delete(server)