import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'settings.json')

DEFAULT_CONFIG = {
    "postgres": {
        "host": "localhost",
        "port": 5432,
        "database": "bookkeeping_db",
        "user": "your_user",
        "password": "your_password"
    },
    "sqlite_db_name": "local_transactions.db",
    "categories": ["Groceries", "Utilities", "Transport", "Salary", "Entertainment", "Other"],
    "payment_methods": ["Cash", "Credit Card", "Debit Card", "Bank Transfer", "Other"]
}

def load_config():
    """Loads configuration from settings.json, creates it with defaults if it doesn't exist."""
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError):
        # Fallback to defaults if file is corrupted or unreadable
        save_config(DEFAULT_CONFIG) # Try to repair with defaults
        return DEFAULT_CONFIG

def save_config(config_data):
    """Saves configuration to settings.json."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=4)
    except IOError as e:
        print(f"Error saving configuration: {e}")

# Initialize config file if it doesn't exist on module import
if not os.path.exists(CONFIG_FILE):
    save_config(DEFAULT_CONFIG)