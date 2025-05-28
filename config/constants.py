# config/constants.py
"""
Application-wide constants.
"""
from typing import Dict

APP_NAME: str = "InvoiceManagerPro"
APP_VERSION: str = "1.0.0" # Updated from previous "1.0.1-db" for new structure

# Default window dimensions
WINDOW_MIN_WIDTH: int = 850
WINDOW_MIN_HEIGHT: int = 700

# Default values for invoice form
DEFAULT_INVOICE_NUMBER_PREFIX: str = "INV-"
DEFAULT_QUANTITY: int = 1
DEFAULT_PRICE: float = 0.0

# UI Styling and Layout
LINE_ITEM_FIELD_WIDTHS: Dict[str, int] = {
    'number': 35,
    'description': 300, # Will be stretchy
    'quantity': 70,
    'price': 100,
    'subtotal': 120,
    'delete_btn': 35
}
CURRENCY_SYMBOL: str = "Rp" # Example: Indonesian Rupiah

# Database
SQLITE_DB_NAME: str = "local_invoices.db"
POSTGRES_DEFAULT_PORT: int = 5432

# PDF Generation
PDF_DEFAULT_AUTHOR: str = APP_NAME
PDF_PAGE_SIZE: str = "A4" # Options: "A4", "LETTER", etc. (ReportLab specific)
PDF_FONT_NAME: str = "Helvetica"
PDF_FONT_NAME_BOLD: str = "Helvetica-Bold"
PDF_FONT_SIZE_NORMAL: int = 10
PDF_FONT_SIZE_LARGE: int = 12
PDF_FONT_SIZE_SMALL: int = 8

# Logging
LOGGING_CONFIG_FILE: str = "logging.conf" # Relative to main app entry point or use absolute path

# File Paths (relative to project root or specific context)
# These might be better managed by specific modules or resolved at runtime
# For example, UI_RESOURCES_PATH = os.path.join(os.path.dirname(__file__), '..', 'ui', 'resources')