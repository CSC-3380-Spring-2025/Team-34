import pandas as pd
import os
from datetime import datetime

DATA_PATH = "../../../data/raw"

def get_latest_job_file(category):
    """Find the latest job listing file for the given category."""
    today = datetime.now().strftime('%Y/%m/%d')
    job_folder = f"{DATA_PATH}/{category}/jobs/{today}"

    if not os.path.exists(job_folder):
        return None  # No data available yet

    files = [f for f in os.listdir(job_folder) if f.endswith('.csv')]
    if not files:
        return None  # No files found

    latest_file = sorted(files, reverse=True)[0]  # Get the most recent file
    return os.path.join(job_folder, latest_file)

def load_jobs(category):
    """Load the latest job CSV into a DataFrame."""
    job_file = get_latest_job_file(category)
    if job_file and os.path.exists(job_file):
        return pd.read_csv(job_file)
    return pd.DataFrame()  # Return empty if no data
