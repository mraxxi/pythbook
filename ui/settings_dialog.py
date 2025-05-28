from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QPushButton, QDialogButtonBox, QLabel, QSpinBox,
                             QPlainTextEdit)
from config.config_manager import load_config, save_config, DEFAULT_CONFIG


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Settings")
        self.config = load_config()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # PostgreSQL Settings
        pg_config = self.config.get("postgres", DEFAULT_CONFIG["postgres"])
        self.pg_host_edit = QLineEdit(pg_config.get("host"))
        form_layout.addRow("PostgreSQL Host:", self.pg_host_edit)

        self.pg_port_edit = QSpinBox()
        self.pg_port_edit.setRange(1, 65535)
        self.pg_port_edit.setValue(int(pg_config.get("port", 5432)))
        form_layout.addRow("PostgreSQL Port:", self.pg_port_edit)

        self.pg_db_edit = QLineEdit(pg_config.get("database"))
        form_layout.addRow("PostgreSQL Database:", self.pg_db_edit)

        self.pg_user_edit = QLineEdit(pg_config.get("user"))
        form_layout.addRow("PostgreSQL User:", self.pg_user_edit)

        self.pg_pass_edit = QLineEdit(pg_config.get("password"))
        self.pg_pass_edit.setEchoMode(QLineEdit.Password)
        form_layout.addRow("PostgreSQL Password:", self.pg_pass_edit)

        layout.addWidget(QLabel("<b>PostgreSQL Connection:</b>"))
        layout.addLayout(form_layout)

        # Categories and Payment Methods
        layout.addWidget(QLabel("<b>Transaction Categories (one per line):</b>"))
        self.categories_edit = QPlainTextEdit()
        self.categories_edit.setPlainText("\n".join(self.config.get("categories", DEFAULT_CONFIG["categories"])))
        layout.addWidget(self.categories_edit)

        layout.addWidget(QLabel("<b>Payment Methods (one per line):</b>"))
        self.payment_methods_edit = QPlainTextEdit()
        self.payment_methods_edit.setPlainText(
            "\n".join(self.config.get("payment_methods", DEFAULT_CONFIG["payment_methods"])))
        layout.addWidget(self.payment_methods_edit)

        # Dialog Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept_settings)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept_settings(self):
        self.config["postgres"]["host"] = self.pg_host_edit.text()
        self.config["postgres"]["port"] = self.pg_port_edit.value()
        self.config["postgres"]["database"] = self.pg_db_edit.text()
        self.config["postgres"]["user"] = self.pg_user_edit.text()
        self.config["postgres"]["password"] = self.pg_pass_edit.text()

        categories = [line.strip() for line in self.categories_edit.toPlainText().splitlines() if line.strip()]
        self.config["categories"] = categories if categories else DEFAULT_CONFIG["categories"]

        payment_methods = [line.strip() for line in self.payment_methods_edit.toPlainText().splitlines() if
                           line.strip()]
        self.config["payment_methods"] = payment_methods if payment_methods else DEFAULT_CONFIG["payment_methods"]

        save_config(self.config)
        self.accept()  # Closes the dialog with QDialog.Accepted