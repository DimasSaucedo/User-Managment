from app.services.audit_service import AuditService


class SystemService:

    def __init__(self, ssh_service):
        self.ssh = ssh_service
        self.audit = AuditService()

    # =========================
    # LISTAR USUARIOS
    # =========================
    def list_users(self, server=None):

        try:
            output, error = self.ssh.execute(
                "cat /etc/passwd",
                audit=True,
                server=server
            )

            if error:
                return []

            users = []

            for line in output.splitlines():
                parts = line.split(":")
                if len(parts) >= 7:
                    users.append({
                        "username": parts[0],
                        "uid": parts[2],
                        "gid": parts[3],
                        "home": parts[5],
                        "shell": parts[6]
                    })

            self.audit.log_success(
                action="USER_LIST",
                message="Listado de usuarios obtenido",
                server=server
            )

            return users

        except Exception as e:
            self.audit.log_error(
                action="USER_LIST_ERROR",
                message=str(e),
                server=server
            )
            return []

    # =========================
    # GRUPOS DE USUARIO
    # =========================
    def get_user_groups(self, user, server=None):

        try:
            output, error = self.ssh.execute(
                f"id {user}",
                audit=True,
                server=server
            )

            if error:
                return []

            # uid=1000(user) gid=1000(user) groups=...
            if "groups=" in output:
                groups_part = output.split("groups=")[1]
                groups = groups_part.strip().split(",")

                self.audit.log_success(
                    action="USER_GROUPS",
                    message=f"Grupos obtenidos para {user}",
                    entity=user,
                    server=server
                )

                return groups

            return []

        except Exception as e:
            self.audit.log_error(
                action="USER_GROUPS_ERROR",
                message=str(e),
                entity=user,
                server=server
            )
            return []

    # =========================
    # AGREGAR A GRUPO
    # =========================
    def add_user_to_group(self, user, group, server=None):

        command = f"usermod -aG {group} {user}"

        try:
            output, error = self.ssh.execute(
                command,
                audit=True,
                server=server
            )

            if error:
                return False, error

            self.audit.log_success(
                action="USER_ADD_GROUP",
                message=command,
                entity=user,
                server=server
            )

            return True, output

        except Exception as e:
            self.audit.log_error(
                action="USER_ADD_GROUP_ERROR",
                message=str(e),
                entity=user,
                server=server
            )
            return False, str(e)

    # =========================
    # ELIMINAR USUARIO
    # =========================
    def delete_user(self, user, server=None):

        command = f"userdel {user}"

        try:
            output, error = self.ssh.execute(
                command,
                audit=True,
                server=server
            )

            if error:
                return False, error

            self.audit.log_success(
                action="USER_DELETE",
                message=command,
                entity=user,
                server=server
            )

            return True, output

        except Exception as e:
            self.audit.log_error(
                action="USER_DELETE_ERROR",
                message=str(e),
                entity=user,
                server=server
            )
            return False, str(e)