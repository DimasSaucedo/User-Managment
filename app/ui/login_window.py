from app.ui.main_window import MainWindow

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QCheckBox
)

class LoginWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("ServerAdmin")
        self.setFixedSize(400, 300)

        layout = QVBoxLayout()

        titulo = QLabel("ServerAdmin")
        titulo.setStyleSheet("font-size:22px;font-weight:bold;")

        self.usuario = QLineEdit()
        self.usuario.setPlaceholderText("Usuario SSH")

        self.password = QLineEdit()
        self.password.setPlaceholderText("Contraseña")
        self.password.setEchoMode(QLineEdit.Password)

        self.recordar = QCheckBox("Recordar usuario")

        self.boton = QPushButton("Iniciar")

        layout.addWidget(titulo)
        layout.addWidget(self.usuario)
        layout.addWidget(self.password)
        layout.addWidget(self.recordar)
        layout.addWidget(self.boton)

        self.setLayout(layout)
        self.boton.clicked.connect(self.login)
    
    def login(self):

        self.main = MainWindow()
        self.main.show()

        self.close()