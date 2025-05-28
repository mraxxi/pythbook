# main_window.py
"""
Main window and invoice form GUI for the Invoice Generator application.
"""
import sys  # For QApplication if running standalone for testing this file
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QGridLayout, QLabel, QLineEdit, QPushButton,
                             QFrame, QScrollArea, QMessageBox, QFileDialog, QSpinBox,
                             QApplication, QAction, QDoubleSpinBox)  # Added QAction for menu
from PyQt5.QtCore import Qt, pyqtSlot, QSize, pyqtSignal
from PyQt5.QtGui import QFont, QIcon


# Assuming these are your existing, correctly defined classes and modules:
# from models import Invoice, LineItem, InvoiceValidator
# from widgets import LineItemWidget, TotalDisplayWidget
# from pdf_generator import PDFExportManager
# import config
# import utils

# ---- Placeholder for your actual imports ----
# For the sake_of this example, let's create dummy versions or assume they exist
class DummyInvoice:
    def __init__(self, invoice_number="", invoice_date="", customer_name="", customer_address="", line_items=None):
        self.invoice_number = invoice_number
        self.invoice_date = invoice_date
        self.customer_name = customer_name
        self.customer_address = customer_address
        self.line_items = line_items if line_items is not None else []

    @staticmethod
    def create_default():
        from datetime import date
        return DummyInvoice(invoice_number=f"INV-{date.today().strftime('%Y%m%d')}-001",
                            invoice_date=date.today().strftime("%Y-%m-%d"))


class DummyLineItem:
    def __init__(self, number=1, description="", amount=1, price=0):  # amount is qty
        self.number = number
        self.description = description
        self.amount = amount  # This is quantity in your context
        self.price = price  # This is unit price

    @property
    def subtotal(self):
        return self.amount * self.price


class DummyInvoiceValidator:
    @staticmethod
    def validate_invoice(invoice):  # invoice is DummyInvoice instance
        errors = []
        if not invoice.invoice_number: errors.append("Invoice number is missing.")
        if not invoice.invoice_date: errors.append("Invoice date is missing.")
        # Basic check for customer name
        if not invoice.customer_name: errors.append("Customer name is missing.")
        if not invoice.line_items: errors.append("At least one line item is required.")
        for i, item in enumerate(invoice.line_items):
            if not item.description: errors.append(f"Line item #{i + 1}: Description is missing.")
            if item.amount <= 0: errors.append(f"Line item #{i + 1}: Quantity must be positive.")
            if item.price < 0: errors.append(f"Line item #{i + 1}: Price cannot be negative.")
        return errors


class DummyLineItemWidget(QWidget):  # Basic placeholder
    data_changed = pyqtSignal()
    delete_requested = pyqtSignal(object)

    def __init__(self, parent_form, line_item_model):
        super().__init__(parent_form)
        self.model = line_item_model
        layout = QHBoxLayout(self)
        self.desc_edit = QLineEdit(self.model.description)
        self.qty_edit = QLineEdit(str(self.model.amount))
        self.price_edit = QLineEdit(str(self.model.price))
        layout.addWidget(QLabel(str(self.model.number)))
        layout.addWidget(self.desc_edit)
        layout.addWidget(self.qty_edit)
        layout.addWidget(self.price_edit)
        # ... more setup ...

    def get_line_item(self):  # Ensure this returns data compatible with LineItemDB mapping
        self.model.description = self.desc_edit.text()
        self.model.amount = int(self.qty_edit.text()) if self.qty_edit.text().isdigit() else 1
        self.model.price = float(self.price_edit.text()) if self.price_edit.text() else 0
        return self.model

    def focus_first_empty_field(self): self.desc_edit.setFocus()

    def set_number(self, num): self.model.number = num  # Update label too


class DummyPDFManager:
    def export_and_open(self, invoice, filename):
        print(f"PDF for {invoice.invoice_number} would be saved to {filename}")
        return True, f"PDF '{filename}' generated (simulated)."


class DummyUtils:
    @staticmethod
    def format_currency(amount): return f"Rp {amount:,.2f}"

    @staticmethod
    def format_validation_errors(errors): return "\n- ".join(errors)

    class FileManager:
        @staticmethod
        def get_default_invoice_filename(inv_num): return f"{inv_num}.pdf"

        @staticmethod
        def suggest_save_location(filename): import os; return os.path.join(os.getcwd(), filename)


