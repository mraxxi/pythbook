# tests/unit/test_models.py
import pytest
from models import Invoice, LineItem, InvoiceValidator # Business models
from datetime import date

def test_line_item_subtotal():
    item = LineItem(number=1, description="Test", quantity=2, price=10.5)
    assert item.subtotal == 21.0

def test_invoice_total_amount():
    invoice = Invoice(
        invoice_number="INV-001", invoice_date="2025-05-30",
        line_items=[
            LineItem(number=1, description="A", quantity=1, price=10),
            LineItem(number=2, description="B", quantity=2, price=5.5)
        ]
    )
    assert invoice.total_amount == (10 + 11)

def test_invoice_validator_valid():
    invoice = Invoice(
        invoice_number="INV-002", invoice_date="2025-05-30", customer_name="Test Cust",
        line_items=[LineItem(number=1, description="Valid Item", quantity=1, price=100)]
    )
    errors = InvoiceValidator.validate_invoice(invoice)
    assert not errors

def test_invoice_validator_missing_fields():
    invoice = Invoice(invoice_number="", invoice_date="", line_items=[])
    errors = InvoiceValidator.validate_invoice(invoice)
    assert "Invoice number is required." in errors
    assert "Invoice date is required." in errors
    assert "Customer name is required." in errors # Based on current validator
    assert "At least one line item is required." in errors

def test_invoice_validator_invalid_date():
    invoice = Invoice(
        invoice_number="INV-003", invoice_date="30-05-2025", customer_name="Test Cust",
        line_items=[LineItem(number=1, description="Item", quantity=1, price=1)]
    )
    errors = InvoiceValidator.validate_invoice(invoice)
    assert "Invoice date format is invalid. Expected YYYY-MM-DD." in errors