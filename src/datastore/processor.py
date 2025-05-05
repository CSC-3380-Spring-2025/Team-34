"""Data processing module for Team-34 project.

Provides utilities for cleaning pandas DataFrames used in the LSU Datastore Dashboard.
"""

import pandas as pd
from pandas import DataFrame


def clean_dataframe(df: DataFrame) -> DataFrame:
    """Clean a DataFrame by removing duplicates and filling missing values.

    Args:
        df (DataFrame): Input DataFrame to process.

    Returns:
        DataFrame: Cleaned DataFrame with duplicates removed and missing values filled.

    Raises:
        ValueError: If the input DataFrame is empty or invalid.
    """
    if df.empty:
        raise ValueError("Input DataFrame is empty")
    try:
        df = df.drop_duplicates()
        df = df.fillna(method='ffill')
        return df
    except Exception as e:
        raise ValueError(f"Error processing DataFrame: {e}")