import os
import pandas as pd
from datetime import datetime

# Define base path inside lsuds/data/raw
DATA_PATH = "../../lsuds/data/raw"

def ensure_dir(directory):
    """Ensure that the directory exists, otherwise create it."""
    os.makedirs(directory, exist_ok=True)

def save_courses_to_csv(courses, category):
    """Save filtered news articles to a CSV file inside the correct directory."""
    if not courses:
        print(f"⚠️ No news articles found for {category}. Skipping CSV save.")
        return

    # Convert category to lowercase with underscores for consistency
    category_folder = category.lower().replace(" ", "_")

    # Set the base directory (keeping 'courses' folder name)
    base_path = os.path.join(DATA_PATH, category_folder, "courses")
    ensure_dir(base_path)

    # Format the filename with the current date
    filename = os.path.join(base_path, f"courses_{category}_{datetime.now().strftime('%Y%m%d')}.csv")

    # Save the news data
    pd.DataFrame(courses).to_csv(filename, index=False)
    
    print(f"✅ Saved {len(courses)} news articles to {filename}")
