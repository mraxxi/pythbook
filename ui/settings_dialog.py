# ui/settings_dialog.py
"""
Configuration dialog for application settings, primarily database connections.
Extends QDialog.
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QPushButton, QDialogButtonBox, QLabel, QSpinBox,
                             QGroupBox, QFileDialog, QHBoxLayout, QPlainTextEdit)  # Added QPlainTextEdit
from PyQt5.QtCore import Qt

from config.config_manager import load_config, save_config, DEFAULT_CONFIG
from config.constants import POSTGRES_DEFAULT_PORT  # Using constant


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Settings")
        self.setMinimumWidth(450)
        self.config_data = load_config()  # Load current config to populate fields
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # --- PostgreSQL Settings Group ---
        pg_group = QGroupBox("PostgreSQL Connection")
        pg_layout = QFormLayout()

        pg_current_config = self.config_data.get("postgres", DEFAULT_CONFIG["postgres"])
        self.pg_host_edit = QLineEdit(pg_current_config.get("host"))
        pg_layout.addRow("Host:", self.pg_host_edit)

        self.pg_port_edit = QSpinBox()
        self.pg_port_edit.setRange(1, 65535)
        self.pg_port_edit.setValue(int(pg_current_config.get("port", POSTGRES_DEFAULT_PORT)))
        pg_layout.addRow("Port:", self.pg_port_edit)

        self.pg_db_edit = QLineEdit(pg_current_config.get("database"))
        pg_layout.addRow("Database Name:", self.pg_db_edit)

        self.pg_user_edit = QLineEdit(pg_current_config.get("user"))
        pg_layout.addRow("User:", self.pg_user_edit)

        self.pg_pass_edit = QLineEdit(pg_current_config.get("password"))
        self.pg_pass_edit.setEchoMode(QLineEdit.Password)
        pg_layout.addRow("Password:", self.pg_pass_edit)

        pg_group.setLayout(pg_layout)
        main_layout.addWidget(pg_group)

        # --- PDF Output Directory ---
        pdf_group = QGroupBox("File Settings")
        pdf_layout = QFormLayout()

        self.pdf_dir_edit = QLineEdit(
            self.config_data.get("pdf_output_directory", DEFAULT_CONFIG["pdf_output_directory"]))
        self.pdf_dir_edit.setReadOnly(True)  # Display only, change via button

        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._browse_pdf_directory)

        pdf_dir_layout = QHBoxLayout()
        pdf_dir_layout.addWidget(self.pdf_dir_edit, 1)
        pdf_dir_layout.addWidget(browse_button)
        pdf_layout.addRow("Default PDF Output Directory:", pdf_dir_layout)

        pdf_group.setLayout(pdf_layout)
        main_layout.addWidget(pdf_group)

        # --- Company Details for PDF ---
        company_group = QGroupBox("Company Details (for PDF Header)")
        company_layout = QFormLayout()
        company_conf = self.config_data.get("company_details", DEFAULT_CONFIG.get("company_details", {}))

        self.company_name_edit = QLineEdit(company_conf.get("name", ""))
        company_layout.addRow("Company Name:", self.company_name_edit)
        self.company_addr1_edit = QLineEdit(company_conf.get("address_line1", ""))
        company_layout.addRow("Address Line 1:", self.company_addr1_edit)
        self.company_addr2_edit = QLineEdit(company_conf.get("address_line2", ""))
        company_layout.addRow("Address Line 2:", self.company_addr2_edit)
        self.company_contact_edit = QLineEdit(company_conf.get("contact", ""))
        company_layout.addRow("Contact Info (Phone/Email):", self.company_contact_edit)
        # Optional: Logo path
        # self.company_logo_edit = QLineEdit(company_conf.get("logo_path", "")) (add browse button)
        # company_layout.addRow("Logo Path:", self.company_logo_edit)

        company_group.setLayout(company_layout)
        main_layout.addWidget(company_group)

        # --- Dialog Buttons (Save, Cancel) ---
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._save_and_accept)
        button_box.rejected.connect(self.reject)  # QDialog's built-in reject
        main_layout.addWidget(button_box)

    def _browse_pdf_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select PDF Output Directory",
            self.pdf_dir_edit.text()  # Start from current directory if set
        )
        if directory:
            self.pdf_dir_edit.setText(directory)

    def _save_and_accept(self):
        """Collects data from UI, saves it to config, then accepts the dialog."""
        # Update PostgreSQL config
        self.config_data["postgres"]["host"] = self.pg_host_edit.text()
        self.config_data["postgres"]["port"] = self.pg_port_edit.value()
        self.config_data["postgres"]["database"] = self.pg_db_edit.text()
        self.config_data["postgres"]["user"] = self.pg_user_edit.text()
        self.config_data["postgres"][
            "password"] = self.pg_pass_edit.text()  # Consider security for password storage/handling

        # Update PDF output directory
        self.config_data["pdf_output_directory"] = self.pdf_dir_edit.text()

        # Update Company Details
        if "company_details" not in self.config_data: self.config_data["company_details"] = {}
        self.config_data["company_details"]["name"] = self.company_name_edit.text()
        self.config_data["company_details"]["address_line1"] = self.company_addr1_edit.text()
        self.config_data["company_details"]["address_line2"] = self.company_addr2_edit.text()
        self.config_data["company_details"]["contact"] = self.company_contact_edit.text()

        save_config(self.config_data)
        self.accept()  # QDialog's built-in accept