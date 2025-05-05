# tests/test_processor.py
import pytest
import pandas as pd
from datastore.processor import process_data
from typing import Any

def test_process_data():
    """Test processing function with missing values and duplicates."""
    data : dict[str, Any]= {"A": [1, 2, 2, None], "B": ["X", "Y", "Y", "Z"]}
    df : pd.DataFrame = pd.DataFrame(data)
    processed_df = process_data(df)

    assert processed_df.isnull().sum().sum() == 0  # No missing values
    assert processed_df.duplicated().sum() == 0  # No duplicates
