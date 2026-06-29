"""
Dialog para modificar grupos masivamente con expiración opcional.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QRadioButton,
    QButtonGroup, QGroupBox, QProgressBar, QHeaderView,
    QCheckBox, QDateTimeEdit
)
from PySide6.QtCore import Qt, QThread, Signal, QDateTime
from PySide6.QtGui import QColor


class BulkWorker(QThread):
    progress = Signal(dict)
    finished = Signal()

    def __init__(self, manager, targets, groups, action, expire_at):
        super().__init__()
        self.manager = manager
        self.targets = targets
        self.groups = groups
        self.action = action
        self.expire_at = expire_at

    def run(self):
        results = self.manager.bulk_modify_groups(
            self.targets, self.groups, self.action, self.expire_at
        )
        for r in results:
            self.progress.emit(r)
        self.finished.emit()


class BulkGroupDialog(QDialog):
    def __init__(self, manager, targets, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.targets = targets
        self.worker = None
        self.setWindowTitle("Modificar Grupos — Masivo")
        self.setMinimumWidth(720)
        self.setMinimumHeight(560)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"<b>{len(self.targets)}</b> usuario(s) seleccionado(s):"))
        summary = QTableWidget(0, 2)
        summary.setHorizontalHeaderLabels(["Servidor", "Usuario"])
        summary.setMaximumHeight(120)
        summary.setEditTriggers(QTableWidget.NoEditTriggers)
        summary.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for t in self.targets:
            r = summary.rowCount(); summary.insertRow(r)
            summary.setItem(r, 0, QTableWidgetItem(t["server_name"]))
            summary.setItem(r, 1, QTableWidgetItem(t["username"]))
        layout.addWidget(summary)

        # Acción
        action_box = QGroupBox("Operación")
        al = QVBoxLayout(action_box)
        self.radio_add = QRadioButton("Agregar grupo(s)")
        self.radio_remove = QRadioButton("Quitar grupo(s)")
        self.radio_add.setChecked(True)
        bg = QButtonGroup(self); bg.addButton(self.radio_add); bg.addButton(self.radio_remove)
        al.addWidget(self.radio_add); al.addWidget(self.radio_remove)

        gr = QHBoxLayout()
        gr.addWidget(QLabel("Grupos (coma):"))
        self.groups_edit = QLineEdit()
        self.groups_edit.setPlaceholderText("sudo, docker, www-data")
        gr.addWidget(self.groups_edit)
        al.addLayout(gr)
        layout.addWidget(action_box)

        # Expiración
        exp_box = QGroupBox("Expiración del grupo (solo aplica al agregar)")
        el = QVBoxLayout(exp_box)
        self.chk_expire = QCheckBox("Remover automáticamente en fecha/hora:")
        self.dt_expire = QDateTimeEdit(QDateTime.currentDateTime().addDays(1))
        self.dt_expire.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.dt_expire.setEnabled(False)
        self.chk_expire.toggled.connect(self.dt_expire.setEnabled)
        self.radio_remove.toggled.connect(lambda c: exp_box.setEnabled(not c))
        el.addWidget(self.chk_expire)
        el.addWidget(self.dt_expire)
        layout.addWidget(exp_box)

        # Resultados
        layout.addWidget(QLabel("Resultados:"))
        self.result_table = QTableWidget(0, 4)
        self.result_table.setHorizontalHeaderLabels(["Servidor", "Usuario", "Grupo", "Estado"])
        self.result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.result_table)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        btns = QHBoxLayout()
        self.btn_run = QPushButton("Ejecutar"); self.btn_run.setDefault(True)
        self.btn_close = QPushButton("Cerrar")
        btns.addStretch(); btns.addWidget(self.btn_run); btns.addWidget(self.btn_close)
        layout.addLayout(btns)

        self.btn_run.clicked.connect(self._run)
        self.btn_close.clicked.connect(self.accept)

    def _run(self):
        groups = [g.strip() for g in self.groups_edit.text().split(",") if g.strip()]
        if not groups:
            return
        action = "add" if self.radio_add.isChecked() else "remove"
        expire_at = None
        if action == "add" and self.chk_expire.isChecked():
            expire_at = self.dt_expire.dateTime().toString("yyyy-MM-dd HH:mm")

        self.result_table.setRowCount(0)
        self._done = 0
        total = len(self.targets) * len(groups)
        self.progress_bar.setMaximum(total); self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.btn_run.setEnabled(False)

        self.worker = BulkWorker(self.manager, self.targets, groups, action, expire_at)
        self.worker.progress.connect(self._on_result)
        self.worker.finished.connect(lambda: (
            self.btn_run.setEnabled(True),
            self.progress_bar.setVisible(False)
        ))
        self.worker.start()

    def _on_result(self, r):
        row = self.result_table.rowCount(); self.result_table.insertRow(row)
        self.result_table.setItem(row, 0, QTableWidgetItem(r["server_name"]))
        self.result_table.setItem(row, 1, QTableWidgetItem(r["username"]))
        self.result_table.setItem(row, 2, QTableWidgetItem(r["group"]))
        txt = "✓ OK" if r["ok"] else f"✗ {r['msg']}"
        item = QTableWidgetItem(txt)
        item.setForeground(QColor("#a6e3a1") if r["ok"] else QColor("#f38ba8"))
        self.result_table.setItem(row, 3, item)
        self._done += 1; self.progress_bar.setValue(self._done)