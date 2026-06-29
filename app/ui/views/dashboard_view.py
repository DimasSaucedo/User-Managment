"""
Vista principal: tabla de servidores con estado de conexión en tiempo real.
- Conecta al iniciar usando credenciales guardadas en DB
- Permite editar cuenta/password por servidor
- Expone el MultiSSHManager global para que otras vistas lo reusen
"""
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QLineEdit, QDialog, QFormLayout, QDialogButtonBox, QAbstractItemView
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QColor, QFont

from app.database.database import SessionLocal
from app.database.models import Server
from app.services.multi_ssh_manager import MultiSSHManager


# ── Dialog editar credenciales ────────────────────────────────────────
class CredDialog(QDialog):
    def __init__(self, server, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Credenciales — {server.nombre}")
        self.setFixedWidth(340)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.user_edit = QLineEdit(server.ssh_username or "")
        self.pass_edit = QLineEdit(server.ssh_password or "")
        self.pass_edit.setEchoMode(QLineEdit.Password)
        form.addRow("Usuario:", self.user_edit)
        form.addRow("Password:", self.pass_edit)
        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get(self):
        return self.user_edit.text().strip(), self.pass_edit.text()


# ── Worker: conecta todos los servidores en background ───────────────
class ConnectWorker(QThread):
    server_result = Signal(int, bool, str)   # server_id, ok, error
    finished = Signal()

    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    def run(self):
        results = self.manager.connect_all()
        for sid, r in results.items():
            self.server_result.emit(sid, r["ok"], r.get("error") or "")
        self.finished.emit()


# ── Vista principal ───────────────────────────────────────────────────
class DashboardView(QWidget):
    """
    Vista de inicio. Mantiene el MultiSSHManager global.
    Otras vistas deben obtenerlo via get_manager().
    """

    COL_ID     = 0
    COL_NOMBRE = 1
    COL_IP     = 2
    COL_PUERTO = 3
    COL_USUARIO= 4
    COL_ESTADO = 5
    COL_ULTIMA = 6

    def __init__(self):
        super().__init__()
        self.manager = MultiSSHManager()
        self._server_rows: dict[int, int] = {}   # server_id → row
        self._build_ui()
        # Conectar al iniciar con pequeño delay para que la UI esté visible
        QTimer.singleShot(500, self._connect_all)

    def get_manager(self) -> MultiSSHManager:
        return self.manager

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("Dashboard — Servidores")
        title.setFont(QFont("", 14, QFont.Bold))
        self.btn_reconectar = QPushButton("↺ Reconectar todos")
        self.btn_creds      = QPushButton("✏️ Editar credenciales")
        self.btn_reconectar.clicked.connect(self._connect_all)
        self.btn_creds.clicked.connect(self._edit_creds)
        hdr.addWidget(title); hdr.addStretch()
        hdr.addWidget(self.btn_creds)
        hdr.addWidget(self.btn_reconectar)
        layout.addLayout(hdr)

        self.status_label = QLabel("Iniciando conexiones…")
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)

        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nombre", "IP", "Puerto", "Usuario SSH", "Estado", "Última conexión"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(self.COL_NOMBRE, QHeaderView.Stretch)
        layout.addWidget(self.table)

        # Leyenda
        leg = QHBoxLayout()
        for color, txt in [("#a6e3a1", "Conectado"), ("#f38ba8", "Error"), ("#cdd6f4", "Sin credenciales")]:
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 16px;")
            leg.addWidget(dot)
            leg.addWidget(QLabel(txt))
            leg.addSpacing(12)
        leg.addStretch()
        layout.addLayout(leg)

    # ── Cargar servidores desde DB ────────────────────────────────────
    def _load_servers(self) -> list:
        session = SessionLocal()
        servers = session.query(Server).filter_by(activo=True).order_by(Server.id).all()
        session.close()
        return servers

    def _render_servers(self, servers: list):
        self.table.setRowCount(0)
        self._server_rows.clear()
        for server in servers:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self._server_rows[server.id] = row

            self.table.setItem(row, self.COL_ID,     QTableWidgetItem(str(server.id)))
            self.table.setItem(row, self.COL_NOMBRE, QTableWidgetItem(server.nombre))
            self.table.setItem(row, self.COL_IP,     QTableWidgetItem(server.ip))
            self.table.setItem(row, self.COL_PUERTO, QTableWidgetItem(str(server.puerto)))
            self.table.setItem(row, self.COL_USUARIO,QTableWidgetItem(server.ssh_username or "—"))

            if not server.ssh_username:
                self._set_status(row, "Sin credenciales", "#cdd6f4")
            else:
                self._set_status(row, "Conectando…", "#fab387")

            ultima = server.ultima_conexion.strftime("%Y-%m-%d %H:%M") if server.ultima_conexion else "—"
            self.table.setItem(row, self.COL_ULTIMA, QTableWidgetItem(ultima))

    def _set_status(self, row: int, text: str, color: str):
        item = QTableWidgetItem(text)
        item.setForeground(QColor(color))
        item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, self.COL_ESTADO, item)

    # ── Conectar ──────────────────────────────────────────────────────
    def _connect_all(self):
        servers = self._load_servers()
        self._render_servers(servers)

        self.manager.clear()
        for s in servers:
            if s.ssh_username and s.ssh_password:
                self.manager.add_connection(s, s.ssh_username, s.ssh_password)

        if not self.manager.connections:
            self.status_label.setText("Ningún servidor tiene credenciales configuradas.")
            return

        self.status_label.setText("Conectando…")
        self.btn_reconectar.setEnabled(False)

        self.worker = ConnectWorker(self.manager)
        self.worker.server_result.connect(self._on_server_result)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_server_result(self, server_id: int, ok: bool, error: str):
        row = self._server_rows.get(server_id)
        if row is None:
            return

        if ok:
            self._set_status(row, "● Conectado", "#a6e3a1")
            # Actualizar ultima_conexion en DB
            session = SessionLocal()
            srv = session.query(Server).filter_by(id=server_id).first()
            if srv:
                srv.ultima_conexion = datetime.now()
                session.commit()
            session.close()
            # Refrescar columna
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.table.setItem(row, self.COL_ULTIMA, QTableWidgetItem(now))
        else:
            self._set_status(row, f"✗ {error[:40]}", "#f38ba8")

    def _on_finished(self):
        ok = sum(
            1 for conn in self.manager.connections.values() if conn.client
        )
        total = len(self.manager.connections)
        self.status_label.setText(f"{ok}/{total} servidores conectados.")
        self.btn_reconectar.setEnabled(True)

    # ── Editar credenciales ───────────────────────────────────────────
    def _edit_creds(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Selección", "Selecciona un servidor.")
            return

        server_id = int(self.table.item(row, self.COL_ID).text())
        session = SessionLocal()
        server = session.query(Server).filter_by(id=server_id).first()

        dlg = CredDialog(server, self)
        if dlg.exec():
            user, pwd = dlg.get()
            server.ssh_username = user
            server.ssh_password = pwd
            session.commit()
            # Refrescar fila
            self.table.setItem(row, self.COL_USUARIO, QTableWidgetItem(user or "—"))
            self._set_status(row, "Reconectando…", "#fab387")

            # Reconectar solo ese servidor
            session2 = SessionLocal()
            srv2 = session2.query(Server).filter_by(id=server_id).first()
            session2.close()
            old = self.manager.connections.pop(server_id, None)
            if old:
                old.close()
            if user and pwd:
                self.manager.add_connection(srv2, user, pwd)
                # Conectar en background
                import threading
                def _reconect():
                    conn = self.manager.connections.get(server_id)
                    if conn:
                        ok = conn.connect()
                        self._on_server_result(server_id, ok, conn.error or "")
                threading.Thread(target=_reconect, daemon=True).start()

        session.close()