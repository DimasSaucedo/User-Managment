from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QHBoxLayout
)


class SSHDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Conexión SSH")
        self.setFixedSize(400, 300)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Usuario"))
        self.usuario = QLineEdit()
        layout.addWidget(self.usuario)

        layout.addWidget(QLabel("Contraseña"))
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password)

        layout.addWidget(QLabel("Puerto"))
        self.port = QSpinBox()
        self.port.setMaximum(65535)
        self.port.setValue(22)
        layout.addWidget(self.port)

        botones = QHBoxLayout()

        self.btn_conectar = QPushButton("Conectar")
        self.btn_cancelar = QPushButton("Cancelar")

        botones.addStretch()
        botones.addWidget(self.btn_conectar)
        botones.addWidget(self.btn_cancelar)

        layout.addLayout(botones)

        self.setLayout(layout)

        self.btn_conectar.clicked.connect(self.accept)
        self.btn_cancelar.clicked.connect(self.reject)