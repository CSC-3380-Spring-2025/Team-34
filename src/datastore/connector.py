# src/datastore/connector.py
import pandas as pd

def load_data(file_path: str) -> pd.DataFrame:
    """Loads data from a CSV file into a DataFrame."""
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()
