from PySide6.QtWidgets import QApplication
from app.ui.login_window import LoginWindow
# from app.database.init_db import init_db
import sys

if __name__ == "__main__":
    # init_db()
    app = QApplication(sys.argv)

    window = LoginWindow()
    window.show()

    sys.exit(app.exec())