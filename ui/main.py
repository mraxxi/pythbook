import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
# Ensure other modules are importable - depends on how you run it.
# If running from bookkeeping_app/ directory:
# from .ui.main_window import MainWindow (if main.py is outside bookkeeping_app)

def main():
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()