# Replace dummy classes with your actual imports
Invoice = DummyInvoice
LineItem = DummyLineItem
InvoiceValidator = DummyInvoiceValidator
LineItemWidget = DummyLineItemWidget  # You'll use your actual LineItemWidget
PDFExportManager = DummyPDFManager


# Assuming 'config' has APP_NAME, APP_VERSION etc.
class DummyConfig:
    CURRENCY_SYMBOL = "Rp"
    MAX_PRICE = 999999999
    MAX_QUANTITY = 999999999
    MIN_QUANTITY = 1
    APP_NAME = "InvoicePro"
    APP_VERSION = "1.0.1-db"
    WINDOW_MIN_WIDTH = 800
    WINDOW_MIN_HEIGHT = 600
    DEFAULT_QUANTITY = 1
    LINE_ITEM_FIELD_WIDTHS = {'number': 30, 'amount': 70, 'price': 100, 'subtotal': 120, 'delete_btn': 30}


config = DummyConfig
utils = DummyUtils
# ---- End Placeholder ----


# Import database and config parts from our previous work
# Ensure these paths are correct for your project structure
from database.db_handler import (add_invoice_local, add_invoice_postgres,
                                 get_unsynced_invoices_local, mark_invoice_as_synced_local,
                                 initialize_postgres_engine, transfer_invoice_to_postgres, get_postgres_session)
from config.config_manager import load_config as app_load_config  # Renamed to avoid conflict
# from ui.settings_dialog import SettingsDialog # Assuming you have this from previous steps


# --- Placeholder for SettingsDialog ---
from PyQt5.QtWidgets import QDialog, QVBoxLayout as QDVBoxLayout, QDialogButtonBox, QLabel as QTLable


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings (DB Placeholder)")
        layout = QDVBoxLayout(self)
        layout.addWidget(QTLable("Database settings would go here."))
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


# --- End Placeholder for SettingsDialog ---


def _create_line_items_headers() -> QHBoxLayout:  #
    """Create the headers for the line items table."""  #
    headers_layout = QHBoxLayout()  #
    headers = ["#", "Description", "Qty", "Price", "Subtotal", ""]  #
    widths = [  #
        config.LINE_ITEM_FIELD_WIDTHS['number'],  #
        0,  # Description takes remaining space #
        config.LINE_ITEM_FIELD_WIDTHS['amount'],  #
        config.LINE_ITEM_FIELD_WIDTHS['price'],  #
        config.LINE_ITEM_FIELD_WIDTHS['subtotal'],  #
        config.LINE_ITEM_FIELD_WIDTHS['delete_btn']  #
    ]

    for i, header in enumerate(headers):  #
        label = QLabel(header)  #
        label.setAlignment(Qt.AlignCenter)  #

        # Apply bold font to headers #
        font = QFont()  #
        font.setBold(True)  #
        label.setFont(font)  #

        if widths[i] > 0:  #
            label.setFixedWidth(widths[i])  #

        headers_layout.addWidget(label, 1 if widths[i] == 0 else 0)  #

    return headers_layout  #


