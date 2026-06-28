from app.services.system_service import SystemService


class UsersController:

    def __init__(self, ssh_service):
        self.system = SystemService(ssh_service)

    def get_users(self, server=None):
        return self.system.list_users(server)

    def get_groups(self, user, server=None):
        return self.system.get_user_groups(user, server)

    def add_to_group(self, user, group, server=None):
        return self.system.add_user_to_group(user, group, server)

    def delete_user(self, user, server=None):
        return self.system.delete_user(user, server)