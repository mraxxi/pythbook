# config/config_manager.py
"""
Centralized settings handler.
Loads configuration from a JSON file, can be extended for environment-aware loading.
"""
import json
import os
from .constants import SQLITE_DB_NAME, POSTGRES_DEFAULT_PORT

# Determine project root to ensure settings.json is in a consistent location
# Assuming this file is in bookkeeping_app/config/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_FILE_PATH = os.path.join(PROJECT_ROOT, 'config', 'settings.json')

DEFAULT_CONFIG = {
    "postgres": {
        "host": "localhost",
        "port": POSTGRES_DEFAULT_PORT,
        "database": "invoice_db",
        "user": "your_pg_user",
        "password": "your_pg_password"
    },
    "sqlite_db_name": SQLITE_DB_NAME, # Uses constant
    # Add other configurable settings here, e.g., PDF output directory
    "pdf_output_directory": os.path.join(PROJECT_ROOT, "invoices_pdf")
}

def load_config() -> dict:
    """
    Loads configuration from settings.json.
    If the file doesn't exist, it creates one with default values.
    """
    if not os.path.exists(CONFIG_FILE_PATH):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy() # Return a copy to prevent modification of defaults
    try:
        with open(CONFIG_FILE_PATH, 'r') as f:
            config_data = json.load(f)
            # Ensure all default keys are present, merge if necessary
            # This provides a simple way to update config structure over time
            updated_config = DEFAULT_CONFIG.copy()
            for key, value in config_data.items():
                if isinstance(value, dict) and isinstance(updated_config.get(key), dict):
                    updated_config[key].update(value)
                else:
                    updated_config[key] = value
            if updated_config != config_data: # If changes were merged
                save_config(updated_config)
            return updated_config
    except (IOError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load {CONFIG_FILE_PATH}, using default configuration. Error: {e}")
        # Attempt to save defaults if file is corrupted
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

def save_config(config_data: dict) -> None:
    """Saves the provided configuration data to settings.json."""
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE_PATH), exist_ok=True)
        with open(CONFIG_FILE_PATH, 'w') as f:
            json.dump(config_data, f, indent=4)
    except IOError as e:
        print(f"Error: Could not save configuration to {CONFIG_FILE_PATH}. Error: {e}")

# Initialize config file if it doesn't exist on module import
if not os.path.exists(CONFIG_FILE_PATH):
    save_config(DEFAULT_CONFIG)