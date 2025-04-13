"""Datastore package initialization - handles logging, environment setup, and clean imports."""
import logging
import os
import sys

# Ensure the correct module path is included
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
except ImportError:
    print("Warning: python-dotenv is not installed. Install it using 'pip install python-dotenv'.")

# Load environment variables from a .env file (if exists)
load_dotenv()

# Configure logging for the package
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Try importing modules while handling circular imports
try:
    from .connector import Connector  # Fix: Import `Connector` class instead of `load_data`
except ImportError as e:
    logging.warning(f"Could not import Connector from connector: {e}")

try:
    from .processor import process_data  # Ensure function name matches `processor.py`
except ImportError as e:
    logging.warning(f"Could not import process_data from processor: {e}")

# Optional: Define package metadata
__version__ = "1.0.0"
__author__ = "Your Team"

# List of public objects when importing the package
__all__ = ["Connector", "process_data"]  # Fix: Now properly references `Connector`

# Log that the datastore package has been initialized
logging.info("Datastore package initialized successfully.")

