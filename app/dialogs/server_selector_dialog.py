from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QScrollArea, QWidget, QGroupBox,
    QRadioButton, QButtonGroup, QFrame, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt


class ServerCredWidget(QFrame):
    """Fila con checkbox de servidor + campos usuario/password."""

    def __init__(self, server, parent=None):
        super().__init__(parent)
        self.server = server
        self.setFrameShape(QFrame.StyledPanel)

        layout = QGridLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)

        self.check = QCheckBox(f"{server.nombre}  [{server.ip}:{server.puerto}]")
        self.check.setChecked(True)
        layout.addWidget(self.check, 0, 0, 1, 4)

        self.lbl_user = QLabel("Usuario:")
        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText("usuario")
        self.user_edit.setFixedWidth(130)

        self.lbl_pass = QLabel("Password:")
        self.pass_edit = QLineEdit()
        self.pass_edit.setEchoMode(QLineEdit.Password)
        self.pass_edit.setPlaceholderText("••••••")
        self.pass_edit.setFixedWidth(130)

        layout.addWidget(self.lbl_user, 1, 0)
        layout.addWidget(self.user_edit, 1, 1)
        layout.addWidget(self.lbl_pass, 1, 2)
        layout.addWidget(self.pass_edit, 1, 3)

        self.check.toggled.connect(self._toggle_creds)

    def _toggle_creds(self, checked):
        for w in [self.lbl_user, self.user_edit, self.lbl_pass, self.pass_edit]:
            w.setEnabled(checked)

    def set_global_creds(self, user, password):
        self.user_edit.setText(user)
        self.pass_edit.setText(password)

    def is_selected(self):
        return self.check.isChecked()

    def get_creds(self):
        return self.user_edit.text().strip(), self.pass_edit.text()


class ServerSelectorDialog(QDialog):
    """
    Muestra lista de servidores con opción de:
    - Credenciales globales (mismas para todos)
    - Credenciales individuales por servidor
    """

    def __init__(self, servers, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Servidores")
        self.setMinimumWidth(520)
        self.setMinimumHeight(480)

        self._server_widgets: list[ServerCredWidget] = []
        self._build_ui(servers)

    def _build_ui(self, servers):
        layout = QVBoxLayout(self)

        # --- Modo credenciales ---
        mode_box = QGroupBox("Credenciales")
        mode_layout = QVBoxLayout(mode_box)

        self.radio_global = QRadioButton("Mismas para todos")
        self.radio_individual = QRadioButton("Individuales por servidor")
        self.radio_global.setChecked(True)

        btn_group = QButtonGroup(self)
        btn_group.addButton(self.radio_global)
        btn_group.addButton(self.radio_individual)

        mode_layout.addWidget(self.radio_global)
        mode_layout.addWidget(self.radio_individual)

        # Campos globales
        global_frame = QFrame()
        gf_layout = QGridLayout(global_frame)
        gf_layout.setContentsMargins(0, 4, 0, 0)
        gf_layout.addWidget(QLabel("Usuario:"), 0, 0)
        self.global_user = QLineEdit()
        self.global_user.setPlaceholderText("usuario")
        gf_layout.addWidget(self.global_user, 0, 1)
        gf_layout.addWidget(QLabel("Password:"), 1, 0)
        self.global_pass = QLineEdit()
        self.global_pass.setEchoMode(QLineEdit.Password)
        gf_layout.addWidget(self.global_pass, 1, 1)

        btn_apply = QPushButton("Aplicar a seleccionados")
        btn_apply.clicked.connect(self._apply_global)
        gf_layout.addWidget(btn_apply, 2, 0, 1, 2)

        mode_layout.addWidget(global_frame)
        layout.addWidget(mode_box)

        self.radio_global.toggled.connect(
            lambda checked: global_frame.setVisible(checked)
        )
        self.radio_individual.toggled.connect(
            lambda checked: global_frame.setVisible(not checked)
        )

        # --- Lista de servidores ---
        layout.addWidget(QLabel("Servidores:"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(4)

        for server in servers:
            w = ServerCredWidget(server)
            # en modo global, ocultar campos individuales
            self.radio_global.toggled.connect(
                lambda checked, widget=w: self._toggle_individual(widget, checked)
            )
            self._toggle_individual(w, True)  # iniciar ocultos
            self._server_widgets.append(w)
            container_layout.addWidget(w)

        container_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

        # --- Botones ---
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Conectar")
        btn_cancel = QPushButton("Cancelar")
        btn_ok.setDefault(True)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

    def _toggle_individual(self, widget: ServerCredWidget, global_mode: bool):
        for w in [widget.lbl_user, widget.user_edit, widget.lbl_pass, widget.pass_edit]:
            w.setVisible(not global_mode)

    def _apply_global(self):
        user = self.global_user.text().strip()
        password = self.global_pass.text()
        for w in self._server_widgets:
            if w.is_selected():
                w.set_global_creds(user, password)

    def get_selected(self) -> list[dict]:
        """
        Retorna lista de dicts:
        {"server": Server, "username": str, "password": str}
        """
        result = []
        global_mode = self.radio_global.isChecked()
        global_user = self.global_user.text().strip()
        global_pass = self.global_pass.text()

        for w in self._server_widgets:
            if not w.is_selected():
                continue
            if global_mode:
                user, password = global_user, global_pass
            else:
                user, password = w.get_creds()

            if user:
                result.append({
                    "server": w.server,
                    "username": user,
                    "password": password
                })

        return result