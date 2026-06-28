from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPlainTextEdit,
    QLineEdit,
    QLabel
)
from PySide6.QtCore import QThread, Signal
import time


# ==========================
# THREAD LECTOR SSH
# ==========================
class SSHReader(QThread):
    output_received = Signal(str)

    def __init__(self, channel):
        super().__init__()
        self.channel = channel
        self.running = True

    def run(self):
        while self.running:
            try:
                if self.channel.recv_ready():
                    data = self.channel.recv(1024).decode(errors="ignore")
                    self.output_received.emit(data)
                time.sleep(0.1)
            except Exception:
                break

    def stop(self):
        self.running = False


# ==========================
# TERMINAL SSH UI
# ==========================
class SSHTerminal(QWidget):

    def __init__(self, ssh_client, parent=None):
        super().__init__(parent)

        self.ssh_client = ssh_client
        self.channel = None
        self.reader = None

        # historial
        self.history = []
        self.history_index = -1

        self.init_ui()
        self.start_shell()

    # --------------------------
    # UI
    # --------------------------
    def init_ui(self):
        layout = QVBoxLayout()

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Escribe un comando y presiona Enter")

        # estilos tipo terminal
        self.output.setStyleSheet("""
            background-color: black;
            color: #00ff00;
            font-family: Consolas;
            font-size: 13px;
        """)

        self.input.setStyleSheet("""
            background-color: black;
            color: #00ff00;
            font-family: Consolas;
            font-size: 14px;
        """)

        layout.addWidget(QLabel("Terminal SSH"))
        layout.addWidget(self.output)
        layout.addWidget(self.input)

        self.setLayout(layout)

        self.input.returnPressed.connect(self.send_command)

        # capturar teclas ↑ ↓
        self.input.keyPressEvent = self.handle_keypress

    # --------------------------
    # CONEXIÓN SHELL
    # --------------------------
    def start_shell(self):
        if not self.ssh_client.client:
            self.output.appendPlainText("❌ No hay conexión SSH activa")
            return

        self.channel = self.ssh_client.client.invoke_shell()

        self.reader = SSHReader(self.channel)
        self.reader.output_received.connect(self.append_output)
        self.reader.start()

    # --------------------------
    # ENVIAR COMANDO
    # --------------------------
    def send_command(self):
        cmd = self.input.text().strip()

        if not cmd:
            return

        # guardar historial
        self.history.append(cmd)
        self.history_index = len(self.history)

        # enviar al servidor
        if self.channel:
            self.channel.send(cmd + "\n")

        self.input.clear()

    # --------------------------
    # OUTPUT SSH
    # --------------------------
    def append_output(self, text):
        self.output.appendPlainText(text)

        # auto-scroll
        self.output.verticalScrollBar().setValue(
            self.output.verticalScrollBar().maximum()
        )

    # --------------------------
    # HISTORIAL TECLAS ↑ ↓
    # --------------------------
    def handle_keypress(self, event):
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QLineEdit

        if event.key() == Qt.Key_Up:
            if self.history:
                self.history_index = max(0, self.history_index - 1)
                self.input.setText(self.history[self.history_index])

        elif event.key() == Qt.Key_Down:
            if self.history:
                self.history_index += 1

                if self.history_index >= len(self.history):
                    self.history_index = len(self.history)
                    self.input.clear()
                else:
                    self.input.setText(self.history[self.history_index])

        else:
            QLineEdit.keyPressEvent(self.input, event)

    # --------------------------
    # CIERRE
    # --------------------------
    def closeEvent(self, event):
        if self.reader:
            self.reader.stop()
            self.reader.wait()

        if self.channel:
            self.channel.close()

        super().closeEvent(event)