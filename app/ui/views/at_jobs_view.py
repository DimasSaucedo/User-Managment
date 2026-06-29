"""
Vista de jobs AT programados en todos los servidores conectados.
Muestra jobs, permite cancelar desde la UI.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QAbstractItemView
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont


# ── Worker ────────────────────────────────────────────────────────────
class FetchATWorker(QThread):
    jobs_ready = Signal(list)

    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    def run(self):
        all_jobs = []
        for sid, conn in self.manager.connections.items():
            if not conn.client:
                continue
            try:
                # atq muestra: id  fecha  queue  user
                out, _ = conn.execute("atq")
                for line in out.splitlines():
                    parts = line.split()
                    if not parts:
                        continue
                    job_id = parts[0]
                    # at -c job_id para ver el contenido
                    content_out, _ = conn.execute(f"at -c {job_id} 2>/dev/null")
                    # Extraer solo líneas que no son exports/variables
                    cmd_lines = [
                        l for l in content_out.splitlines()
                        if l.strip()
                        and not l.startswith("#")
                        and "export" not in l
                        and "=" in l and "export" not in l or (
                            l.strip() and
                            not any(x in l for x in ["export", "umask", "cd /", "echo 'Execution"])
                            and "=" not in l
                        )
                    ]
                    # Fecha: parts[1..4] típicamente "Mon Jun 29 18:27:00 2026"
                    fecha = " ".join(parts[1:5]) if len(parts) >= 5 else "—"
                    cmd_preview = "; ".join(l.strip() for l in cmd_lines[:3]) or "—"

                    all_jobs.append({
                        "server_id":   sid,
                        "server_name": conn.server.nombre,
                        "job_id":      job_id,
                        "fecha":       fecha,
                        "cmd":         cmd_preview,
                    })
            except Exception as e:
                all_jobs.append({
                    "server_id":   sid,
                    "server_name": conn.server.nombre,
                    "job_id":      "—",
                    "fecha":       "—",
                    "cmd":         f"ERROR: {e}",
                })
        self.jobs_ready.emit(all_jobs)


class CancelATWorker(QThread):
    result = Signal(str, str, bool, str)  # server_name, job_id, ok, msg
    finished = Signal()

    def __init__(self, manager, targets):
        super().__init__()
        self.manager = manager
        self.targets = targets  # list of {"server_id", "server_name", "job_id"}

    def run(self):
        for t in self.targets:
            conn = self.manager.connections.get(t["server_id"])
            if not conn or not conn.client:
                self.result.emit(t["server_name"], t["job_id"], False, "Sin conexión")
                continue
            try:
                _, err = conn.execute(f"atrm {t['job_id']}")
                ok = not bool(err.strip())
                self.result.emit(t["server_name"], t["job_id"], ok, err.strip() or "OK")
            except Exception as e:
                self.result.emit(t["server_name"], t["job_id"], False, str(e))
        self.finished.emit()


# ── Vista ─────────────────────────────────────────────────────────────
class ATJobsView(QWidget):

    COL_SERVER = 0
    COL_JOB    = 1
    COL_FECHA  = 2
    COL_CMD    = 3

    def __init__(self, manager_provider):
        """
        manager_provider: callable que retorna el MultiSSHManager actual
        (para obtenerlo desde DashboardView)
        """
        super().__init__()
        self.manager_provider = manager_provider
        self._jobs: list[dict] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        hdr = QHBoxLayout()
        title = QLabel("Jobs AT Programados")
        title.setFont(QFont("", 14, QFont.Bold))
        self.btn_refresh = QPushButton("↺ Recargar")
        self.btn_cancel  = QPushButton("✗ Cancelar seleccionados")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.setStyleSheet("color: #f38ba8;")
        hdr.addWidget(title); hdr.addStretch()
        hdr.addWidget(self.btn_refresh)
        hdr.addWidget(self.btn_cancel)
        layout.addLayout(hdr)

        self.status_label = QLabel("Haz clic en Recargar para obtener los jobs.")
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Servidor", "Job ID", "Fecha programada", "Comando"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(self.COL_CMD, QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.btn_refresh.clicked.connect(self._fetch)
        self.btn_cancel.clicked.connect(self._cancel_selected)
        self.table.itemSelectionChanged.connect(
            lambda: self.btn_cancel.setEnabled(len(self.table.selectedItems()) > 0)
        )

    def showEvent(self, event):
        """Auto-recargar al mostrar la vista."""
        super().showEvent(event)
        self._fetch()

    def _fetch(self):
        manager = self.manager_provider()
        active = [c for c in manager.connections.values() if c.client]
        if not active:
            self.status_label.setText("Sin servidores conectados. Ve al Dashboard primero.")
            return

        self.table.setRowCount(0)
        self._jobs = []
        self.status_label.setText("Consultando jobs AT…")
        self.btn_refresh.setEnabled(False)

        self.worker = FetchATWorker(manager)
        self.worker.jobs_ready.connect(self._populate)
        self.worker.start()

    def _populate(self, jobs: list[dict]):
        self._jobs = jobs
        self.table.setRowCount(len(jobs))
        for row, j in enumerate(jobs):
            srv_item = QTableWidgetItem(j["server_name"])
            srv_item.setData(Qt.UserRole, (j["server_id"], j["job_id"], j["server_name"]))
            self.table.setItem(row, self.COL_SERVER, srv_item)
            self.table.setItem(row, self.COL_JOB,    QTableWidgetItem(j["job_id"]))
            self.table.setItem(row, self.COL_FECHA,  QTableWidgetItem(j["fecha"]))
            cmd_item = QTableWidgetItem(j["cmd"])
            if "ERROR" in j["cmd"]:
                cmd_item.setForeground(QColor("#f38ba8"))
            self.table.setItem(row, self.COL_CMD, cmd_item)

        self.status_label.setText(f"{len(jobs)} job(s) encontrado(s).")
        self.btn_refresh.setEnabled(True)

    def _cancel_selected(self):
        seen = set()
        targets = []
        for idx in self.table.selectedIndexes():
            if idx.column() != 0:
                continue
            item = self.table.item(idx.row(), self.COL_SERVER)
            sid, job_id, sname = item.data(Qt.UserRole)
            key = (sid, job_id)
            if key not in seen:
                seen.add(key)
                targets.append({"server_id": sid, "server_name": sname, "job_id": job_id})

        if not targets:
            return

        answer = QMessageBox.question(
            self, "Confirmar",
            f"¿Cancelar <b>{len(targets)}</b> job(s)?",
            QMessageBox.Yes | QMessageBox.No
        )
        if answer != QMessageBox.Yes:
            return

        self.btn_cancel.setEnabled(False)
        self.btn_refresh.setEnabled(False)
        self.status_label.setText("Cancelando…")

        self.cancel_worker = CancelATWorker(self.manager_provider(), targets)
        self.cancel_worker.result.connect(self._on_cancel_result)
        self.cancel_worker.finished.connect(self._fetch)
        self.cancel_worker.start()

    def _on_cancel_result(self, server_name, job_id, ok, msg):
        verb = "Cancelado" if ok else f"Error ({msg})"
        self.status_label.setText(f"{server_name} job {job_id}: {verb}")