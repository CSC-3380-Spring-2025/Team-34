"""Datastore package initialization - handles logging, environment setup, and clean imports."""
import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

# Load environment variables from a .env file (if exists)
load_dotenv()

# Configure logging for the package
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Expose key modules at the package level for cleaner imports
from .connector import load_data
from .processor import Processor

# Optional: Define package metadata
__version__ = "1.0.0"
__author__ = "Your Team"

# List of public objects when importing the package
__all__ = ["Connector", "Processor"]

# Log that the datastore package has been initialized
logging.info("Datastore package initialized successfully.")


