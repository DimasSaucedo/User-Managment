from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QMessageBox
)

from app.dialogs.server_list_dialog import ServerListDialog
from app.repositories.server_list_repository import ServerListRepository


class ServerListsView(QWidget):

    def __init__(self):
        super().__init__()

        self.repo = ServerListRepository()

        layout = QVBoxLayout(self)

        titulo = QLabel("Listas de Servidores")
        titulo.setStyleSheet("font-size:22px;font-weight:bold;")

        botones = QHBoxLayout()

        self.btn_nuevo = QPushButton("Nuevo")
        self.btn_editar = QPushButton("Editar")
        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_actualizar = QPushButton("Actualizar")

        botones.addWidget(self.btn_nuevo)
        botones.addWidget(self.btn_editar)
        botones.addWidget(self.btn_eliminar)
        botones.addStretch()
        botones.addWidget(self.btn_actualizar)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            "ID",
            "Nombre",
            "Descripción"
        ])

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addWidget(titulo)
        layout.addLayout(botones)
        layout.addWidget(self.table)

        # Eventos
        self.btn_nuevo.clicked.connect(self.nueva_lista)
        self.btn_editar.clicked.connect(self.editar_lista)
        self.btn_eliminar.clicked.connect(self.eliminar_lista)
        self.btn_actualizar.clicked.connect(self.cargar_datos)

        self.cargar_datos()

    def cargar_datos(self):

        datos = self.repo.get_all()

        self.table.setRowCount(len(datos))

        for fila, item in enumerate(datos):

            self.table.setItem(
                fila,
                0,
                QTableWidgetItem(str(item.id))
            )

            self.table.setItem(
                fila,
                1,
                QTableWidgetItem(item.nombre)
            )

            self.table.setItem(
                fila,
                2,
                QTableWidgetItem(item.descripcion or "")
            )

        self.table.resizeColumnsToContents()

    def nueva_lista(self):

        dialog = ServerListDialog(self)

        if dialog.exec():

            nombre = dialog.nombre.text().strip()
            descripcion = dialog.descripcion.toPlainText().strip()

            if not nombre:

                QMessageBox.warning(
                    self,
                    "Error",
                    "El nombre es obligatorio."
                )

                return

            self.repo.create(nombre, descripcion)

            self.cargar_datos()

    def editar_lista(self):

        fila = self.table.currentRow()

        if fila < 0:

            QMessageBox.warning(
                self,
                "Error",
                "Seleccione una lista."
            )

            return

        id_lista = int(self.table.item(fila, 0).text())

        lista = self.repo.get_by_id(id_lista)

        dialog = ServerListDialog(
            self,
            lista.nombre,
            lista.descripcion or ""
        )

        if dialog.exec():

            self.repo.update(
                id_lista,
                dialog.nombre.text().strip(),
                dialog.descripcion.toPlainText().strip()
            )

            self.cargar_datos()

    def eliminar_lista(self):

        fila = self.table.currentRow()

        if fila < 0:

            QMessageBox.warning(
                self,
                "Error",
                "Seleccione una lista."
            )

            return

        id_lista = int(self.table.item(fila, 0).text())

        respuesta = QMessageBox.question(
            self,
            "Eliminar",
            "¿Desea eliminar la lista seleccionada?"
        )

        if respuesta == QMessageBox.Yes:

            self.repo.delete(id_lista)

            self.cargar_datos()