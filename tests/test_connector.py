# tests/test_connector.py
import pytest
import pandas as pd
from datastore.connector import load_data

def test_load_data():
    """Test loading valid CSV file."""
    df = load_data("sample.csv")  # Replace with a valid test file
    assert isinstance(df, pd.DataFrame)
