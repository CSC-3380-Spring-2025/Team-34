import os
import pandas as pd
from datetime import datetime

# Define base path inside lsuds/data/raw
DATA_PATH = "../../lsuds/data/raw"

def ensure_dir(directory):
    """Ensure that the directory exists, otherwise create it."""
    os.makedirs(directory, exist_ok=True)

def save_research_to_csv(papers, category):
    """Save filtered research papers to a CSV file inside the correct directory."""
    if not papers:
        print(f"⚠️ No research papers found for {category}. Skipping CSV save.")
        return

    # Convert category to lowercase with underscores for consistency
    category_folder = category.lower().replace(" ", "_")

    # Set the base directory (no year/month/day structure)
    base_path = os.path.join(DATA_PATH, category_folder, "research")
    ensure_dir(base_path)

    # Format the filename with the current date
    filename = os.path.join(base_path, f"research_{category}_{datetime.now().strftime('%Y%m%d')}.csv")

    # Save the research data
    pd.DataFrame(papers).to_csv(filename, index=False)
    
    print(f"✅ Saved {len(papers)} research papers to {filename}")
