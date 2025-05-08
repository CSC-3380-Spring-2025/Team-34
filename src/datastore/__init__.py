"""Datastore package for the LSU Datastore Dashboard.

This module initializes the datastore package for the Team-34 project, configuring
logging, loading environment variables, and exporting the Connector class and
clean_dataframe function. It relies on environment variables (e.g., DATABASE_NAME,
LOG_DIR, LOG_FILE) loaded from a .env file (ignored by .gitignore). CSV files
handled by the package may be tracked by Git Large File Storage (LFS) per
.gitattributes.

Attributes:
    __version__: Package version.
    __author__: Package author.
    __all__: Public objects exposed by the package.
"""

import logging
import os
from typing import List

from dotenv import load_dotenv

from .connector import Connector
from .processor import clean_dataframe


# Load environment variables
load_dotenv()

# Configure logging to align with project setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("LiveFeedLogger")
logger.info("Datastore package initialized successfully.")

# Package metadata
__version__: str = "1.0.0"
__author__: str = "Team-34"
__all__: List[str] = ["Connector", "clean_dataframe"]
