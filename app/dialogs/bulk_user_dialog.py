"""
Dialog para Crear / Editar / Eliminar usuarios de forma masiva en N servidores.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QCheckBox, QProgressBar, QTabWidget, QWidget,
    QListWidget, QListWidgetItem, QAbstractItemView, QMessageBox,
    QComboBox, QSplitter
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor


# ── Workers ──────────────────────────────────────────────────────────
class CreateWorker(QThread):
    result = Signal(dict)
    finished = Signal()

    def __init__(self, manager, server_ids, user_data):
        super().__init__()
        self.manager = manager
        self.server_ids = server_ids
        self.user_data = user_data

    def run(self):
        for r in self.manager.bulk_create_user(self.server_ids, self.user_data):
            self.result.emit(r)
        self.finished.emit()


class EditWorker(QThread):
    result = Signal(dict)
    finished = Signal()

    def __init__(self, manager, targets, changes):
        super().__init__()
        self.manager = manager
        self.targets = targets
        self.changes = changes

    def run(self):
        for r in self.manager.bulk_edit_user(self.targets, self.changes):
            self.result.emit(r)
        self.finished.emit()


class DeleteWorker(QThread):
    result = Signal(dict)
    finished = Signal()

    def __init__(self, manager, targets, remove_home):
        super().__init__()
        self.manager = manager
        self.targets = targets
        self.remove_home = remove_home

    def run(self):
        for r in self.manager.bulk_delete_user(self.targets, self.remove_home):
            self.result.emit(r)
        self.finished.emit()


# ── Widget reutilizable: tabla de resultados ─────────────────────────
class ResultTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(0, 4, parent)
        self.setHorizontalHeaderLabels(["Servidor", "Acción", "Usuario", "Estado"])
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def add_result(self, r: dict):
        row = self.rowCount(); self.insertRow(row)
        self.setItem(row, 0, QTableWidgetItem(r.get("server_name", "")))
        self.setItem(row, 1, QTableWidgetItem(r.get("action", "")))
        self.setItem(row, 2, QTableWidgetItem(r.get("username", "")))
        txt = "✓ OK" if r["ok"] else f"✗ {r['msg']}"
        item = QTableWidgetItem(txt)
        item.setForeground(QColor("#a6e3a1") if r["ok"] else QColor("#f38ba8"))
        self.setItem(row, 3, item)


# ── Dialog principal ─────────────────────────────────────────────────
class BulkUserDialog(QDialog):
    """
    manager: MultiSSHManager con conexiones activas.
    connected_servers: lista de {"server_id", "server_name"}
    selected_targets: lista de {"server_id", "server_name", "username"} (puede estar vacío)
    """

    def __init__(self, manager, connected_servers, selected_targets=None, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.connected_servers = connected_servers
        self.selected_targets = selected_targets or []
        self.setWindowTitle("Gestión de Usuarios — Masivo")
        self.setMinimumWidth(780)
        self.setMinimumHeight(620)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_create_tab(), "➕ Crear")
        self.tabs.addTab(self._build_edit_tab(),   "✏️ Editar")
        self.tabs.addTab(self._build_delete_tab(), "🗑️ Eliminar")
        layout.addWidget(self.tabs)

        self.progress_bar = QProgressBar(); self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.result_table = ResultTable()
        layout.addWidget(QLabel("Resultados:"))
        layout.addWidget(self.result_table)

        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        bh = QHBoxLayout(); bh.addStretch(); bh.addWidget(btn_close)
        layout.addLayout(bh)

    # ── TAB CREAR ────────────────────────────────────────────────────
    def _build_create_tab(self):
        w = QWidget(); layout = QVBoxLayout(w)

        # Selección de servidores
        layout.addWidget(QLabel("Servidores destino:"))
        self.create_server_list = QListWidget()
        self.create_server_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.create_server_list.setMaximumHeight(110)
        for s in self.connected_servers:
            item = QListWidgetItem(f"{s['server_name']}")
            item.setData(Qt.UserRole, s["server_id"])
            self.create_server_list.addItem(item)
        layout.addWidget(self.create_server_list)

        # Datos del usuario
        form = QGroupBox("Datos del usuario")
        fl = QVBoxLayout(form)
        self._c_username = self._field(fl, "Usuario *:")
        self._c_password = self._field(fl, "Password *:", echo=True)
        self._c_uid      = self._field(fl, "UID (opcional):")
        self._c_gid      = self._field(fl, "GID principal (opcional):")
        self._c_home     = self._field(fl, "Home (opcional):", placeholder="/home/usuario")
        self._c_shell    = self._field(fl, "Shell (opcional):", placeholder="/bin/bash")
        self._c_groups   = self._field(fl, "Grupos adicionales:", placeholder="sudo,docker")
        layout.addWidget(form)

        btn = QPushButton("Crear usuario en servidores seleccionados")
        btn.clicked.connect(self._run_create)
        layout.addWidget(btn)
        return w

    # ── TAB EDITAR ───────────────────────────────────────────────────
    def _build_edit_tab(self):
        w = QWidget(); layout = QVBoxLayout(w)

        layout.addWidget(QLabel(
            f"Usuarios a editar: <b>{len(self.selected_targets)}</b> "
            f"(seleccionados en la tabla principal)"
        ))

        if self.selected_targets:
            t = QTableWidget(0, 2)
            t.setHorizontalHeaderLabels(["Servidor", "Usuario"])
            t.setMaximumHeight(100)
            t.setEditTriggers(QTableWidget.NoEditTriggers)
            t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            for tgt in self.selected_targets:
                r = t.rowCount(); t.insertRow(r)
                t.setItem(r, 0, QTableWidgetItem(tgt["server_name"]))
                t.setItem(r, 1, QTableWidgetItem(tgt["username"]))
            layout.addWidget(t)
        else:
            layout.addWidget(QLabel("⚠️  Selecciona usuarios en la tabla principal primero."))

        form = QGroupBox("Cambios a aplicar (dejar en blanco = no cambiar)")
        fl = QVBoxLayout(form)
        self._e_shell    = self._field(fl, "Nuevo shell:")
        self._e_home     = self._field(fl, "Nuevo home:")
        self._e_password = self._field(fl, "Nueva contraseña:", echo=True)

        lock_row = QHBoxLayout()
        self._e_lock   = QCheckBox("Bloquear cuenta")
        self._e_unlock = QCheckBox("Desbloquear cuenta")
        self._e_lock.toggled.connect(lambda c: self._e_unlock.setChecked(False) if c else None)
        self._e_unlock.toggled.connect(lambda c: self._e_lock.setChecked(False) if c else None)
        lock_row.addWidget(self._e_lock); lock_row.addWidget(self._e_unlock)
        fl.addLayout(lock_row)
        layout.addWidget(form)

        btn = QPushButton("Aplicar cambios")
        btn.clicked.connect(self._run_edit)
        layout.addWidget(btn)
        return w

    # ── TAB ELIMINAR ─────────────────────────────────────────────────
    def _build_delete_tab(self):
        w = QWidget(); layout = QVBoxLayout(w)

        layout.addWidget(QLabel(
            f"Usuarios a eliminar: <b>{len(self.selected_targets)}</b>"
        ))

        if self.selected_targets:
            t = QTableWidget(0, 2)
            t.setHorizontalHeaderLabels(["Servidor", "Usuario"])
            t.setMaximumHeight(100)
            t.setEditTriggers(QTableWidget.NoEditTriggers)
            t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            for tgt in self.selected_targets:
                r = t.rowCount(); t.insertRow(r)
                t.setItem(r, 0, QTableWidgetItem(tgt["server_name"]))
                t.setItem(r, 1, QTableWidgetItem(tgt["username"]))
            layout.addWidget(t)

        self._d_remove_home = QCheckBox("Eliminar directorio home (-r)")
        layout.addWidget(self._d_remove_home)

        warn = QLabel("⚠️  Esta acción es irreversible.")
        warn.setStyleSheet("color: #f38ba8; font-weight: bold;")
        layout.addWidget(warn)

        btn = QPushButton("Eliminar usuarios")
        btn.setStyleSheet("background-color: #f38ba8; color: black;")
        btn.clicked.connect(self._run_delete)
        layout.addWidget(btn)
        layout.addStretch()
        return w

    # ── Helpers ──────────────────────────────────────────────────────
    def _field(self, layout, label, placeholder="", echo=False):
        row = QHBoxLayout()
        row.addWidget(QLabel(label))
        edit = QLineEdit()
        if placeholder: edit.setPlaceholderText(placeholder)
        if echo: edit.setEchoMode(QLineEdit.Password)
        row.addWidget(edit)
        layout.addLayout(row)
        return edit

    def _start_progress(self, total):
        self.result_table.setRowCount(0)
        self.progress_bar.setMaximum(max(total, 1))
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self._done = 0

    def _on_result(self, r):
        self.result_table.add_result(r)
        self._done += 1; self.progress_bar.setValue(self._done)

    def _on_finished(self):
        self.progress_bar.setVisible(False)

    # ── Ejecutores ───────────────────────────────────────────────────
    def _run_create(self):
        selected_items = self.create_server_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Servidores", "Selecciona al menos un servidor.")
            return
        uname = self._c_username.text().strip()
        pwd   = self._c_password.text()
        if not uname or not pwd:
            QMessageBox.warning(self, "Datos", "Usuario y password son obligatorios.")
            return

        server_ids = [item.data(Qt.UserRole) for item in selected_items]
        user_data = {
            "username": uname, "password": pwd,
            "uid": self._c_uid.text().strip(),
            "gid": self._c_gid.text().strip(),
            "home": self._c_home.text().strip(),
            "shell": self._c_shell.text().strip(),
            "groups": self._c_groups.text().strip(),
        }
        self._start_progress(len(server_ids))
        self.worker = CreateWorker(self.manager, server_ids, user_data)
        self.worker.result.connect(self._on_result)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _run_edit(self):
        if not self.selected_targets:
            QMessageBox.warning(self, "Sin selección", "No hay usuarios seleccionados.")
            return
        changes = {
            "shell":    self._e_shell.text().strip() or None,
            "home":     self._e_home.text().strip() or None,
            "password": self._e_password.text() or None,
            "lock":     self._e_lock.isChecked(),
            "unlock":   self._e_unlock.isChecked(),
        }
        if not any(changes.values()):
            QMessageBox.warning(self, "Sin cambios", "No hay nada que modificar.")
            return
        self._start_progress(len(self.selected_targets))
        self.worker = EditWorker(self.manager, self.selected_targets, changes)
        self.worker.result.connect(self._on_result)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _run_delete(self):
        if not self.selected_targets:
            QMessageBox.warning(self, "Sin selección", "No hay usuarios seleccionados.")
            return
        answer = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Eliminar <b>{len(self.selected_targets)}</b> usuario(s)?<br>"
            "Esta acción es irreversible.",
            QMessageBox.Yes | QMessageBox.No
        )
        if answer != QMessageBox.Yes:
            return
        self._start_progress(len(self.selected_targets))
        self.worker = DeleteWorker(
            self.manager, self.selected_targets, self._d_remove_home.isChecked()
        )
        self.worker.result.connect(self._on_result)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()