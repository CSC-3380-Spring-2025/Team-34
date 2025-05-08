"""Data processing module for the LSU Datastore Dashboard.

This module provides utilities for cleaning pandas DataFrames, removing duplicates
and filling missing values, for the Team-34 project. It is used in the dashboard's
data processing pipeline, such as in rendering scripts or tests. Errors are logged
to LOG_DIR/LOG_FILE.
"""

import pandas as pd

from src.utils import logger


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean a DataFrame by removing duplicates and filling missing values.

    Removes all duplicate rows and fills missing values using forward fill (ffill).
    Logs errors to LOG_DIR/LOG_FILE.

    Args:
        df: Input DataFrame to process.

    Returns:
        Cleaned DataFrame with duplicates removed and missing values filled.

    Raises:
        ValueError: If the input DataFrame is empty or contains invalid data.
        TypeError: If the DataFrame has incompatible data types for processing.
    """
    if df.empty:
        logger.error(
            "DataFrame Cleaning Failed",
            extra={
                "username": "System",
                "action": "clean_dataframe",
                "details": "Input DataFrame is empty",
            },
        )
        raise ValueError("Input DataFrame is empty")

    try:
        df_cleaned: pd.DataFrame = df.drop_duplicates()
        df_cleaned = df_cleaned.fillna(method="ffill")
        return df_cleaned
    except (ValueError, TypeError) as e:
        logger.error(
            "DataFrame Cleaning Failed",
            extra={
                "username": "System",
                "action": "clean_dataframe",
                "details": f"Error: {e}",
            },
        )
        raise ValueError(f"Error processing DataFrame: {e}")
