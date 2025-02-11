import os
import pandas as pd
from datetime import datetime

# Define base path inside lsuds/data/raw
DATA_PATH = "../../lsuds/data/raw"

def ensure_dir(directory):
    """Ensure that the directory exists, otherwise create it."""
    os.makedirs(directory, exist_ok=True)

def save_jobs_to_csv(jobs, category):
    """Save filtered job listings to a CSV file inside the correct directory."""
    if not jobs:
        print(f"⚠️ No jobs found for {category}. Skipping CSV save.")
        return

    # Convert category to lowercase with underscores for consistency
    category_folder = category.lower().replace(" ", "_")

    # Set the base directory (no year/month/day structure)
    base_path = os.path.join(DATA_PATH, category_folder, "jobs")
    ensure_dir(base_path)

    # Format the filename with the current date
    filename = os.path.join(base_path, f"jobs_{category}_{datetime.now().strftime('%Y%m%d')}.csv")

    # Save the jobs data
    pd.DataFrame(jobs).to_csv(filename, index=False)
    
    print(f"✅ Saved {len(jobs)} jobs to {filename}")
