import paramiko

from app.services.audit_service import AuditService

class SSHService:

    def __init__(self):
        self.client = None
        self.is_connected = False

    # -------------------------
    # CONEXIÓN
    # -------------------------
    def connect(self, host, user, password, port=22):
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            self.client.connect(
                hostname=host,
                username=user,
                password=password,
                port=port,
                timeout=10
            )

            self.is_connected = True

        except Exception as e:
            self.is_connected = False
            raise Exception(f"Error SSH connect: {str(e)}")

    # -------------------------
    # EJECUTAR COMANDO
    # -------------------------
    def execute(self, command, audit=False, server=None):
        try:
            stdin, stdout, stderr = self.client.exec_command(command)

            output = stdout.read().decode()
            error = stderr.read().decode()

            if audit:
                AuditService().log_success(
                    action="SSH_EXEC",
                    message=command,
                    server=server
                )

            if error:
                if audit:
                    AuditService().log_error(
                        action="SSH_EXEC_ERROR",
                        message=error,
                        server=server
                    )

            return output, error

        except Exception as e:
            if audit:
                AuditService().log_error(
                    action="SSH_EXEC_EXCEPTION",
                    message=str(e),
                    server=server
                )
            raise e

    # -------------------------
    # SHELL INTERACTIVO
    # -------------------------
    def shell(self):
        if not self.client or not self.is_connected:
            raise Exception("SSH no conectado")

        return self.client.invoke_shell()

    # -------------------------
    # VERIFICAR ESTADO
    # -------------------------
    def is_alive(self):
        if not self.client:
            return False

        transport = self.client.get_transport()
        return transport is not None and transport.is_active()

    # -------------------------
    # CERRAR CONEXIÓN
    # -------------------------
    def close(self):
        if self.client:
            self.client.close()

        self.client = None
        self.is_connected = False