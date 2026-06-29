from PySide6.QtWidgets import QApplication
from app.ui.login_window import LoginWindow
from app.database.database import run_migrations
import sys

if __name__ == "__main__":
    run_migrations()
    app = QApplication(sys.argv)

    window = LoginWindow()
    window.show()

    sys.exit(app.exec())