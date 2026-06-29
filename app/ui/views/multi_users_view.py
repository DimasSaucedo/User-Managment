from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QLineEdit, QAbstractItemView
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont

from app.database.database import SessionLocal
from app.database.models import Server
from app.services.multi_ssh_manager import MultiSSHManager
from app.dialogs.server_selector_dialog import ServerSelectorDialog
from app.dialogs.bulk_group_dialog import BulkGroupDialog
from app.dialogs.bulk_user_dialog import BulkUserDialog


class FetchWorker(QThread):
    status = Signal(str)
    users_ready = Signal(list)
    connect_results = Signal(dict)

    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    def run(self):
        self.status.emit("Conectando servidores…")
        results = self.manager.connect_all()
        self.connect_results.emit(results)
        ok = sum(1 for r in results.values() if r["ok"])
        self.status.emit(f"Conectados {ok}/{len(results)} — obteniendo usuarios y grupos…")
        users = self.manager.list_users_all()
        self.users_ready.emit(users)


class MultiUsersView(QWidget):

    COL_SERVER  = 0
    COL_USER    = 1
    COL_UID     = 2
    COL_GID     = 3
    COL_HOME    = 4
    COL_SHELL   = 5
    COL_GROUPS  = 6

    def __init__(self):
        super().__init__()
        self.manager = MultiSSHManager()
        self.all_users: list[dict] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("Usuarios — Multi-Servidor")
        title.setFont(QFont("", 14, QFont.Bold))
        self.btn_connect = QPushButton("Seleccionar Servidores…")
        self.btn_refresh = QPushButton("↺ Recargar")
        self.btn_refresh.setEnabled(False)
        hdr.addWidget(title); hdr.addStretch()
        hdr.addWidget(self.btn_connect); hdr.addWidget(self.btn_refresh)
        layout.addLayout(hdr)

        self.status_label = QLabel("Sin conexión.")
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)

        # Filtro
        fr = QHBoxLayout()
        fr.addWidget(QLabel("Filtrar:"))
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("usuario, servidor, grupo, shell…")
        self.filter_edit.textChanged.connect(self._apply_filter)
        fr.addWidget(self.filter_edit)
        layout.addLayout(fr)

        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Servidor", "Usuario", "UID", "GID", "Home", "Shell", "Grupos"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(True)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(self.COL_GROUPS, QHeaderView.Stretch)
        layout.addWidget(self.table)

        # Acciones
        act = QHBoxLayout()
        self.lbl_sel = QLabel("0 seleccionado(s)")
        self.btn_modify_groups = QPushButton("Modificar Grupos…")
        self.btn_manage_users  = QPushButton("Gestionar Usuarios…")
        self.btn_modify_groups.setEnabled(False)
        act.addWidget(self.lbl_sel); act.addStretch()
        act.addWidget(self.btn_modify_groups)
        act.addWidget(self.btn_manage_users)
        layout.addLayout(act)

        # Señales
        self.btn_connect.clicked.connect(self._open_server_selector)
        self.btn_refresh.clicked.connect(self._fetch_users)
        self.btn_modify_groups.clicked.connect(self._open_bulk_groups)
        self.btn_manage_users.clicked.connect(self._open_manage_users)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

    # ── Conectar ──────────────────────────────────────────────────────
    def _open_server_selector(self):
        session = SessionLocal()
        servers = session.query(Server).filter_by(activo=True).all()
        session.close()
        if not servers:
            QMessageBox.warning(self, "Sin servidores", "No hay servidores registrados.")
            return
        dlg = ServerSelectorDialog(servers, self)
        if dlg.exec():
            selected = dlg.get_selected()
            if not selected:
                QMessageBox.warning(self, "Vacío", "Sin servidores con credenciales.")
                return
            self.manager.clear()
            for s in selected:
                self.manager.add_connection(s["server"], s["username"], s["password"])
            self._fetch_users()

    # ── Fetch ─────────────────────────────────────────────────────────
    def _fetch_users(self):
        self.table.setRowCount(0); self.all_users = []
        self.status_label.setText("Conectando…")
        self.btn_refresh.setEnabled(False); self.btn_connect.setEnabled(False)
        self.worker = FetchWorker(self.manager)
        self.worker.status.connect(self.status_label.setText)
        self.worker.connect_results.connect(self._show_connect_errors)
        self.worker.users_ready.connect(self._populate_table)
        self.worker.start()

    def _show_connect_errors(self, results):
        failed = [r["error"] for r in results.values() if not r["ok"]]
        if failed:
            QMessageBox.warning(self, "Errores de conexión", "\n".join(failed))

    def _populate_table(self, users):
        self.all_users = users
        self._render_table(users)
        self.btn_refresh.setEnabled(True); self.btn_connect.setEnabled(True)
        self.status_label.setText(
            f"{len(users)} usuario(s) — {len(self.manager.connections)} servidor(es)."
        )

    def _render_table(self, users):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(users))
        for row, u in enumerate(users):
            if "error" in u:
                item = QTableWidgetItem(u["server_name"])
                item.setForeground(QColor("#f38ba8"))
                item.setData(Qt.UserRole, u["server_id"])
                self.table.setItem(row, 0, item)
                self.table.setItem(row, 1, QTableWidgetItem(f"ERROR: {u['error']}"))
                continue
            srv = QTableWidgetItem(u["server_name"])
            srv.setData(Qt.UserRole, u["server_id"])
            self.table.setItem(row, self.COL_SERVER, srv)
            self.table.setItem(row, self.COL_USER,   QTableWidgetItem(u["username"]))
            self.table.setItem(row, self.COL_UID,    QTableWidgetItem(u["uid"]))
            self.table.setItem(row, self.COL_GID,    QTableWidgetItem(u["gid"]))
            self.table.setItem(row, self.COL_HOME,   QTableWidgetItem(u["home"]))
            self.table.setItem(row, self.COL_SHELL,  QTableWidgetItem(u["shell"]))
            self.table.setItem(row, self.COL_GROUPS, QTableWidgetItem(u.get("groups", "")))
        self.table.setSortingEnabled(True)

    # ── Filtro ────────────────────────────────────────────────────────
    def _apply_filter(self, text):
        text = text.lower()
        filtered = self.all_users if not text else [
            u for u in self.all_users
            if any(text in str(v).lower() for v in u.values())
        ]
        self._render_table(filtered)

    # ── Selección ─────────────────────────────────────────────────────
    def _on_selection_changed(self):
        count = len(self._selected_targets())
        self.lbl_sel.setText(f"{count} seleccionado(s)")
        self.btn_modify_groups.setEnabled(count > 0)

    def _selected_targets(self) -> list[dict]:
        seen, targets = set(), []
        for idx in self.table.selectedIndexes():
            if idx.column() != 0:
                continue
            row = idx.row()
            srv_item = self.table.item(row, 0)
            usr_item = self.table.item(row, 1)
            if not srv_item or not usr_item:
                continue
            sid  = srv_item.data(Qt.UserRole)
            user = usr_item.text()
            if (sid, user) not in seen:
                seen.add((sid, user))
                targets.append({
                    "server_id":   sid,
                    "server_name": srv_item.text(),
                    "username":    user,
                })
        return targets

    def _connected_servers(self) -> list[dict]:
        return [
            {"server_id": sid, "server_name": conn.server.nombre}
            for sid, conn in self.manager.connections.items()
            if conn.client
        ]

    # ── Dialogs ───────────────────────────────────────────────────────
    def _open_bulk_groups(self):
        targets = self._selected_targets()
        if targets:
            BulkGroupDialog(self.manager, targets, self).exec()

    def _open_manage_users(self):
        dlg = BulkUserDialog(
            self.manager,
            self._connected_servers(),
            self._selected_targets(),
            self
        )
        dlg.exec()