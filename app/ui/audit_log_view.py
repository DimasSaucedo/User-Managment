from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QComboBox, QPushButton, QLabel, QHBoxLayout
)

from app.controllers.audit_log_controller import AuditLogController


class AuditLogView(QWidget):

    def __init__(self):
        super().__init__()

        self.controller = AuditLogController()

        self.setWindowTitle("Audit Logs")
        self.resize(900, 500)

        self.layout = QVBoxLayout()

        # ===== FILTROS =====
        self.filter_layout = QHBoxLayout()

        self.action_filter = QComboBox()
        self.action_filter.addItem("ALL")
        self.action_filter.addItems(["SSH_EXEC", "GROUP_MOD", "SSH_EXEC_ERROR"])

        self.status_filter = QComboBox()
        self.status_filter.addItems(["ALL", "SUCCESS", "ERROR"])

        self.refresh_btn = QPushButton("Refrescar")

        self.filter_layout.addWidget(QLabel("Acción"))
        self.filter_layout.addWidget(self.action_filter)
        self.filter_layout.addWidget(QLabel("Estado"))
        self.filter_layout.addWidget(self.status_filter)
        self.filter_layout.addWidget(self.refresh_btn)

        self.layout.addLayout(self.filter_layout)

        # ===== TABLA =====
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Fecha", "Acción", "Estado", "Servidor", "Mensaje"
        ])

        self.layout.addWidget(self.table)

        self.setLayout(self.layout)

        self.table.cellDoubleClicked.connect(self.open_detail)
        
        # eventos
        self.refresh_btn.clicked.connect(self.load_data)

        self.load_data()

    def load_data(self):

        action = self.action_filter.currentText()
        status = self.status_filter.currentText()

        action = None if action == "ALL" else action
        status = None if status == "ALL" else status

        logs = self.controller.get_filtered_logs(action, status)

        self.table.setRowCount(len(logs))

        for row, log in enumerate(logs):

            self.table.setItem(row, 0, QTableWidgetItem(str(log.created_at)))
            self.table.setItem(row, 1, QTableWidgetItem(log.action))
            self.table.setItem(row, 2, QTableWidgetItem(log.status))
            self.table.setItem(row, 3, QTableWidgetItem(str(log.server)))
            self.table.setItem(row, 4, QTableWidgetItem(str(log.message)))
            
    def open_detail(self, row, column):

        log = self.controller.get_logs(500)[row]

        from app.ui.audit_log_detail import AuditLogDetail

        dialog = AuditLogDetail(log)
        dialog.exec()   