from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QLineEdit, QFrame, QSplitter, QAbstractItemView
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont

from app.database.database import SessionLocal
from app.database.models import Server
from app.services.multi_ssh_manager import MultiSSHManager
from app.dialogs.server_selector_dialog import ServerSelectorDialog
from app.dialogs.bulk_group_dialog import BulkGroupDialog


# ------------------------------------------------------------------
# Worker: conecta y lista usuarios en background
# ------------------------------------------------------------------
class FetchWorker(QThread):
    status = Signal(str)          # mensajes de estado
    users_ready = Signal(list)    # resultado final
    connect_results = Signal(dict)

    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    def run(self):
        self.status.emit("Conectando servidores...")
        results = self.manager.connect_all()
        self.connect_results.emit(results)

        ok_count = sum(1 for r in results.values() if r["ok"])
        self.status.emit(f"Conectados {ok_count}/{len(results)} — obteniendo usuarios...")

        users = self.manager.list_users_all()
        self.users_ready.emit(users)


# ------------------------------------------------------------------
# Vista principal
# ------------------------------------------------------------------
class MultiUsersView(QWidget):

    def __init__(self):
        super().__init__()
        self.manager = MultiSSHManager()
        self.all_users: list[dict] = []   # cache completo
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        # --- Header ---
        header = QHBoxLayout()
        title = QLabel("Usuarios — Multi-Servidor")
        title.setFont(QFont("", 14, QFont.Bold))

        self.btn_connect = QPushButton("Seleccionar Servidores…")
        self.btn_refresh = QPushButton("↺ Recargar")
        self.btn_refresh.setEnabled(False)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.btn_connect)
        header.addWidget(self.btn_refresh)
        layout.addLayout(header)

        # --- Barra de estado ---
        self.status_label = QLabel("Sin conexión. Haz clic en 'Seleccionar Servidores'.")
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)

        # --- Filtro rápido ---
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Filtrar:"))
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("usuario, servidor, shell…")
        self.filter_edit.textChanged.connect(self._apply_filter)
        filter_row.addWidget(self.filter_edit)
        layout.addLayout(filter_row)

        # --- Tabla de usuarios ---
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Servidor", "Usuario", "UID", "GID", "Home", "Shell"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

        # --- Acciones ---
        actions = QHBoxLayout()
        self.lbl_selection = QLabel("0 seleccionado(s)")
        self.btn_groups = QPushButton("Ver Grupos")
        self.btn_modify = QPushButton("Modificar Grupos…")
        self.btn_modify.setEnabled(False)
        self.btn_groups.setEnabled(False)

        actions.addWidget(self.lbl_selection)
        actions.addStretch()
        actions.addWidget(self.btn_groups)
        actions.addWidget(self.btn_modify)
        layout.addLayout(actions)

        # --- Señales ---
        self.btn_connect.clicked.connect(self._open_server_selector)
        self.btn_refresh.clicked.connect(self._fetch_users)
        self.btn_modify.clicked.connect(self._open_bulk_groups)
        self.btn_groups.clicked.connect(self._show_groups)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

    # ------------------------------------------------------------------
    # SELECCIONAR SERVIDORES Y CONECTAR
    # ------------------------------------------------------------------
    def _open_server_selector(self):
        session = SessionLocal()
        servers = session.query(Server).filter_by(activo=True).all()
        session.close()

        if not servers:
            QMessageBox.warning(self, "Sin servidores", "No hay servidores registrados.")
            return

        dialog = ServerSelectorDialog(servers, self)
        if dialog.exec():
            selected = dialog.get_selected()
            if not selected:
                QMessageBox.warning(self, "Vacío", "No seleccionaste ningún servidor con usuario.")
                return

            self.manager.clear()
            for s in selected:
                self.manager.add_connection(s["server"], s["username"], s["password"])

            self._fetch_users()

    # ------------------------------------------------------------------
    # OBTENER USUARIOS (background)
    # ------------------------------------------------------------------
    def _fetch_users(self):
        self.table.setRowCount(0)
        self.all_users = []
        self.status_label.setText("Conectando…")
        self.btn_refresh.setEnabled(False)
        self.btn_connect.setEnabled(False)

        self.worker = FetchWorker(self.manager)
        self.worker.status.connect(self.status_label.setText)
        self.worker.connect_results.connect(self._show_connect_results)
        self.worker.users_ready.connect(self._populate_table)
        self.worker.start()

    def _show_connect_results(self, results):
        failed = [(sid, r["error"]) for sid, r in results.items() if not r["ok"]]
        if failed:
            msgs = "\n".join(f"  • Servidor {sid}: {err}" for sid, err in failed)
            QMessageBox.warning(self, "Errores de conexión", f"No se pudo conectar a:\n{msgs}")

    def _populate_table(self, users: list[dict]):
        self.all_users = users
        self._render_table(users)
        self.btn_refresh.setEnabled(True)
        self.btn_connect.setEnabled(True)
        self.status_label.setText(
            f"{len(users)} usuario(s) en {len(self.manager.connections)} servidor(es)."
        )

    def _render_table(self, users: list[dict]):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(users))

        for row, u in enumerate(users):
            if "error" in u:
                item = QTableWidgetItem(u["server_name"])
                item.setForeground(QColor("#f38ba8"))
                self.table.setItem(row, 0, item)
                err_item = QTableWidgetItem(f"ERROR: {u['error']}")
                err_item.setForeground(QColor("#f38ba8"))
                self.table.setItem(row, 1, err_item)
                # guardar server_id en data del item para selección
                item.setData(Qt.UserRole, u["server_id"])
                continue

            srv_item = QTableWidgetItem(u["server_name"])
            srv_item.setData(Qt.UserRole, u["server_id"])
            self.table.setItem(row, 0, srv_item)
            self.table.setItem(row, 1, QTableWidgetItem(u["username"]))
            self.table.setItem(row, 2, QTableWidgetItem(u["uid"]))
            self.table.setItem(row, 3, QTableWidgetItem(u["gid"]))
            self.table.setItem(row, 4, QTableWidgetItem(u["home"]))
            self.table.setItem(row, 5, QTableWidgetItem(u["shell"]))

        self.table.setSortingEnabled(True)

    # ------------------------------------------------------------------
    # FILTRO
    # ------------------------------------------------------------------
    def _apply_filter(self, text: str):
        text = text.lower()
        if not text:
            self._render_table(self.all_users)
            return

        filtered = [
            u for u in self.all_users
            if any(text in str(v).lower() for v in u.values())
        ]
        self._render_table(filtered)

    # ------------------------------------------------------------------
    # SELECCIÓN
    # ------------------------------------------------------------------
    def _on_selection_changed(self):
        rows = self._selected_rows()
        count = len(rows)
        self.lbl_selection.setText(f"{count} seleccionado(s)")
        self.btn_modify.setEnabled(count > 0)
        self.btn_groups.setEnabled(count == 1)

    def _selected_rows(self) -> list[dict]:
        """Retorna targets únicos de las filas seleccionadas."""
        seen = set()
        targets = []
        for idx in self.table.selectedIndexes():
            if idx.column() != 0:
                continue
            row = idx.row()
            srv_item = self.table.item(row, 0)
            usr_item = self.table.item(row, 1)
            if not srv_item or not usr_item:
                continue
            server_id = srv_item.data(Qt.UserRole)
            username = usr_item.text()
            key = (server_id, username)
            if key not in seen:
                seen.add(key)
                targets.append({
                    "server_id":   server_id,
                    "server_name": srv_item.text(),
                    "username":    username
                })
        return targets

    # ------------------------------------------------------------------
    # VER GRUPOS (1 usuario)
    # ------------------------------------------------------------------
    def _show_groups(self):
        targets = self._selected_rows()
        if len(targets) != 1:
            return
        t = targets[0]
        groups = self.manager.get_user_groups(t["server_id"], t["username"])
        if groups:
            QMessageBox.information(
                self,
                f"Grupos de {t['username']} @ {t['server_name']}",
                "\n".join(groups)
            )
        else:
            QMessageBox.warning(self, "Grupos", "No se obtuvieron grupos.")

    # ------------------------------------------------------------------
    # MODIFICAR GRUPOS (masivo)
    # ------------------------------------------------------------------
    def _open_bulk_groups(self):
        targets = self._selected_rows()
        if not targets:
            return
        dialog = BulkGroupDialog(self.manager, targets, self)
        dialog.exec()