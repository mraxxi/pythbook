# widgets.py
"""
Custom PyQt5 widgets for the invoice application, including LineItemWidget.
"""
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QSpinBox, QDoubleSpinBox, QStyle, QMessageBox, QComboBox) # Added QComboBox
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QDoubleValidator, QIntValidator, QIcon

from models import LineItem as BusinessLineItem # Business logic model
from config.constants import (LINE_ITEM_FIELD_WIDTHS as FIELD_WIDTHS, CURRENCY_SYMBOL,
                              DEFAULT_QUANTITY, DEFAULT_PRICE)
from utils import format_currency # For displaying currency

class LineItemWidget(QWidget):
    """Widget for inputting a single line item in the invoice form."""
    # Signals
    data_changed = pyqtSignal()  # Emitted when quantity or price changes, for total recalculation
    delete_requested = pyqtSignal(object) # Emitted when delete button is clicked, passing self

    def __init__(self, line_item_model: BusinessLineItem, parent_form=None): # parent_form for context if needed
        super().__init__(parent_form)
        self.model = line_item_model # Stores the business logic LineItem
        self.parent_form = parent_form
        self._init_ui()
        self._connect_signals()
        self.update_display_from_model() # Populate UI from model

    def _init_ui(self):
        """Initialize the UI elements for the line item."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0) # Compact layout

        # 1. Item Number (Label)
        self.number_label = QLabel(str(self.model.number))
        self.number_label.setFixedWidth(FIELD_WIDTHS['number'])
        self.number_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.number_label)

        # 2. Description (QLineEdit)
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Item description")
        # Description width is flexible, set in main form layout
        layout.addWidget(self.description_edit, 1) # Stretch factor of 1

        # 3. Quantity (QDoubleSpinBox or QSpinBox)
        self.quantity_spinbox = QDoubleSpinBox() # Using QDoubleSpinBox for potential fractional quantities
        self.quantity_spinbox.setFixedWidth(FIELD_WIDTHS['quantity'])
        self.quantity_spinbox.setRange(0.01, 999999.99) # Min 0.01 for positive quantity
        self.quantity_spinbox.setDecimals(2) # Or 0 if only whole numbers
        self.quantity_spinbox.setAlignment(Qt.AlignRight)
        layout.addWidget(self.quantity_spinbox)

        # 4. Unit Price (QDoubleSpinBox)
        self.price_spinbox = QDoubleSpinBox()
        self.price_spinbox.setFixedWidth(FIELD_WIDTHS['price'])
        self.price_spinbox.setRange(0.00, 99999999.99) # Price can be 0
        self.price_spinbox.setDecimals(2) # Standard for currency
        self.price_spinbox.setPrefix(f"{CURRENCY_SYMBOL} ")
        self.price_spinbox.setAlignment(Qt.AlignRight)
        layout.addWidget(self.price_spinbox)

        # 5. Subtotal (QLabel - read-only)
        self.subtotal_label = QLabel(format_currency(0, CURRENCY_SYMBOL))
        self.subtotal_label.setFixedWidth(FIELD_WIDTHS['subtotal'])
        self.subtotal_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.subtotal_label)

        # 6. Delete Button
        self.delete_button = QPushButton()
        # Use a standard icon for delete
        icon = self.style().standardIcon(QStyle.SP_TrashIcon)
        if not icon.isNull():
            self.delete_button.setIcon(icon)
        else:
            self.delete_button.setText("X") # Fallback text
        self.delete_button.setFixedWidth(FIELD_WIDTHS['delete_btn'])
        self.delete_button.setToolTip("Delete this line item")
        layout.addWidget(self.delete_button)

        self.setLayout(layout)

    def _connect_signals(self):
        """Connect internal signals to update model and emit data_changed."""
        self.description_edit.textChanged.connect(self._on_description_changed)
        self.quantity_spinbox.valueChanged.connect(self._on_numeric_changed)
        self.price_spinbox.valueChanged.connect(self._on_numeric_changed)
        self.delete_button.clicked.connect(self._on_delete_clicked)

    def update_display_from_model(self):
        """Updates UI elements from the current state of the internal model."""
        self.number_label.setText(str(self.model.number))
        self.description_edit.setText(self.model.description)
        self.quantity_spinbox.setValue(float(self.model.quantity)) # Ensure float for QDoubleSpinBox
        self.price_spinbox.setValue(float(self.model.price))
        self.subtotal_label.setText(format_currency(self.model.subtotal, CURRENCY_SYMBOL))

    @pyqtSlot(str)
    def _on_description_changed(self, text: str):
        self.model.description = text
        # self.data_changed.emit() # Description change doesn't alter total, but form might want to know

    @pyqtSlot(float) # Or int if using QSpinBox
    def _on_numeric_changed(self):
        """Handles changes in quantity or price."""
        self.model.quantity = self.quantity_spinbox.value()
        self.model.price = self.price_spinbox.value()
        self.subtotal_label.setText(format_currency(self.model.subtotal, CURRENCY_SYMBOL))
        self.data_changed.emit() # Crucial: emit to update grand total

    @pyqtSlot()
    def _on_delete_clicked(self):
        # Optional: Add a confirmation dialog here if desired
        # reply = QMessageBox.question(self, "Confirm Delete",
        #                              "Are you sure you want to delete this line item?",
        #                              QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        # if reply == QMessageBox.Yes:
        self.delete_requested.emit(self)

    def get_line_item(self) -> BusinessLineItem:
        """Returns the current state of the business model associated with this widget."""
        # Ensure model is up-to-date with UI before returning
        self.model.description = self.description_edit.text()
        self.model.quantity = self.quantity_spinbox.value()
        self.model.price = self.price_spinbox.value()
        return self.model

    def set_number(self, number: int):
        """Updates the displayed item number and the model."""
        self.model.number = number
        self.number_label.setText(str(number))

    def focus_first_empty_field(self):
        """Sets focus to the description field, especially for new items."""
        self.description_edit.setFocus()

    # Add validation feedback methods if needed (e.g., highlight_error(field_name))