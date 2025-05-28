# utils.py
"""
General utility functions for formatting, validation, file operations, etc.
"""
import os
from datetime import datetime, date
from typing import List, Union
from decimal import Decimal, InvalidOperation

from config.constants import CURRENCY_SYMBOL  # Using constant


def format_currency(amount: Union[float, Decimal, int, str], currency_symbol: str = CURRENCY_SYMBOL) -> str:
    """Formats a numeric amount as currency string."""
    try:
        # Convert to Decimal for consistent formatting, especially if input is float
        if not isinstance(amount, Decimal):
            dec_amount = Decimal(str(amount))
        else:
            dec_amount = amount
        # Format with thousands separator and 2 decimal places
        return f"{currency_symbol} {dec_amount:,.2f}"
    except (InvalidOperation, ValueError):
        return f"{currency_symbol} 0.00"  # Fallback for invalid input


def format_validation_errors(errors: List[str]) -> str:
    """Formats a list of validation error strings into a user-friendly message."""
    if not errors:
        return "No errors."
    return "- " + "\n- ".join(errors)


def sanitize_filename(filename: str) -> str:
    """Sanitizes a string to be used as a safe filename."""
    # Remove invalid characters (common ones for Windows/Linux/Mac)
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    # Replace multiple underscores with a single one
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores or whitespace
    sanitized = sanitized.strip('_ ')
    # Limit length (optional)
    return sanitized[:200] if len(sanitized) > 200 else sanitized


class FileManager:
    """Utility class for file and directory operations."""

    @staticmethod
    def get_default_invoice_filename(invoice_number: str, extension: str = "pdf") -> str:
        """Generates a default filename for an invoice."""
        sanitized_inv_num = sanitize_filename(invoice_number)
        return f"Invoice_{sanitized_inv_num}.{extension}"

    @staticmethod
    def suggest_save_location(filename: str, default_dir_key: str = "pdf_output_directory") -> str:
        """
        Suggests a save location for a file, using a configured default directory.
        Falls back to user's documents or current working directory.
        """
        from config.config_manager import load_config  # Local import to avoid circularity at module level

        app_config = load_config()
        configured_dir = app_config.get(default_dir_key)

        if configured_dir and os.path.isdir(configured_dir):
            base_path = configured_dir
        else:
            # Fallback: User's Documents directory
            documents_path = os.path.join(os.path.expanduser('~'), 'Documents')
            if os.path.isdir(documents_path):
                base_path = documents_path
            else:
                # Ultimate fallback: current working directory
                base_path = os.getcwd()

        os.makedirs(base_path, exist_ok=True)  # Ensure directory exists
        return os.path.join(base_path, filename)


# Example date utility (if storing dates as strings and needing conversion)
def parse_date_string(date_str: str, fmt: str = "%Y-%m-%d") -> Optional[date]:
    """Parses a date string into a date object."""
    try:
        return datetime.strptime(date_str, fmt).date()
    except (ValueError, TypeError):
        return None


def format_date_object(date_obj: Optional[date], fmt: str = "%Y-%m-%d") -> str:
    """Formats a date object into a string."""
    if date_obj is None:
        return ""
    return date_obj.strftime(fmt)