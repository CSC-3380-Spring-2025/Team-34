"""Connector module for Team-34 project.

Provides the Connector class to load CSV data into pandas DataFrames for the
LSU Datastore Dashboard.
"""

import pandas as pd


class Connector:
    """Handle loading data from CSV files into pandas DataFrames."""

    @staticmethod
    def load_data(file_path: str) -> pd.DataFrame:
        """Load data from a CSV file into a pandas DataFrame.

        Args:
            file_path (str): Path to the CSV file to load.

        Returns:
            pd.DataFrame: The loaded DataFrame, or an empty DataFrame if loading fails.

        Raises:
            Exception: If the CSV file cannot be read (e.g., file not found, invalid format).
        """
        try:
            df = pd.read_csv(file_path)
            return df
        except Exception as e:
            print(f"Error loading data from {file_path}: {e}")
            return pd.DataFrame()