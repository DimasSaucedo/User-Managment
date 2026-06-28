from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QStackedWidget
)

from app.views.server_lists_view import ServerListsView


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("ServerAdmin")
        self.resize(1400, 800)

        # Widget central
        central = QWidget()
        self.setCentralWidget(central)

        # Layout principal
        layout = QHBoxLayout(central)

        # ==========================
        # Menú lateral
        # ==========================

        menu = QVBoxLayout()

        titulo = QLabel("ServerAdmin")
        titulo.setStyleSheet("font-size:20px; font-weight:bold;")

        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_listas = QPushButton("Listas")
        self.btn_servidores = QPushButton("Servidores")
        self.btn_usuarios = QPushButton("Usuarios")
        self.btn_operaciones = QPushButton("Operaciones")
        self.btn_bitacora = QPushButton("Bitácora")
        self.btn_configuracion = QPushButton("Configuración")

        menu.addWidget(titulo)
        menu.addWidget(self.btn_dashboard)
        menu.addWidget(self.btn_listas)
        menu.addWidget(self.btn_servidores)
        menu.addWidget(self.btn_usuarios)
        menu.addWidget(self.btn_operaciones)
        menu.addWidget(self.btn_bitacora)
        menu.addWidget(self.btn_configuracion)
        menu.addStretch()

        menu_widget = QWidget()
        menu_widget.setLayout(menu)
        menu_widget.setFixedWidth(220)

        # ==========================
        # Páginas
        # ==========================

        self.pages = QStackedWidget()

        self.dashboard = QLabel("Dashboard")
        self.dashboard.setStyleSheet("font-size:28px;")

        self.server_lists_view = ServerListsView()

        self.pages.addWidget(self.dashboard)           # Página 0
        self.pages.addWidget(self.server_lists_view)   # Página 1

        # ==========================
        # Layout principal
        # ==========================

        layout.addWidget(menu_widget)
        layout.addWidget(self.pages)

        # ==========================
        # Eventos
        # ==========================

        self.btn_dashboard.clicked.connect(
            lambda: self.pages.setCurrentIndex(0)
        )

        self.btn_listas.clicked.connect(
            lambda: self.pages.setCurrentIndex(1)
        )

        # Mostrar Dashboard al iniciar
        self.pages.setCurrentIndex(0)