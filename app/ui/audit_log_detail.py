from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton
)


class AuditLogDetail(QDialog):

    def __init__(self, log):
        super().__init__()

        self.setWindowTitle("Detalle de Auditoría")
        self.resize(600, 400)

        layout = QVBoxLayout()

        layout.addWidget(QLabel(f"Acción: {log.action}"))
        layout.addWidget(QLabel(f"Estado: {log.status}"))
        layout.addWidget(QLabel(f"Servidor: {log.server}"))
        layout.addWidget(QLabel(f"Fecha: {log.created_at}"))

        self.message = QTextEdit()
        self.message.setReadOnly(True)
        self.message.setText(str(log.message))

        layout.addWidget(QLabel("Mensaje / Comando:"))
        layout.addWidget(self.message)

        btn = QPushButton("Cerrar")
        btn.clicked.connect(self.close)

        layout.addWidget(btn)

        self.setLayout(layout)