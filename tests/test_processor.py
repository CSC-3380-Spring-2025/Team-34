"""Unit tests for the datastore processor module."""

from typing import Any

import pandas as pd
import pytest

from datastore.processor import process_data


def test_process_data() -> None:
    """Test that process_data removes missing values and duplicates from a DataFrame.

    The test uses a sample DataFrame with missing values and duplicate rows to verify
    that process_data returns a cleaned DataFrame with no missing values or duplicates.

    Raises:
        ValueError: If the input DataFrame contains invalid data that process_data cannot handle.
        TypeError: If the input is not a pandas DataFrame.
    """
    data: dict[str, Any] = {'A': [1, 2, 2, None], 'B': ['X', 'Y', 'Y', 'Z']}
    df: pd.DataFrame = pd.DataFrame(data)
    processed_df: pd.DataFrame = process_data(df)

    assert processed_df.isnull().sum().sum() == 0  # No missing values
    assert processed_df.duplicated().sum() == 0  # No duplicates
