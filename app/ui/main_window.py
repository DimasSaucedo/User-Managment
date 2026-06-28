from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QStackedWidget
)

from app.ui.views.server_lists_view import ServerListsView
from app.ui.views.servers_view import ServersView
from app.ui.audit_log_view import AuditLogView


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("ServerAdmin")
        self.resize(1400, 800)

        self.init_ui()

    def init_ui(self):

        # ==========================
        # Widget central
        # ==========================
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
        # Páginas (Stack)
        # ==========================
        self.pages = QStackedWidget()

        # Página 0: Dashboard
        self.dashboard = QLabel("Dashboard")
        self.dashboard.setStyleSheet("font-size:28px;")

        # Página 1: Listas
        self.server_lists_view = ServerListsView()

        # Página 2: Servidores (CRUD)
        self.servers_view = ServersView()

        # Página 3: Bitácora (NUEVA)
        self.audit_log_view = AuditLogView()

        # Agregar páginas al stack
        self.pages.addWidget(self.dashboard)            # 0
        self.pages.addWidget(self.server_lists_view)   # 1
        self.pages.addWidget(self.servers_view)        # 2
        self.pages.addWidget(self.audit_log_view)      # 3

        # ==========================
        # Layout principal
        # ==========================
        layout.addWidget(menu_widget)
        layout.addWidget(self.pages)

        # ==========================
        # Eventos navegación
        # ==========================
        self.btn_dashboard.clicked.connect(
            lambda: self.pages.setCurrentIndex(0)
        )

        self.btn_listas.clicked.connect(
            lambda: self.pages.setCurrentIndex(1)
        )

        self.btn_servidores.clicked.connect(
            lambda: self.pages.setCurrentIndex(2)
        )

        self.btn_bitacora.clicked.connect(
            lambda: self.pages.setCurrentIndex(3)
        )

        # ==========================
        # Vista inicial
        # ==========================
        self.pages.setCurrentIndex(0)