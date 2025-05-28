# models.py (at the root of your application, or in a 'domain' sub-package)
"""
Business logic layer: data classes for Invoice and LineItem, and validation logic.
These models are used by the GUI and business logic, and are distinct from
database ORM models.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Union
from datetime import date
import re

from config.constants import DEFAULT_QUANTITY, DEFAULT_PRICE  # Using constants


@dataclass
class LineItem:
    """Represents a single line item in an invoice."""
    # 'number' is primarily for UI display and ordering within the form.
    # It might not be persisted if DB uses its own ordering or PK.
    number: int
    description: str = ""
    quantity: Union[int, float] = DEFAULT_QUANTITY
    price: float = DEFAULT_PRICE

    @property
    def subtotal(self) -> float:
        """Calculated subtotal for the line item."""
        return self.quantity * self.price


@dataclass
class Invoice:
    """Represents an invoice, containing header information and line items."""
    invoice_number: str
    invoice_date: str  # Stored as string e.g., "YYYY-MM-DD" from UI
    customer_name: str = ""
    customer_address: str = ""
    line_items: List[LineItem] = field(default_factory=list)

    # Optional: fields for notes, terms, tax rates, discounts etc.

    @property
    def total_amount(self) -> float:
        """Calculated total amount for the invoice."""
        return sum(item.subtotal for item in self.line_items)

    @staticmethod
    def create_default() -> 'Invoice':
        """Creates a default invoice instance, e.g., for a new form."""
        from config.constants import DEFAULT_INVOICE_NUMBER_PREFIX
        today_str = date.today().strftime("%Y-%m-%d")
        # Simplified default number; a real system might query DB for next sequence
        default_inv_num = f"{DEFAULT_INVOICE_NUMBER_PREFIX}{date.today().strftime('%Y%m%d')}-001"
        return Invoice(
            invoice_number=default_inv_num,
            invoice_date=today_str,
            line_items=[LineItem(number=1)]  # Start with one empty line item
        )


class InvoiceValidator:
    """Provides validation logic for Invoice and LineItem data."""

    @staticmethod
    def is_valid_date_format(date_string: str, date_format: str = "%Y-%m-%d") -> bool:
        """Checks if the date string matches the expected format."""
        try:
            date.strptime(date_string, date_format)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_invoice(invoice: Invoice) -> List[str]:
        """
        Validates the invoice data.
        Returns a list of error messages. An empty list means valid.
        """
        errors: List[str] = []

        if not invoice.invoice_number.strip():
            errors.append("Invoice number is required.")

        if not invoice.invoice_date.strip():
            errors.append("Invoice date is required.")
        elif not InvoiceValidator.is_valid_date_format(invoice.invoice_date):
            errors.append(f"Invoice date format is invalid. Expected YYYY-MM-DD.")

        if not invoice.customer_name.strip():
            errors.append("Customer name is required.")

        # Basic check for address, could be optional
        # if not invoice.customer_address.strip():
        #     errors.append("Customer address is required.")

        if not invoice.line_items:
            errors.append("At least one line item is required.")
        else:
            for i, item in enumerate(invoice.line_items):
                item_num = item.number  # Use the item's own number for error reporting
                if not item.description.strip():
                    errors.append(f"Line item #{item_num}: Description is required.")
                if not isinstance(item.quantity, (int, float)) or item.quantity <= 0:
                    errors.append(f"Line item #{item_num}: Quantity must be a positive number.")
                if not isinstance(item.price, (int, float)) or item.price < 0:  # Price can be zero
                    errors.append(f"Line item #{item_num}: Price must be a non-negative number.")

        return errors