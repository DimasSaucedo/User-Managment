from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QRadioButton,
    QButtonGroup, QGroupBox, QProgressBar, QHeaderView, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor


# ------------------------------------------------------------------
# Worker thread para no bloquear la UI
# ------------------------------------------------------------------
class BulkWorker(QThread):
    progress = Signal(dict)   # emite cada resultado
    finished = Signal()

    def __init__(self, manager, targets, groups, action):
        super().__init__()
        self.manager = manager
        self.targets = targets
        self.groups = groups
        self.action = action

    def run(self):
        results = self.manager.bulk_modify_groups(
            self.targets, self.groups, self.action
        )
        for r in results:
            self.progress.emit(r)
        self.finished.emit()


# ------------------------------------------------------------------
# Dialog principal
# ------------------------------------------------------------------
class BulkGroupDialog(QDialog):
    """
    Recibe:
      - manager: MultiSSHManager (con conexiones activas)
      - targets: lista de {"server_id": int, "server_name": str, "username": str}
    """

    def __init__(self, manager, targets, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.targets = targets
        self.worker = None

        self.setWindowTitle("Modificar Grupos — Operación Masiva")
        self.setMinimumWidth(700)
        self.setMinimumHeight(540)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # --- Resumen de selección ---
        layout.addWidget(QLabel(
            f"<b>{len(self.targets)}</b> usuario(s) seleccionado(s):"
        ))

        summary = QTableWidget()
        summary.setColumnCount(2)
        summary.setHorizontalHeaderLabels(["Servidor", "Usuario"])
        summary.setMaximumHeight(130)
        summary.setEditTriggers(QTableWidget.NoEditTriggers)
        summary.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for t in self.targets:
            row = summary.rowCount()
            summary.insertRow(row)
            summary.setItem(row, 0, QTableWidgetItem(t["server_name"]))
            summary.setItem(row, 1, QTableWidgetItem(t["username"]))

        layout.addWidget(summary)

        # --- Acción y grupos ---
        action_box = QGroupBox("Operación")
        action_layout = QVBoxLayout(action_box)

        self.radio_add = QRadioButton("Agregar a grupo(s)")
        self.radio_remove = QRadioButton("Quitar de grupo(s)")
        self.radio_add.setChecked(True)

        bg = QButtonGroup(self)
        bg.addButton(self.radio_add)
        bg.addButton(self.radio_remove)

        action_layout.addWidget(self.radio_add)
        action_layout.addWidget(self.radio_remove)

        group_row = QHBoxLayout()
        group_row.addWidget(QLabel("Grupos (separados por coma):"))
        self.groups_edit = QLineEdit()
        self.groups_edit.setPlaceholderText("sudo, docker, www-data")
        group_row.addWidget(self.groups_edit)
        action_layout.addLayout(group_row)

        layout.addWidget(action_box)

        # --- Resultados ---
        layout.addWidget(QLabel("Resultados:"))

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(
            ["Servidor", "Usuario", "Grupo", "Estado"]
        )
        self.result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.result_table)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # --- Botones ---
        btn_layout = QHBoxLayout()
        self.btn_run = QPushButton("Ejecutar")
        self.btn_run.setDefault(True)
        self.btn_close = QPushButton("Cerrar")
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_run)
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

        self.btn_run.clicked.connect(self._run)
        self.btn_close.clicked.connect(self.accept)

    def _run(self):
        raw = self.groups_edit.text().strip()
        if not raw:
            return

        groups = [g.strip() for g in raw.split(",") if g.strip()]
        action = "add" if self.radio_add.isChecked() else "remove"
        total = len(self.targets) * len(groups)

        self.result_table.setRowCount(0)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(0)
        self.btn_run.setEnabled(False)
        self._done_count = 0

        self.worker = BulkWorker(self.manager, self.targets, groups, action)
        self.worker.progress.connect(self._on_result)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_result(self, result):
        row = self.result_table.rowCount()
        self.result_table.insertRow(row)

        self.result_table.setItem(row, 0, QTableWidgetItem(result["server_name"]))
        self.result_table.setItem(row, 1, QTableWidgetItem(result["username"]))
        self.result_table.setItem(row, 2, QTableWidgetItem(result["group"]))

        status_text = "✓ OK" if result["ok"] else f"✗ {result['msg']}"
        status_item = QTableWidgetItem(status_text)
        status_item.setForeground(
            QColor("#a6e3a1") if result["ok"] else QColor("#f38ba8")
        )
        self.result_table.setItem(row, 3, status_item)

        self._done_count += 1
        self.progress_bar.setValue(self._done_count)

    def _on_finished(self):
        self.btn_run.setEnabled(True)
        self.progress_bar.setVisible(False)