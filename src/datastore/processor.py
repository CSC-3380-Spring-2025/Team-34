# src/datastore/processor.py
import pandas as pd

def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """Performs basic data processing: fills missing values and removes duplicates."""
    df = df.drop_duplicates()
    df = df.fillna(method='ffill')
    return df
