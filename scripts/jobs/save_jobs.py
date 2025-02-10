import os
import pandas as pd
from datetime import datetime

def ensure_dir(directory):
    """Ensure that the directory exists, otherwise create it."""
    os.makedirs(directory, exist_ok=True)

def save_jobs_to_csv(jobs, category):
    """Save filtered job listings to a CSV file inside structured folders."""
    if not jobs:
        print(f"No jobs found for {category}. Skipping CSV save.")
        return

    date_str = datetime.now().strftime('%Y/%m/%d')  # YYYY/MM/DD format
    base_path = f'Team-34/lsuds/data/raw/{category}/jobs/{date_str}'
    ensure_dir(base_path)

    filename = f'{base_path}/jobs_{category}_{datetime.now().strftime("%Y%m%d")}.csv'
    pd.DataFrame(jobs).to_csv(filename, index=False)
    
    print(f"✅ Saved {len(jobs)} jobs to {filename}")

