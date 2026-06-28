from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QHBoxLayout
)


class ServerListDialog(QDialog):

    def __init__(self, parent=None, nombre="", descripcion=""):
        super().__init__(parent)

        self.setWindowTitle("Lista de Servidores")
        self.setFixedSize(400, 250)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Nombre"))

        self.nombre = QLineEdit()
        self.nombre.setText(nombre)

        layout.addWidget(self.nombre)

        layout.addWidget(QLabel("Descripción"))

        self.descripcion = QTextEdit()
        self.descripcion.setPlainText(descripcion)

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