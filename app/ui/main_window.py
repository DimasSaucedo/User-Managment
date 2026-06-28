from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget
)

from app.ui.views.server_lists_view import ServerListsView
from app.ui.views.servers_view import ServersView
from app.ui.audit_log_view import AuditLogView
from app.ui.views.multi_users_view import MultiUsersView  # ← nueva vista


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ServerAdmin")
        self.resize(1400, 800)
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        # --- MENU ---
        menu = QVBoxLayout()
        titulo = QLabel("ServerAdmin")
        titulo.setStyleSheet("font-size:20px; font-weight:bold;")

        self.btn_dashboard    = QPushButton("Dashboard")
        self.btn_listas       = QPushButton("Listas")
        self.btn_servidores   = QPushButton("Servidores")
        self.btn_usuarios     = QPushButton("Usuarios")
        self.btn_operaciones  = QPushButton("Operaciones")
        self.btn_bitacora     = QPushButton("Bitácora")
        self.btn_configuracion= QPushButton("Configuración")

        for w in [titulo, self.btn_dashboard, self.btn_listas,
                  self.btn_servidores, self.btn_usuarios,
                  self.btn_operaciones, self.btn_bitacora,
                  self.btn_configuracion]:
            menu.addWidget(w)
        menu.addStretch()

        menu_widget = QWidget()
        menu_widget.setLayout(menu)
        menu_widget.setFixedWidth(220)

        # --- PAGES ---
        self.pages = QStackedWidget()

        self.dashboard         = QLabel("Dashboard")
        self.server_lists_view = ServerListsView()
        self.servers_view      = ServersView()
        self.audit_log_view    = AuditLogView()
        self.users_view        = MultiUsersView()   # ← multi-servidor

        self.pages.addWidget(self.dashboard)           # 0
        self.pages.addWidget(self.server_lists_view)   # 1
        self.pages.addWidget(self.servers_view)        # 2
        self.pages.addWidget(self.audit_log_view)      # 3
        self.pages.addWidget(self.users_view)          # 4

        layout.addWidget(menu_widget)
        layout.addWidget(self.pages)

        # --- NAVEGACIÓN ---
        self.btn_dashboard.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        self.btn_listas.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        self.btn_servidores.clicked.connect(lambda: self.pages.setCurrentIndex(2))
        self.btn_bitacora.clicked.connect(lambda: self.pages.setCurrentIndex(3))
        self.btn_usuarios.clicked.connect(lambda: self.pages.setCurrentIndex(4))

        self.pages.setCurrentIndex(0)