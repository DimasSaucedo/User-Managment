from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QHBoxLayout,
    QSpinBox
)


class ServerDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Servidor")
        self.setFixedSize(450, 400)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Nombre"))
        self.nombre = QLineEdit()
        layout.addWidget(self.nombre)

        layout.addWidget(QLabel("Hostname"))
        self.hostname = QLineEdit()
        layout.addWidget(self.hostname)

        layout.addWidget(QLabel("IP"))
        self.ip = QLineEdit()
        layout.addWidget(self.ip)

        layout.addWidget(QLabel("Puerto"))
        self.puerto = QSpinBox()
        self.puerto.setMaximum(65535)
        self.puerto.setValue(22)
        layout.addWidget(self.puerto)

        layout.addWidget(QLabel("Descripción"))
        self.descripcion = QTextEdit()
        layout.addWidget(self.descripcion)

        botones = QHBoxLayout()

        self.btn_guardar = QPushButton("Guardar")
        self.btn_cancelar = QPushButton("Cancelar")

        botones.addStretch()
        botones.addWidget(self.btn_guardar)
        botones.addWidget(self.btn_cancelar)

        layout.addLayout(botones)

        self.setLayout(layout)

        self.btn_guardar.clicked.connect(self.accept)
        self.btn_cancelar.clicked.connect(self.reject)