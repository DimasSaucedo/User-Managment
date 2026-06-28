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
from app.ui.views.users_view import UsersView

from app.services.ssh_service import SSHService


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("ServerAdmin")
        self.resize(1400, 800)

        # ==========================
        # SERVICES (GLOBAL APP STATE)
        # ==========================
        self.ssh_service = SSHService()

        self.init_ui()

    def init_ui(self):

        # ==========================
        # Widget central
        # ==========================
        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)

        # ==========================
        # MENU
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
        # STACKED PAGES
        # ==========================
        self.pages = QStackedWidget()

        self.dashboard = QLabel("Dashboard")
        self.dashboard.setStyleSheet("font-size:28px;")

        self.server_lists_view = ServerListsView()
        self.servers_view = ServersView()
        self.audit_log_view = AuditLogView()

        # 👇 USERS VIEW (usa SSH shared)
        self.users_view = UsersView(self.ssh_service)

        self.pages.addWidget(self.dashboard)           # 0
        self.pages.addWidget(self.server_lists_view)  # 1
        self.pages.addWidget(self.servers_view)       # 2
        self.pages.addWidget(self.audit_log_view)     # 3
        self.pages.addWidget(self.users_view)         # 4

        # ==========================
        # LAYOUT
        # ==========================
        layout.addWidget(menu_widget)
        layout.addWidget(self.pages)

        # ==========================
        # NAVIGATION
        # ==========================
        self.btn_dashboard.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        self.btn_listas.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        self.btn_servidores.clicked.connect(lambda: self.pages.setCurrentIndex(2))
        self.btn_bitacora.clicked.connect(lambda: self.pages.setCurrentIndex(3))
        self.btn_usuarios.clicked.connect(lambda: self.pages.setCurrentIndex(4))

        # ==========================
        # DEFAULT VIEW
        # ==========================
        self.pages.setCurrentIndex(0)