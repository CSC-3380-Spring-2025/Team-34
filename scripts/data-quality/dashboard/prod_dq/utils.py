import pandas as pd
import os
from datetime import datetime

DATA_PATH = "C:/Users/Bdog/Team-34/lsuds/data/raw"

def get_latest_file(major, data_type, date_str=None):
    """Get the latest CSV file for jobs, courses, or research projects for a specific major and date."""
    folder_path = os.path.join(DATA_PATH, major, data_type)

    if not os.path.exists(folder_path):
        return None  # Folder does not exist

    files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]

    # If a date is specified, try to find a file with that date
    if date_str:
        matched_files = [f for f in files if date_str in f]
        if matched_files:
            latest_file = sorted(matched_files, reverse=True)[0]
            return os.path.join(folder_path, latest_file)

    # If no file matches the date, default to the most recent file available
    if files:
        latest_file = sorted(files, reverse=True)[0]
        return os.path.join(folder_path, latest_file)

    return None  # No files found

def load_data(major, data_type="jobs", date_str=None):
    """Load the latest CSV file for a selected date into a DataFrame.
       If no file is found for the selected date, it loads the most recent available file."""
    
    file_path = get_latest_file(major, data_type, date_str)
    
    # If no file was found for the selected date, get the most recent file available
    if not file_path:
        file_path = get_latest_file(major, data_type)

    if file_path and os.path.exists(file_path):
        return pd.read_csv(file_path)

    return pd.DataFrame()  # Return empty DataFrame if no data is found
