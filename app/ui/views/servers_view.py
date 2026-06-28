from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox
)

from app.dialogs.server_dialog import ServerDialog
from app.database.database import SessionLocal
from app.database.models import Server
from app.services.ssh_client import SSHClient
from app.dialogs.ssh_dialog import SSHDialog
from app.widgets.ssh_terminal import SSHTerminal

class ServersView(QWidget):

    def __init__(self):
        super().__init__()

        self.session = SessionLocal()

        self.init_ui()
        self.load_servers()
        self.ssh = SSHClient()
        self.terminal = None

    def init_ui(self):
        layout = QVBoxLayout()

        # Botones superiores
        botones_layout = QHBoxLayout()

        self.btn_agregar = QPushButton("Agregar")
        self.btn_editar = QPushButton("Editar")
        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_recargar = QPushButton("Recargar")

        botones_layout.addWidget(self.btn_agregar)
        botones_layout.addWidget(self.btn_editar)
        botones_layout.addWidget(self.btn_eliminar)
        botones_layout.addWidget(self.btn_recargar)

        layout.addLayout(botones_layout)
        
        self.btn_conectar = QPushButton("Conectar SSH")
        botones_layout.addWidget(self.btn_conectar)

        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nombre", "Hostname", "IP", "Puerto"
        ])

        layout.addWidget(self.table)

        self.setLayout(layout)

        # Eventos
        self.btn_agregar.clicked.connect(self.add_server)
        self.btn_editar.clicked.connect(self.edit_server)
        self.btn_eliminar.clicked.connect(self.delete_server)
        self.btn_recargar.clicked.connect(self.load_servers)
        self.btn_conectar.clicked.connect(self.connect_ssh)

    def load_servers(self):
        self.table.setRowCount(0)

        servers = self.session.query(Server).all()

        for row, server in enumerate(servers):
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(str(server.id)))
            self.table.setItem(row, 1, QTableWidgetItem(server.nombre))
            self.table.setItem(row, 2, QTableWidgetItem(server.hostname))
            self.table.setItem(row, 3, QTableWidgetItem(server.ip))
            self.table.setItem(row, 4, QTableWidgetItem(str(server.puerto)))

    def add_server(self):
        dialog = ServerDialog(self)

        if dialog.exec():
            server = Server(
                nombre=dialog.nombre.text(),
                hostname=dialog.hostname.text(),
                ip=dialog.ip.text(),
                puerto=dialog.puerto.value(),
                descripcion=dialog.descripcion.toPlainText()
            )

            self.session.add(server)
            self.session.commit()
            self.load_servers()

    def get_selected_server(self):
        selected = self.table.currentRow()

        if selected < 0:
            return None

        server_id = int(self.table.item(selected, 0).text())

        return self.session.query(Server).filter_by(id=server_id).first()

    def edit_server(self):
        server = self.get_selected_server()

        if not server:
            QMessageBox.warning(self, "Error", "Selecciona un servidor")
            return

        dialog = ServerDialog(self)

        # Cargar datos
        dialog.nombre.setText(server.nombre)
        dialog.hostname.setText(server.hostname)
        dialog.ip.setText(server.ip)
        dialog.puerto.setValue(server.puerto)
        dialog.descripcion.setPlainText(server.descripcion or "")

        if dialog.exec():
            server.nombre = dialog.nombre.text()
            server.hostname = dialog.hostname.text()
            server.ip = dialog.ip.text()
            server.puerto = dialog.puerto.value()
            server.descripcion = dialog.descripcion.toPlainText()

            self.session.commit()
            self.load_servers()

    def delete_server(self):
        server = self.get_selected_server()

        if not server:
            QMessageBox.warning(self, "Error", "Selecciona un servidor")
            return

        confirm = QMessageBox.question(
            self,
            "Confirmar",
            "¿Eliminar este servidor?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            self.session.delete(server)
            self.session.commit()
            self.load_servers()
            
    def connect_ssh(self):
        server = self.get_selected_server()

        if not server:
            QMessageBox.warning(self, "Error", "Selecciona un servidor")
            return

        dialog = SSHDialog(self)

        if dialog.exec():

            try:
                self.ssh.connect(
                    hostname=server.ip,
                    username=dialog.usuario.text(),
                    password=dialog.password.text(),
                    port=dialog.port.value()
                )

                QMessageBox.information(
                    self,
                    "Éxito",
                    "Conexión SSH establecida"
                )

                # 🔥 abrir terminal
                self.open_terminal()

            except Exception as e:
                QMessageBox.critical(self, "Error SSH", str(e))
                
    def run_command(self, command):
        try:
            output, error = self.ssh.execute(command)

            if error:
                QMessageBox.warning(self, "Error", error)
            else:
                QMessageBox.information(self, "Salida", output)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            
    def open_terminal(self):
        if self.terminal:
            self.terminal.setParent(None)

        self.terminal = SSHTerminal(self.ssh)

        # abrir como ventana flotante (simple)
        self.terminal.setWindowTitle("Terminal SSH")
        self.terminal.resize(700, 500)
        self.terminal.show()