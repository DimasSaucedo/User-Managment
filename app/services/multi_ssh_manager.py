import paramiko
from concurrent.futures import ThreadPoolExecutor, as_completed


class ServerConnection:
    """Credenciales + conexión para un servidor."""

    def __init__(self, server, username, password):
        self.server = server          # modelo Server (id, nombre, ip, puerto)
        self.username = username
        self.password = password
        self.client = None
        self.error = None

    def connect(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.server.ip,
                username=self.username,
                password=self.password,
                port=self.server.puerto,
                timeout=10
            )
            return True
        except Exception as e:
            self.error = str(e)
            return False

    def execute(self, command):
        if not self.client:
            raise Exception("Sin conexión")
        stdin, stdout, stderr = self.client.exec_command(command)
        return stdout.read().decode(), stderr.read().decode()

    def close(self):
        if self.client:
            self.client.close()
            self.client = None


class MultiSSHManager:
    """
    Gestiona múltiples ServerConnection.
    Permite consultar usuarios y modificar grupos en paralelo.
    """

    def __init__(self):
        # server_id -> ServerConnection
        self.connections: dict[int, ServerConnection] = {}

    def add_connection(self, server, username, password):
        self.connections[server.id] = ServerConnection(server, username, password)

    def remove_connection(self, server_id):
        conn = self.connections.pop(server_id, None)
        if conn:
            conn.close()

    def clear(self):
        for conn in self.connections.values():
            conn.close()
        self.connections.clear()

    # ------------------------------------------------------------------
    # CONECTAR TODOS EN PARALELO
    # Retorna dict: server_id -> {"ok": bool, "error": str|None}
    # ------------------------------------------------------------------
    def connect_all(self) -> dict:
        results = {}

        def _connect(server_id, conn):
            ok = conn.connect()
            return server_id, ok, conn.error

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = {
                pool.submit(_connect, sid, conn): sid
                for sid, conn in self.connections.items()
            }
            for future in as_completed(futures):
                sid, ok, err = future.result()
                results[sid] = {"ok": ok, "error": err}

        return results

    # ------------------------------------------------------------------
    # LISTAR USUARIOS EN TODOS LOS SERVIDORES CONECTADOS
    # Retorna lista de dicts con clave "server" añadida
    # ------------------------------------------------------------------
    def list_users_all(self) -> list[dict]:
        all_users = []

        def _list(server_id, conn):
            rows = []
            try:
                output, _ = conn.execute("cat /etc/passwd")
                for line in output.splitlines():
                    parts = line.split(":")
                    if len(parts) >= 7:
                        rows.append({
                            "server_id":   server_id,
                            "server_name": conn.server.nombre,
                            "username":    parts[0],
                            "uid":         parts[2],
                            "gid":         parts[3],
                            "home":        parts[5],
                            "shell":       parts[6],
                        })
            except Exception as e:
                rows.append({
                    "server_id":   server_id,
                    "server_name": conn.server.nombre,
                    "error":       str(e),
                })
            return rows

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = {
                pool.submit(_list, sid, conn): sid
                for sid, conn in self.connections.items()
                if conn.client is not None
            }
            for future in as_completed(futures):
                all_users.extend(future.result())

        return all_users

    # ------------------------------------------------------------------
    # OBTENER GRUPOS DE UN USUARIO EN UN SERVIDOR
    # ------------------------------------------------------------------
    def get_user_groups(self, server_id: int, username: str) -> list[str]:
        conn = self.connections.get(server_id)
        if not conn or not conn.client:
            return []
        try:
            output, _ = conn.execute(f"id {username}")
            if "groups=" in output:
                return output.split("groups=")[1].strip().split(",")
        except Exception:
            pass
        return []

    # ------------------------------------------------------------------
    # MODIFICAR GRUPOS EN PARALELO
    # targets: lista de {"server_id": int, "username": str}
    # groups:  lista de grupos a agregar
    # action:  "add" | "remove"
    # Retorna lista de {"server_name", "username", "group", "ok", "msg"}
    # ------------------------------------------------------------------
    def bulk_modify_groups(
        self,
        targets: list[dict],
        groups: list[str],
        action: str = "add"
    ) -> list[dict]:

        results = []

        def _modify(server_id, username, group):
            conn = self.connections.get(server_id)
            if not conn or not conn.client:
                return {
                    "server_name": str(server_id),
                    "username": username,
                    "group": group,
                    "ok": False,
                    "msg": "Sin conexión"
                }

            if action == "add":
                cmd = f"usermod -aG {group} {username}"
            else:
                cmd = f"gpasswd -d {username} {group}"

            try:
                _, err = conn.execute(cmd)
                ok = not bool(err.strip())
                return {
                    "server_name": conn.server.nombre,
                    "username": username,
                    "group": group,
                    "ok": ok,
                    "msg": err.strip() if err else "OK"
                }
            except Exception as e:
                return {
                    "server_name": conn.server.nombre,
                    "username": username,
                    "group": group,
                    "ok": False,
                    "msg": str(e)
                }

        tasks = [
            (t["server_id"], t["username"], g)
            for t in targets
            for g in groups
        ]

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(_modify, sid, user, grp) for sid, user, grp in tasks]
            for f in as_completed(futures):
                results.append(f.result())

        return results