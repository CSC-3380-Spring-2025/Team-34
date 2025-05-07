"""Unit tests for the datastore connector module."""

import pytest
import pandas as pd

from datastore.connector import load_data


def test_load_data() -> None:
    """Test loading a valid CSV file into a DataFrame.

    The test uses a sample CSV file to verify that load_data returns a pandas
    DataFrame. The sample file should be available in the test environment.

    Raises:
        FileNotFoundError: If the sample CSV file does not exist.
        pd.errors.ParserError: If the CSV file cannot be parsed.
    """
    df: pd.DataFrame = load_data("sample.csv")
    assert isinstance(df, pd.DataFrame)