class InvoiceForm(QWidget):  # Your existing InvoiceForm class
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent  # Store reference to MainWindow for statusbar
        self.line_item_widgets = []
        self.pdf_manager = PDFExportManager()
        self._setup_ui()  # This calls your existing UI setup
        self._load_default_invoice()

    # ... (all your existing _setup_ui, _create_header_section, etc. methods remain unchanged) ...
    # You need to ensure `_create_actions_section` is modified or extended.

    def _setup_ui(self):
        """Initialize the UI components."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Number field (read-only)
        self.number_edit = QLineEdit()
        self.number_edit.setFixedWidth(config.LINE_ITEM_FIELD_WIDTHS['number'])
        self.number_edit.setReadOnly(True)
        self.number_edit.setAlignment(Qt.AlignCenter)

        # Description field
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Item description")

        # Amount field (spinner)
        self.amount_spin = QSpinBox()
        self.amount_spin.setRange(config.MIN_QUANTITY, config.MAX_QUANTITY)
        self.amount_spin.setFixedWidth(config.LINE_ITEM_FIELD_WIDTHS['amount'])

        # Price field
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, config.MAX_PRICE)
        self.price_spin.setPrefix(config.CURRENCY_SYMBOL)
        self.price_spin.setFixedWidth(config.LINE_ITEM_FIELD_WIDTHS['price'])

        # Subtotal field (read-only)
        self.subtotal_edit = QLineEdit()
        self.subtotal_edit.setReadOnly(True)
        self.subtotal_edit.setFixedWidth(config.LINE_ITEM_FIELD_WIDTHS['subtotal'])
        self.subtotal_edit.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Make subtotal field visually distinct
        font = QFont()
        font.setBold(True)
        self.subtotal_edit.setFont(font)

        # Delete button
        self.delete_btn = QPushButton("✕")
        self.delete_btn.setFixedWidth(config.LINE_ITEM_FIELD_WIDTHS['delete_btn'])
        self.delete_btn.setToolTip("Delete this line item")

        # Add all widgets to layout
        layout.addWidget(self.number_edit)
        layout.addWidget(self.desc_edit, 1)  # Description takes remaining space
        layout.addWidget(self.amount_spin)
        layout.addWidget(self.price_spin)
        layout.addWidget(self.subtotal_edit)
        layout.addWidget(self.delete_btn)

        self.setLayout(layout)

    def _create_header_section(self) -> QGridLayout:  #
        """Create the invoice header input section."""  #
        header_layout = QGridLayout()  #

        # Invoice number #
        header_layout.addWidget(QLabel("Invoice #:"), 0, 0)  #
        self.invoice_number = QLineEdit()  #
        header_layout.addWidget(self.invoice_number, 0, 1)  #

        # Invoice date #
        header_layout.addWidget(QLabel("Date:"), 0, 2)  #
        self.invoice_date = QLineEdit()  #
        # TODO: Consider using QDateEdit for better date handling
        header_layout.addWidget(self.invoice_date, 0, 3)  #

        # Customer details #
        header_layout.addWidget(QLabel("Customer:"), 1, 0)  #
        self.customer_name = QLineEdit()  #
        self.customer_name.setPlaceholderText("Customer name")  #
        header_layout.addWidget(self.customer_name, 1, 1)  #

        header_layout.addWidget(QLabel("Address:"), 1, 2)  #
        self.customer_address = QLineEdit()  #
        self.customer_address.setPlaceholderText("Customer address")  #
        header_layout.addWidget(self.customer_address, 1, 3)  #

        return header_layout  #

    def _create_separator(self) -> QFrame:  #
        """Create a horizontal separator line."""  #
        line = QFrame()  #
        line.setFrameShape(QFrame.HLine)  #
        line.setFrameShadow(QFrame.Sunken)  #
        return line  #

    def _create_line_items_section(self) -> QVBoxLayout:  #
        """Create the line items input section."""  #
        line_items_layout = QVBoxLayout()  #

        # Headers #
        line_items_layout.addLayout(_create_line_items_headers())  #

        # Scroll area for line items #
        self.scroll_area = QScrollArea()  #
        self.scroll_area.setWidgetResizable(True)  #
        self.scroll_content = QWidget()  #
        self.items_layout = QVBoxLayout(self.scroll_content)  #
        self.items_layout.setAlignment(Qt.AlignTop)  #
        self.scroll_area.setWidget(self.scroll_content)  #

        line_items_layout.addWidget(self.scroll_area)  #

        # Add button for new line item #
        self.add_item_btn = QPushButton("+ Add Item")  #
        self.add_item_btn.clicked.connect(self.add_line_item)  #
        line_items_layout.addWidget(self.add_item_btn)  #

        return line_items_layout  #

    def _create_total_section(self) -> QHBoxLayout:  #
        """Create the total display section."""  #
        total_layout = QHBoxLayout()  #
        total_layout.addStretch()  #
        total_label = QLabel("Total:")  #
        font = QFont()  #
        font.setBold(True)  #
        total_label.setFont(font)  #
        total_layout.addWidget(total_label)  #
        self.total_display = QLineEdit("Rp 0")  #
        self.total_display.setReadOnly(True)  #
        self.total_display.setFixedWidth(config.LINE_ITEM_FIELD_WIDTHS['subtotal'])  #
        self.total_display.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  #
        font = QFont()  #
        font.setBold(True)  #
        font.setPointSize(font.pointSize() + 1)  #
        self.total_display.setFont(font)  #
        total_layout.addWidget(self.total_display)  #
        placeholder = QWidget()  #
        placeholder.setFixedWidth(config.LINE_ITEM_FIELD_WIDTHS['delete_btn'])  #
        total_layout.addWidget(placeholder)  #
        return total_layout  #

    def _create_actions_section(self) -> QVBoxLayout:  # Modified to QVBoxLayout for more buttons
        """Create the action buttons section, now including DB actions."""
        actions_main_layout = QVBoxLayout()  # Parent layout for rows of buttons

        # Row 1: PDF and Clear buttons (as before)
        pdf_clear_layout = QHBoxLayout()  #
        self.generate_pdf_btn = QPushButton("Generate PDF")  #
        self.generate_pdf_btn.setMinimumWidth(120)  #
        self.generate_pdf_btn.clicked.connect(self.generate_pdf)  #
        pdf_clear_layout.addWidget(self.generate_pdf_btn)  #

        self.clear_form_btn = QPushButton("Clear Form")  #
        self.clear_form_btn.setMinimumWidth(120)  #
        self.clear_form_btn.clicked.connect(self.clear_form)  #
        pdf_clear_layout.addWidget(self.clear_form_btn)  #
        pdf_clear_layout.addStretch()  #
        actions_main_layout.addLayout(pdf_clear_layout)

        # Row 2: Database action buttons
        db_actions_layout = QHBoxLayout()
        self.save_offline_btn = QPushButton("Save Invoice Offline")
        self.save_offline_btn.setMinimumWidth(150)
        self.save_offline_btn.clicked.connect(self.save_invoice_offline_action)
        db_actions_layout.addWidget(self.save_offline_btn)

        self.submit_online_btn = QPushButton("Submit Invoice (Online)")
        self.submit_online_btn.setMinimumWidth(150)
        self.submit_online_btn.clicked.connect(self.submit_invoice_online_action)
        db_actions_layout.addWidget(self.submit_online_btn)

        db_actions_layout.addStretch()
        actions_main_layout.addLayout(db_actions_layout)

        # Row 3: Sync button (optional, could also be in menu)
        sync_layout = QHBoxLayout()
        self.sync_invoices_btn = QPushButton("Sync Offline Invoices")
        self.sync_invoices_btn.setMinimumWidth(150)
        self.sync_invoices_btn.clicked.connect(self.sync_invoices_action)
        sync_layout.addWidget(self.sync_invoices_btn)
        sync_layout.addStretch()
        actions_main_layout.addLayout(sync_layout)

        return actions_main_layout  # (adapted)

    # --- NEW ACTION HANDLERS FOR DB OPERATIONS ---
    def _validate_and_get_invoice(self):
        """Helper to validate form and get invoice data."""
        invoice_gui_data = self.get_invoice_data()  # From your existing method
        # Use your existing InvoiceValidator
        errors = InvoiceValidator.validate_invoice(invoice_gui_data)  #
        if errors:
            error_msg = utils.format_validation_errors(errors)  #
            QMessageBox.warning(
                self,
                "Validation Error",
                f"Please fix the following issues:\n\n{error_msg}"  #
            )
            return None
        return invoice_gui_data

    @pyqtSlot()
    def save_invoice_offline_action(self):
        invoice_gui_data = self._validate_and_get_invoice()
        if not invoice_gui_data:
            return

        saved_invoice, error = add_invoice_local(invoice_gui_data)
        if error:
            QMessageBox.critical(self, "Offline Save Error", f"Failed to save invoice offline: {error}")
            if self.parent_window: self.parent_window.statusBar().showMessage(f"Offline save error: {error}", 5000)
        else:
            QMessageBox.information(self, "Success", f"Invoice '{saved_invoice.invoice_number}' saved offline.")
            if self.parent_window: self.parent_window.statusBar().showMessage(
                f"Invoice '{saved_invoice.invoice_number}' saved offline.", 5000)
            self.clear_form()  # Optionally clear form after save

    @pyqtSlot()
    def submit_invoice_online_action(self):
        invoice_gui_data = self._validate_and_get_invoice()
        if not invoice_gui_data:
            return

        try:
            submitted_invoice, error = add_invoice_postgres(invoice_gui_data)
            if error:
                # Check for unique constraint violation (example, highly DB dependent error string)
                if "unique constraint" in str(error).lower() and "invoices_invoice_number_key" in str(error).lower():
                    QMessageBox.critical(self, "Online Submission Error",
                                         f"Invoice number '{invoice_gui_data.invoice_number}' already exists in the online database.")
                else:
                    QMessageBox.critical(self, "Online Submission Error", f"Failed to submit invoice: {error}")
                if self.parent_window: self.parent_window.statusBar().showMessage(f"Online submission error: {error}",
                                                                                  5000)
            else:
                QMessageBox.information(self, "Success",
                                        f"Invoice '{submitted_invoice.invoice_number}' submitted online.")
                if self.parent_window: self.parent_window.statusBar().showMessage(
                    f"Invoice '{submitted_invoice.invoice_number}' submitted online.", 5000)

                # Optional: Also save/mark as synced in local DB if you want a complete local mirror
                # add_invoice_local(invoice_gui_data, is_synced_val=True)

                self.clear_form()  # Optionally clear form
        except ConnectionError as e:
            QMessageBox.critical(self, "Connection Error", f"Could not connect to PostgreSQL: {e}\nTry saving offline.")
            if self.parent_window: self.parent_window.statusBar().showMessage(f"PostgreSQL Connection Error: {e}", 5000)

    @pyqtSlot()
    def sync_invoices_action(self):
        if self.parent_window: self.parent_window.statusBar().showMessage("Starting sync...", 3000)
        try:
            pg_session = get_postgres_session()  # Establish session for all operations
        except ConnectionError as e:
            QMessageBox.critical(self, "Sync Error", f"Could not connect to PostgreSQL for sync: {e}")
            if self.parent_window: self.parent_window.statusBar().showMessage(f"Sync Connection Error: {e}", 5000)
            return

        unsynced_local_invoices = get_unsynced_invoices_local()
        if not unsynced_local_invoices:
            QMessageBox.information(self, "Sync", "No local invoices to sync.")
            if self.parent_window: self.parent_window.statusBar().showMessage("No invoices to sync.", 3000)
            pg_session.close()
            return

        synced_count = 0
        failed_count = 0
        skipped_count = 0

        for local_inv in unsynced_local_invoices:
            # Pass the active pg_session to avoid opening/closing sessions per invoice
            pg_invoice, error = transfer_invoice_to_postgres(pg_session, local_inv)
            if error == "skipped_duplicate":
                skipped_count += 1
                # Mark as synced locally even if skipped, as it exists in remote
                mark_invoice_as_synced_local(local_inv.id)
            elif error:
                failed_count += 1
                print(f"Failed to sync invoice ID {local_inv.id} ({local_inv.invoice_number}): {error}")
            else:
                mark_invoice_as_synced_local(local_inv.id)
                synced_count += 1

        pg_session.close()  # Close session after all operations

        summary = f"Sync complete. Synced: {synced_count}, Skipped (duplicates): {skipped_count}, Failed: {failed_count}."
        QMessageBox.information(self, "Sync Complete", summary)
        if self.parent_window: self.parent_window.statusBar().showMessage(summary, 10000)

    # ... (all your existing methods like _load_default_invoice, add_line_item, remove_line_item,
    # update_total, get_invoice_data, generate_pdf, clear_form must be present and correct) ...
    # Ensure they use self.parent_window.statusBar() if MainWindow instance is passed.

    # Ensure these methods are present from your provided code:
    def _load_default_invoice(self):  #
        """Load default invoice data into the form."""  #
        default_invoice = Invoice.create_default()  #
        self._load_invoice_data(default_invoice)  #
        self.add_line_item()  # Add the initial line item #

    def _load_invoice_data(self, invoice: Invoice):  #
        """Load invoice data into the form fields."""  #
        self.invoice_number.setText(invoice.invoice_number)  #
        self.invoice_date.setText(invoice.invoice_date)  #
        self.customer_name.setText(invoice.customer_name)  #
        self.customer_address.setText(invoice.customer_address)  #

    @pyqtSlot()  #
    def add_line_item(self):  #
        """Add a new line item to the invoice."""  #
        line_item = LineItem(  #
            number=len(self.line_item_widgets) + 1,  #
            description="",  #
            amount=config.DEFAULT_QUANTITY,  #
            price=0  #
        )
        widget = LineItemWidget(self, line_item)  # # Pass self (InvoiceForm)
        widget.data_changed.connect(self.update_total)  #
        widget.delete_requested.connect(self.remove_line_item)  #
        self.line_item_widgets.append(widget)  #
        self.items_layout.addWidget(widget)  #
        widget.focus_first_empty_field()  #
        self.update_total()  #

    @pyqtSlot(object)  #
    def remove_line_item(self, widget: LineItemWidget):  #
        """Remove a line item from the invoice."""  #
        if len(self.line_item_widgets) <= 1:  #
            QMessageBox.warning(  #
                self,  #
                "Cannot Delete",  #
                "At least one line item is required."  #
            )
            return  #
        self.line_item_widgets.remove(widget)  #
        self.items_layout.removeWidget(widget)  #
        widget.deleteLater()  #
        self._renumber_line_items()  #
        self.update_total()  #

    def _renumber_line_items(self):  #
        """Renumber all line items to maintain sequential order."""  #
        for i, widget in enumerate(self.line_item_widgets):  #
            widget.set_number(i + 1)  #

    @pyqtSlot()  #
    def update_total(self):  #
        """Update the total invoice amount display."""  #
        total = sum(widget.get_line_item().subtotal for widget in self.line_item_widgets)  #
        self.total_display.setText(utils.format_currency(total))  #

    def get_invoice_data(self) -> Invoice:  #
        """Get the current invoice data from the form."""  #
        line_items_data = [widget.get_line_item() for widget in self.line_item_widgets]  #
        return Invoice(  #
            invoice_number=self.invoice_number.text(),  #
            invoice_date=self.invoice_date.text(),  #
            customer_name=self.customer_name.text(),  #
            customer_address=self.customer_address.text(),  #
            line_items=line_items_data  #
        )

    # validate_invoice is now part of _validate_and_get_invoice helper #

    @pyqtSlot()  #
    def generate_pdf(self):  #
        """Generate and save the invoice PDF."""  #
        invoice_gui_data = self._validate_and_get_invoice()  # Use the helper
        if not invoice_gui_data:
            return

        default_filename = utils.FileManager.get_default_invoice_filename(  #
            invoice_gui_data.invoice_number  #
        )
        suggested_path = utils.FileManager.suggest_save_location(default_filename)  #

        options = QFileDialog.Options()  #
        filename, _ = QFileDialog.getSaveFileName(  #
            self,  #
            "Save Invoice PDF",  #
            suggested_path,  #
            "PDF Files (*.pdf)",  #
            options=options  #
        )
        if not filename: return  #
        success, message = self.pdf_manager.export_and_open(invoice_gui_data, filename)  #
        if success:
            QMessageBox.information(self, "Success", message)  #
        else:
            QMessageBox.critical(self, "Error", f"Failed to generate PDF:\n{message}")  #

    @pyqtSlot()  #
    def clear_form(self):  #
        """Clear the form and reset to default state."""  #
        reply = QMessageBox.question(  #
            self, "Clear Form", "Are you sure you want to clear all data?",  #
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No  #
        )
        if reply == QMessageBox.Yes:  #
            self.customer_name.clear()  #
            self.customer_address.clear()  #
            default_invoice = Invoice.create_default()  #
            self.invoice_number.setText(default_invoice.invoice_number)  #
            self.invoice_date.setText(default_invoice.invoice_date)  #
            while self.line_item_widgets:  #
                widget = self.line_item_widgets[0]  #
                self.line_item_widgets.remove(widget)  #
                self.items_layout.removeWidget(widget)  #
                widget.deleteLater()  #
            self.add_line_item()  #
            if self.parent_window: self.parent_window.statusBar().showMessage("Form cleared.", 2000)


class MainWindow(QMainWindow):  # Your existing MainWindow class
    def __init__(self):
        super().__init__()  #
        self.db_config = app_load_config()  # Load app config for DB
        self._setup_window()  #
        # Pass self (MainWindow instance) to InvoiceForm so it can access statusbar
        self._create_central_widget()  # Modified to pass self
        self._setup_menu_bar()  #
        self._setup_status_bar()  #
        self.check_postgres_connection_status()

    def _setup_window(self):  #
        """Configure the main window properties."""  #
        self.setWindowTitle(f"{config.APP_NAME} v{config.APP_VERSION}")  #
        self.setMinimumSize(QSize(config.WINDOW_MIN_WIDTH, config.WINDOW_MIN_HEIGHT))  #
        self._center_window()  #

    def _center_window(self):  #
        """Center the window on the screen."""  #
        try:  # QApplication.desktop() is deprecated in Qt6, use screenAt for multi-monitor
            screen_geometry = QApplication.primaryScreen().geometry()
        except AttributeError:  # Fallback for older PyQt or single screen
            screen_geometry = QApplication.desktop().screenGeometry()  #

        size = self.geometry()  #
        x = (screen_geometry.width() - size.width()) // 2  #
        y = (screen_geometry.height() - size.height()) // 2  #
        self.move(x, y)  #

    def _create_central_widget(self):  #
        """Create and set the central widget."""  #
        # Pass 'self' (the MainWindow instance) to InvoiceForm
        self.invoice_form = InvoiceForm(self)  #
        self.setCentralWidget(self.invoice_form)  #

    def _setup_menu_bar(self):  #
        menubar = self.menuBar()  #
        file_menu = menubar.addMenu('&File')  #

        settings_action = QAction('&Settings', self)
        settings_action.triggered.connect(self.open_settings_dialog)
        file_menu.addAction(settings_action)

        exit_action = QAction('&Exit', self)  # (adapted)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _setup_status_bar(self):  #
        """Setup the status bar."""  #
        self.statusBar().showMessage("Ready")  #

    def open_settings_dialog(self):
        # Assuming SettingsDialog is adapted from previous response for DB settings
        dialog = SettingsDialog(self)  # Use the imported SettingsDialog
        if dialog.exec_():
            self.db_config = app_load_config()  # Reload config
            self.statusBar().showMessage("Settings updated. Re-checking PostgreSQL connection...", 3000)
            self.check_postgres_connection_status()
        else:
            self.statusBar().showMessage("Settings dialog cancelled.", 3000)

    def check_postgres_connection_status(self):
        if initialize_postgres_engine():  # This function now returns True/False
            self.statusBar().showMessage("PostgreSQL Connected.", 5000)
            if hasattr(self.invoice_form, 'submit_online_btn'):  # Check if buttons exist
                self.invoice_form.submit_online_btn.setEnabled(True)
                self.invoice_form.sync_invoices_btn.setEnabled(True)
        else:
            self.statusBar().showMessage("PostgreSQL Disconnected. Online features disabled. Check File > Settings.",
                                         10000)
            if hasattr(self.invoice_form, 'submit_online_btn'):
                self.invoice_form.submit_online_btn.setEnabled(False)
                self.invoice_form.sync_invoices_btn.setEnabled(False)

    def closeEvent(self, event):  #
        # Add unsaved changes check here if needed
        event.accept()  #


# --- Main execution (for testing this file directly) ---
if __name__ == '__main__':
    # Ensure you have `database/models.py`, `database/db_handler.py`,
    # `config/config_manager.py` and `config/settings.json` (can be default)
    # in the correct relative paths if running this directly.

    # Create dummy settings.json if it doesn't exist for db_handler to load
    import os
    from config.config_manager import save_config as app_save_config, DEFAULT_CONFIG as APP_DEFAULT_CONFIG

    if not os.path.exists(os.path.join(os.path.dirname(__file__), '..', 'config', 'settings.json')):
        # Create a default config file in the expected location
        # This path assumes main_window.py is in a subdirectory like 'ui'
        # Adjust path if your structure is different.
        config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        app_save_config(APP_DEFAULT_CONFIG)  # Save default config using your config_manager
        print("Created default settings.json for testing.")

    app = QApplication(sys.argv)
    # Your original main window class
    main_win = MainWindow()  # (instantiation)
    main_win.show()
    sys.exit(app.exec_())