import pandas as pd

class Connector:
    """Handles loading data from a CSV file into a DataFrame."""

    @staticmethod
    def load_data(file_path: str) -> pd.DataFrame:
        """Loads data from a CSV file into a DataFrame."""
        try:
            df = pd.read_csv(file_path)
            return df
        except Exception as e:
            print(f"Error loading data: {e}")
            return pd.DataFrame()
