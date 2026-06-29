"""
Maneja conexiones SSH a múltiples servidores en paralelo.
Soporta Linux y AIX.
"""
import paramiko
from concurrent.futures import ThreadPoolExecutor, as_completed


class ServerConnection:
    def __init__(self, server, username, password):
        self.server = server
        self.username = username
        self.password = password
        self.client = None
        self.error = None
        self.os_type = "linux"   # "linux" | "aix"

    def connect(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.server.ip,
                username=self.username,
                password=self.password,
                port=self.server.puerto,
                timeout=10,
            )
            self._detect_os()
            return True
        except Exception as e:
            self.error = str(e)
            return False

    def _detect_os(self):
        try:
            out, _ = self.execute("uname -s")
            self.os_type = "aix" if "AIX" in out else "linux"
        except Exception:
            self.os_type = "linux"

    def execute(self, command):
        if not self.client:
            raise Exception("Sin conexión")
        _, stdout, stderr = self.client.exec_command(command)
        return stdout.read().decode(errors="replace"), stderr.read().decode(errors="replace")

    def close(self):
        if self.client:
            self.client.close()
            self.client = None


class MultiSSHManager:
    def __init__(self):
        self.connections: dict[int, ServerConnection] = {}

    def add_connection(self, server, username, password):
        self.connections[server.id] = ServerConnection(server, username, password)

    def clear(self):
        for c in self.connections.values():
            c.close()
        self.connections.clear()

    # ── CONECTAR TODOS ──────────────────────────────────────────────
    def connect_all(self) -> dict:
        def _connect(sid, conn):
            ok = conn.connect()
            return sid, ok, conn.error

        results = {}
        with ThreadPoolExecutor(max_workers=10) as pool:
            for sid, ok, err in pool.map(
                lambda x: _connect(*x), self.connections.items()
            ):
                results[sid] = {"ok": ok, "error": err}
        return results

    # ── LISTAR USUARIOS + GRUPOS ─────────────────────────────────────
    def list_users_all(self) -> list[dict]:
        def _list(sid, conn):
            rows = []
            try:
                passwd_out, _ = conn.execute("cat /etc/passwd")
                usernames = []
                raw_rows = {}
                for line in passwd_out.splitlines():
                    p = line.split(":")
                    if len(p) < 7:
                        continue
                    raw_rows[p[0]] = {
                        "server_id": sid,
                        "server_name": conn.server.nombre,
                        "username": p[0],
                        "uid": p[2],
                        "gid": p[3],
                        "home": p[5],
                        "shell": p[6],
                        "groups": "",
                    }
                    usernames.append(p[0])

                # id en batch: un solo comando por servidor
                if usernames:
                    batch = " && ".join(f"id {u} 2>/dev/null" for u in usernames)
                    id_out, _ = conn.execute(batch)
                    for line in id_out.splitlines():
                        line = line.strip()
                        if not line or "uid=" not in line:
                            continue
                        # uid=1000(dimas) gid=1000(dimas) groups=...
                        try:
                            uname = line.split("(")[1].split(")")[0]
                            if "groups=" in line:
                                grp_part = line.split("groups=")[1]
                                groups = ",".join(
                                    g.split("(")[1].rstrip(")")
                                    for g in grp_part.split(",")
                                    if "(" in g
                                )
                                if uname in raw_rows:
                                    raw_rows[uname]["groups"] = groups
                        except (IndexError, KeyError):
                            pass

                rows = list(raw_rows.values())
            except Exception as e:
                rows = [{"server_id": sid, "server_name": conn.server.nombre, "error": str(e)}]
            return rows

        all_users = []
        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = {
                pool.submit(_list, sid, conn): sid
                for sid, conn in self.connections.items()
                if conn.client
            }
            for f in as_completed(futures):
                all_users.extend(f.result())
        return all_users

    # ── MODIFICAR GRUPOS CON EXPIRACIÓN OPCIONAL ────────────────────
    def bulk_modify_groups(
        self,
        targets: list[dict],
        groups: list[str],
        action: str = "add",           # "add" | "remove"
        expire_at: str | None = None,  # "YYYY-MM-DD HH:MM" o None
    ) -> list[dict]:

        results = []

        def _modify(sid, username, group):
            conn = self.connections.get(sid)
            if not conn or not conn.client:
                return {"server_name": str(sid), "username": username,
                        "group": group, "ok": False, "msg": "Sin conexión"}

            aix = conn.os_type == "aix"

            if action == "add":
                cmd = f"usermod -G {group} {username}" if aix else f"usermod -aG {group} {username}"
            else:
                cmd = f"rmgroup {username} {group}" if aix else f"gpasswd -d {username} {group}"

            try:
                _, err = conn.execute(cmd)
                ok = not bool(err.strip())

                # Programar remoción con 'at' si se pidió expiración
                if ok and action == "add" and expire_at:
                    if aix:
                        rm_cmd = f"rmgroup {username} {group}"
                    else:
                        rm_cmd = f"gpasswd -d {username} {group}"
                    # at acepta: echo "cmd" | at "HH:MM MM/DD/YYYY"
                    # expire_at formato: "YYYY-MM-DD HH:MM"
                    try:
                        dt_parts = expire_at.split(" ")
                        date_p = dt_parts[0].split("-")  # YYYY MM DD
                        time_p = dt_parts[1] if len(dt_parts) > 1 else "00:00"
                        at_time = f"{time_p} {date_p[1]}/{date_p[2]}/{date_p[0]}"
                        script = f"/tmp/.grp_{username}_{group}.sh"
                        script_content = (
                            "#!/bin/sh\n"
                            f"{rm_cmd}\n"
                            f"pkill -u {username}\n"
                            f"pkill -f 'sshd.*{username}'\n"
                            f"who | grep {username} | awk '{{print $2}}' | xargs -I{{}} pkill -t {{}}\n"
                            f"rm -f {script}\n"
                        )
                        sftp = conn.client.open_sftp()
                        with sftp.open(script, "w") as fh:
                            fh.write(script_content)
                        sftp.close()
                        conn.execute(f"chmod +x {script}")
                        at_out, at_err = conn.execute(f"echo '{script}' | at {at_time} 2>&1")
                        at_msg = (at_out + at_err).strip()
                        if "job" in at_msg.lower():
                            return {"server_name": conn.server.nombre, "username": username,
                                    "group": group, "ok": True,
                                    "msg": f"OK — expiración programada ({at_msg})"}
                        else:
                            return {"server_name": conn.server.nombre, "username": username,
                                    "group": group, "ok": True,
                                    "msg": f"Grupo agregado. Error at: {at_msg}"}
                    except Exception as ate:
                        return {"server_name": conn.server.nombre, "username": username,
                                "group": group, "ok": True,
                                "msg": f"Grupo agregado. Excepción at: {ate}"}

                return {"server_name": conn.server.nombre, "username": username,
                        "group": group, "ok": ok,
                        "msg": "OK" if ok else err.strip()}
            except Exception as e:
                return {"server_name": conn.server.nombre, "username": username,
                        "group": group, "ok": False, "msg": str(e)}

        tasks = [(t["server_id"], t["username"], g) for t in targets for g in groups]
        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(_modify, sid, usr, grp) for sid, usr, grp in tasks]
            for f in as_completed(futures):
                results.append(f.result())
        return results

    # ── CRUD USUARIOS ────────────────────────────────────────────────
    def bulk_create_user(self, targets_servers: list, user_data: dict) -> list[dict]:
        """
        targets_servers: lista de server_ids
        user_data: {username, password, uid(opt), gid(opt), home(opt), shell(opt), groups(opt)}
        """
        results = []

        def _create(sid):
            conn = self.connections.get(sid)
            if not conn or not conn.client:
                return {"server_name": str(sid), "action": "create",
                        "username": user_data["username"], "ok": False, "msg": "Sin conexión"}
            aix = conn.os_type == "aix"
            u = user_data
            try:
                if aix:
                    opts = f"-m {u['username']}"
                    if u.get("uid"):    opts = f"-u {u['uid']} " + opts
                    if u.get("gid"):    opts = f"-g {u['gid']} " + opts
                    if u.get("home"):   opts += f" -d {u['home']}"
                    if u.get("shell"):  opts += f" -s {u['shell']}"
                    cmd = f"mkuser {opts}"
                else:
                    opts = ""
                    if u.get("uid"):    opts += f" -u {u['uid']}"
                    if u.get("gid"):    opts += f" -g {u['gid']}"
                    if u.get("home"):   opts += f" -m -d {u['home']}"
                    if u.get("shell"):  opts += f" -s {u['shell']}"
                    cmd = f"useradd{opts} {u['username']}"

                _, err = conn.execute(cmd)
                ok = not bool(err.strip())
                if ok and u.get("password"):
                    conn.execute(f"echo '{u['username']}:{u['password']}' | chpasswd")
                if ok and u.get("groups"):
                    for g in u["groups"].split(","):
                        g = g.strip()
                        if g:
                            if aix:
                                conn.execute(f"usermod -G {g} {u['username']}")
                            else:
                                conn.execute(f"usermod -aG {g} {u['username']}")

                return {"server_name": conn.server.nombre, "action": "create",
                        "username": u["username"], "ok": ok,
                        "msg": "OK" if ok else err.strip()}
            except Exception as e:
                return {"server_name": conn.server.nombre, "action": "create",
                        "username": u["username"], "ok": False, "msg": str(e)}

        with ThreadPoolExecutor(max_workers=10) as pool:
            for r in pool.map(_create, targets_servers):
                results.append(r)
        return results

    def bulk_edit_user(self, targets: list[dict], changes: dict) -> list[dict]:
        """
        targets: [{"server_id": int, "username": str}]
        changes: {shell, home, password, lock(bool), unlock(bool)}
        """
        results = []

        def _edit(sid, username):
            conn = self.connections.get(sid)
            if not conn or not conn.client:
                return {"server_name": str(sid), "action": "edit",
                        "username": username, "ok": False, "msg": "Sin conexión"}
            aix = conn.os_type == "aix"
            try:
                cmds = []
                if changes.get("shell"):
                    cmds.append(f"chsh -s {changes['shell']} {username}" if not aix
                                else f"chuser shell={changes['shell']} {username}")
                if changes.get("home"):
                    cmds.append(f"usermod -d {changes['home']} {username}" if not aix
                                else f"chuser home={changes['home']} {username}")
                if changes.get("password"):
                    cmds.append(f"echo '{username}:{changes['password']}' | chpasswd")
                if changes.get("lock"):
                    cmds.append(f"passwd -l {username}")
                if changes.get("unlock"):
                    cmds.append(f"passwd -u {username}")

                errors = []
                for cmd in cmds:
                    _, err = conn.execute(cmd)
                    if err.strip():
                        errors.append(err.strip())

                ok = not bool(errors)
                return {"server_name": conn.server.nombre, "action": "edit",
                        "username": username, "ok": ok,
                        "msg": "OK" if ok else "; ".join(errors)}
            except Exception as e:
                return {"server_name": conn.server.nombre, "action": "edit",
                        "username": username, "ok": False, "msg": str(e)}

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(_edit, t["server_id"], t["username"]) for t in targets]
            for f in as_completed(futures):
                results.append(f.result())
        return results

    def bulk_delete_user(self, targets: list[dict], remove_home: bool = False) -> list[dict]:
        """
        targets: [{"server_id": int, "username": str}]
        """
        results = []

        def _delete(sid, username):
            conn = self.connections.get(sid)
            if not conn or not conn.client:
                return {"server_name": str(sid), "action": "delete",
                        "username": username, "ok": False, "msg": "Sin conexión"}
            aix = conn.os_type == "aix"
            try:
                if aix:
                    cmd = f"rmuser -p {username}"
                else:
                    cmd = f"userdel {'-r ' if remove_home else ''}{username}"
                _, err = conn.execute(cmd)
                ok = not bool(err.strip())
                return {"server_name": conn.server.nombre, "action": "delete",
                        "username": username, "ok": ok,
                        "msg": "OK" if ok else err.strip()}
            except Exception as e:
                return {"server_name": conn.server.nombre, "action": "delete",
                        "username": username, "ok": False, "msg": str(e)}

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(_delete, t["server_id"], t["username"]) for t in targets]
            for f in as_completed(futures):
                results.append(f.result())
        return results