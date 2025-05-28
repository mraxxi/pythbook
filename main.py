import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow

import logging.config
import os
from config.constants import LOGGING_CONFIG_FILE

# Construct the path to logging.conf relative to the current file or project root
# Assuming main.py is at project root and logging.conf is also at project root or in config/
#log_conf_path = os.path.join(os.path.dirname(__file__), LOGGING_CONFIG_FILE) # Adjust if LOGGING_CONFIG_FILE path is different
#if os.path.exists(log_conf_path):
#    logging.config.fileConfig(log_conf_path)
#else:
#    # Basic fallback logging if a config file not found
#    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#    logging.warning(f"Logging configuration file '{log_conf_path}' not found. Using basicConfig.")

# Get specific loggers
# logger = logging.getLogger('app_logger') # In main_window.py
# db_logger = logging.getLogger('db_logger') # In db_handler.py

# Ensure other modules are importable - depends on how you run it.
# If running from bookkeeping_app/ directory:
# from .ui.main_window import MainWindow (if main.py is outside bookkeeping_app)

# with open("ui/resources/stylesheets/style.qss", "r") as f:
#    app.setStyleSheet(f.read())


def main():
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()