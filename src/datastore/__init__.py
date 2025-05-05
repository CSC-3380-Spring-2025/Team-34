"""Datastore package for Team-34 project.

Initializes logging, environment variables, and imports for database operations
and data processing. Exports Connector class and clean_dataframe function for use
in the LSU Datastore Dashboard.

Attributes:
    __version__ (str): Package version.
    __author__ (str): Package author.
    __all__ (list): Public objects exposed by the package.
"""

import logging
import os
import sys
from typing import List

try:
    from dotenv import load_dotenv
except ImportError:
    print("Warning: python-dotenv is not installed. Install it using 'pip install python-dotenv'.")

# Local imports
try:
    from .connector import Connector
except ImportError as e:
    logging.warning(f"Could not import Connector from connector: {e}")

try:
    from .processor import clean_dataframe  # Updated from process_data
except ImportError as e:
    logging.warning(f"Could not import clean_dataframe from processor: {e}")

# Configure logging for the package
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

# Load environment variables from a .env file (if exists)
load_dotenv()

# Ensure the correct module path is included
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Package metadata
__version__: str = '1.0.0'
__author__: str = 'Your Team'
__all__: List[str] = ['Connector', 'clean_dataframe']  # Updated from process_data

# Log package initialization
logging.info('Datastore package initialized successfully.')