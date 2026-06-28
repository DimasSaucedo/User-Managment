import paramiko


class SSHClient:

    def __init__(self):
        self.client = None

    def connect(self, hostname, username, password, port=22):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        self.client.connect(
            hostname=hostname,
            username=username,
            password=password,
            port=port,
            timeout=10
        )

    def execute(self, command):
        if not self.client:
            raise Exception("No hay conexión SSH activa")

        stdin, stdout, stderr = self.client.exec_command(command)

        output = stdout.read().decode()
        error = stderr.read().decode()

        return output, error

    def close(self):
        if self.client:
            self.client.close()
            self.client = None