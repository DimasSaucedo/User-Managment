from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QInputDialog,
    QMessageBox
)

from app.controllers.users_controller import UsersController


class UsersView(QWidget):

    def __init__(self, ssh_service):
        super().__init__()

        self.controller = UsersController(ssh_service)

        self.setWindowTitle("Usuarios del Sistema")

        self.layout = QVBoxLayout()

        # =========================
        # HEADER
        # =========================
        header = QHBoxLayout()

        self.title = QLabel("Gestión de Usuarios")
        self.refresh_btn = QPushButton("Refrescar")

        header.addWidget(self.title)
        header.addStretch()
        header.addWidget(self.refresh_btn)

        self.layout.addLayout(header)

        # =========================
        # TABLE
        # =========================
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Usuario", "UID", "GID", "Home", "Shell"
        ])

        self.layout.addWidget(self.table)

        # =========================
        # ACTION BUTTONS
        # =========================
        actions = QHBoxLayout()

        self.btn_groups = QPushButton("Ver Grupos")
        self.btn_add_group = QPushButton("Agregar a Grupo")
        self.btn_delete = QPushButton("Eliminar Usuario")

        actions.addWidget(self.btn_groups)
        actions.addWidget(self.btn_add_group)
        actions.addWidget(self.btn_delete)

        self.layout.addLayout(actions)

        self.setLayout(self.layout)

        # =========================
        # EVENTS
        # =========================
        self.refresh_btn.clicked.connect(self.load_users)
        self.btn_groups.clicked.connect(self.show_groups)
        self.btn_add_group.clicked.connect(self.add_to_group)
        self.btn_delete.clicked.connect(self.delete_user)

        self.load_users()

    # =========================
    # LOAD USERS
    # =========================
    def load_users(self):

        users = self.controller.get_users()

        self.table.setRowCount(len(users))

        for row, user in enumerate(users):
            self.table.setItem(row, 0, QTableWidgetItem(user["username"]))
            self.table.setItem(row, 1, QTableWidgetItem(user["uid"]))
            self.table.setItem(row, 2, QTableWidgetItem(user["gid"]))
            self.table.setItem(row, 3, QTableWidgetItem(user["home"]))
            self.table.setItem(row, 4, QTableWidgetItem(user["shell"]))

    # =========================
    # GET SELECTED USER
    # =========================
    def get_selected_user(self):

        row = self.table.currentRow()

        if row < 0:
            return None

        return self.table.item(row, 0).text()

    # =========================
    # SHOW GROUPS
    # =========================
    def show_groups(self):

        user = self.get_selected_user()
        if not user:
            QMessageBox.warning(self, "Error", "Selecciona un usuario")
            return

        groups = self.controller.get_groups(user)

        QMessageBox.information(
            self,
            "Grupos",
            f"{user} pertenece a:\n\n" + ", ".join(groups)
        )

    # =========================
    # ADD TO GROUP
    # =========================
    def add_to_group(self):

        user = self.get_selected_user()
        if not user:
            QMessageBox.warning(self, "Error", "Selecciona un usuario")
            return

        group, ok = QInputDialog.getText(self, "Grupo", "Nombre del grupo:")

        if ok and group:

            success, msg = self.controller.add_to_group(user, group)

            if success:
                QMessageBox.information(self, "OK", "Usuario agregado al grupo")
            else:
                QMessageBox.critical(self, "Error", msg)

    # =========================
    # DELETE USER
    # =========================
    def delete_user(self):

        user = self.get_selected_user()
        if not user:
            QMessageBox.warning(self, "Error", "Selecciona un usuario")
            return

        confirm = QMessageBox.question(
            self,
            "Confirmar",
            f"¿Eliminar usuario {user}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:

            success, msg = self.controller.delete_user(user)

            if success:
                QMessageBox.information(self, "OK", "Usuario eliminado")
                self.load_users()
            else:
                QMessageBox.critical(self, "Error", msg)