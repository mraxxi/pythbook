import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QDateEdit,
                             QComboBox, QMessageBox, QStatusBar, QFormLayout,
                             QApplication, QDialog)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QDoubleValidator
from datetime import date

from database.db_handler import (get_sqlite_session, get_postgres_session,
                                 add_transaction_local, add_transaction_postgres,
                                 get_unsynced_transactions_local, mark_transaction_as_synced_local,
                                 initialize_postgres_engine)  # Ensure this can be called to re-init
from .settings_dialog import SettingsDialog
from config.config_manager import load_config, save_config


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bookkeeping Transaction Input v1.0.0")
        self.setGeometry(100, 100, 500, 400)  # x, y, width, height

        self.config = load_config()

        self.init_ui()
        self.check_postgres_connection_status()

    def init_ui(self):
        # Central Widget and Layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Form Layout for Inputs
        form_layout = QFormLayout()

        self.date_edit = QDateEdit(self)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form_layout.addRow("Date:", self.date_edit)

        self.amount_edit = QLineEdit(self)
        self.amount_edit.setPlaceholderText("0.00")
        self.amount_edit.setValidator(QDoubleValidator(0.00, 1000000000.00, 2))  # Amount validation
        form_layout.addRow("Amount:", self.amount_edit)

        self.category_combo = QComboBox(self)
        self.category_combo.addItems(self.config.get("categories", ["Other"]))
        form_layout.addRow("Category:", self.category_combo)

        self.description_edit = QLineEdit(self)
        self.description_edit.setPlaceholderText("Transaction details")
        form_layout.addRow("Description:", self.description_edit)

        self.payment_method_combo = QComboBox(self)
        self.payment_method_combo.addItems(self.config.get("payment_methods", ["Other"]))
        form_layout.addRow("Payment Method:", self.payment_method_combo)

        main_layout.addLayout(form_layout)

        # Buttons Layout
        button_layout = QHBoxLayout()
        self.submit_button = QPushButton("Submit (Online)", self)
        self.submit_button.clicked.connect(self.submit_transaction)
        button_layout.addWidget(self.submit_button)

        self.save_offline_button = QPushButton("Save Offline", self)
        self.save_offline_button.clicked.connect(self.save_transaction_offline)
        button_layout.addWidget(self.save_offline_button)

        self.sync_button = QPushButton("Sync Offline Data", self)
        self.sync_button.clicked.connect(self.sync_transactions)
        button_layout.addWidget(self.sync_button)

        self.clear_button = QPushButton("Clear Form", self)
        self.clear_button.clicked.connect(self.clear_form)
        button_layout.addWidget(self.clear_button)

        main_layout.addLayout(button_layout)

        # Status Bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

        # Menu Bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')

        settings_action = file_menu.addAction('&Settings')
        settings_action.triggered.connect(self.open_settings)

        exit_action = file_menu.addAction('&Exit')
        exit_action.triggered.connect(self.close)

    def check_postgres_connection_status(self):
        if initialize_postgres_engine():
            self.statusBar.showMessage("PostgreSQL connected.", 5000)
            self.submit_button.setEnabled(True)
            self.sync_button.setEnabled(True)
        else:
            self.statusBar.showMessage("PostgreSQL connection failed. Check settings. Online features disabled.", 5000)
            self.submit_button.setEnabled(False)
            self.sync_button.setEnabled(False)

    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec_():  # Show dialog modally
            self.config = load_config()  # Reload config after save
            # Update UI elements that depend on config, like categories
            self.category_combo.clear()
            self.category_combo.addItems(self.config.get("categories", ["Other"]))
            self.payment_method_combo.clear()
            self.payment_method_combo.addItems(self.config.get("payment_methods", ["Other"]))
            self.statusBar.showMessage("Settings updated. Re-checking PostgreSQL connection...", 3000)
            self.check_postgres_connection_status()

    def validate_inputs(self):
        if not self.amount_edit.text() or float(self.amount_edit.text()) <= 0:
            QMessageBox.warning(self, "Validation Error", "Amount must be greater than zero.")
            return False
        if not self.category_combo.currentText():
            QMessageBox.warning(self, "Validation Error", "Category cannot be empty.")
            return False
        # Add more validations as needed
        return True

    def get_transaction_data_from_form(self):
        return {
            "date": self.date_edit.date().toPyDate(),
            "amount": float(self.amount_edit.text()),
            "category": self.category_combo.currentText(),
            "description": self.description_edit.text(),
            "payment_method": self.payment_method_combo.currentText()
        }

    def clear_form(self):
        self.date_edit.setDate(QDate.currentDate())
        self.amount_edit.clear()
        self.category_combo.setCurrentIndex(0)  # Or -1 for no selection if allow_empty
        self.description_edit.clear()
        self.payment_method_combo.setCurrentIndex(0)
        self.statusBar.showMessage("Form cleared.", 2000)

    def submit_transaction(self):
        if not self.validate_inputs():
            return

        transaction_data = self.get_transaction_data_from_form()

        try:
            pg_session = get_postgres_session()  # This will raise ConnectionError if not connected
            add_transaction_postgres(pg_session, transaction_data)

            # Optionally, also save to local as synced
            # transaction_data['is_synced'] = True
            # sqlite_session = get_sqlite_session()
            # add_transaction_local(sqlite_session, transaction_data)
            # sqlite_session.close()

            pg_session.close()
            self.statusBar.showMessage("Transaction submitted to PostgreSQL successfully!", 5000)
            QMessageBox.information(self, "Success", "Transaction submitted online.")
            self.clear_form()
        except ConnectionError as e:
            self.statusBar.showMessage(f"PostgreSQL Error: {e}. Try saving offline.", 10000)
            QMessageBox.critical(self, "Online Submission Failed",
                                 f"Could not connect to PostgreSQL: {e}\nPlease save offline or check your settings.")
            self.submit_button.setEnabled(False)  # Disable until connection is restored/checked
        except Exception as e:
            self.statusBar.showMessage(f"Error submitting transaction: {e}", 5000)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")

    def save_transaction_offline(self):
        if not self.validate_inputs():
            return

        transaction_data = self.get_transaction_data_from_form()
        transaction_data['is_synced'] = False  # Explicitly mark as not synced

        try:
            db = get_sqlite_session()
            add_transaction_local(db, transaction_data)
            db.close()
            self.statusBar.showMessage("Transaction saved offline.", 5000)
            QMessageBox.information(self, "Success", "Transaction saved for offline sync.")
            self.clear_form()
        except Exception as e:
            self.statusBar.showMessage(f"Error saving offline: {e}", 5000)
            QMessageBox.critical(self, "Error", f"Could not save transaction offline: {e}")

    def sync_transactions(self):
        self.statusBar.showMessage("Starting sync...", 2000)
        try:
            sqlite_db = get_sqlite_session()
            postgres_db = get_postgres_session()  # Will raise error if no connection

            unsynced_txns = get_unsynced_transactions_local(sqlite_db)
            if not unsynced_txns:
                self.statusBar.showMessage("No transactions to sync.", 5000)
                QMessageBox.information(self, "Sync", "No offline transactions to sync.")
                sqlite_db.close()
                postgres_db.close()
                return

            synced_count = 0
            failed_count = 0
            for txn in unsynced_txns:
                try:
                    transaction_data = {
                        "date": txn.date,
                        "amount": txn.amount,
                        "category": txn.category,
                        "description": txn.description,
                        "payment_method": txn.payment_method
                        # is_synced is not needed for the postgres record directly
                    }
                    add_transaction_postgres(postgres_db, transaction_data)
                    mark_transaction_as_synced_local(sqlite_db, txn.id)
                    synced_count += 1
                except Exception as e:
                    failed_count += 1
                    print(f"Failed to sync transaction ID {txn.id}: {e}")
                    # Optionally, log this error more formally

            sqlite_db.close()
            postgres_db.close()

            summary_message = f"Sync complete. Synced: {synced_count}, Failed: {failed_count}."
            self.statusBar.showMessage(summary_message, 10000)
            QMessageBox.information(self, "Sync Complete", summary_message)

        except ConnectionError as e:
            self.statusBar.showMessage(f"PostgreSQL connection error during sync: {e}", 10000)
            QMessageBox.critical(self, "Sync Error", f"Could not connect to PostgreSQL for sync: {e}")
            self.sync_button.setEnabled(False)  # Disable until connection restored
        except Exception as e:
            self.statusBar.showMessage(f"Error during sync: {e}", 10000)
            QMessageBox.critical(self, "Sync Error", f"An unexpected error occurred during sync: {e}")