"""Connector module for the LSU Datastore Dashboard.

This module provides the Connector class to load CSV data into pandas DataFrames
for the Team-34 project. CSV files may be tracked by Git Large File Storage (LFS)
per .gitattributes.
"""

import pandas as pd

from src.utils import logger


class Connector:
    """Utility class for loading data from CSV files into pandas DataFrames.

    Provides a static method to read CSV files, used by the LSU Datastore Dashboard
    for data processing and analysis.
    """

    @staticmethod
    def load_data(file_path: str) -> pd.DataFrame:
        """Load data from a CSV file into a pandas DataFrame.

        Args:
            file_path: Path to the CSV file to load.

        Returns:
            The loaded DataFrame, or an empty DataFrame if loading fails.

        Raises:
            FileNotFoundError: If the CSV file does not exist.
            pd.errors.ParserError: If the CSV file cannot be parsed.
        """
        try:
            df: pd.DataFrame = pd.read_csv(file_path)
            return df
        except (FileNotFoundError, pd.errors.ParserError) as e:
            logger.error(
                "Data Load Failed",
                extra={
                    "username": "System",
                    "action": "load_data",
                    "details": f"Error loading {file_path}: {e}",
                },
            )
            return pd.DataFrame()
