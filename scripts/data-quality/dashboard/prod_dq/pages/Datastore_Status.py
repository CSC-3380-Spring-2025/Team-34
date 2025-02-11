import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from utils import load_data

# Set up page
st.set_page_config(page_title="📈 Datastore Update Status", layout="wide")
st.title("📈 Datastore Update Status")

# Get today's date and allow user to browse past data
today = datetime.today().date()
default_date = today - timedelta(days=1) if today.weekday() == 0 else today  # Default to Friday if Monday

# Allow user to select a date
date_selected = st.sidebar.date_input(
    "Select a Date to Check Updates",
    value=default_date,
    min_value=today - timedelta(days=30),
    max_value=today,
)

date_str = date_selected.strftime("%Y-%m-%d")

# Define majors and categories
majors = ["cloud_computing", "data_science", "software_engineering"]
categories = ["jobs", "courses", "research"]

# Function to check if data exists
def check_datastore_status(date_str):
    status_data = []
    
    for major in majors:
        row = {"Major": major.replace("_", " ").title()}  # Format major name nicely
        
        for category in categories:
            data = load_data(major, category, date_str)
            
            if data is not None:  # If script ran
                status = "✅ Updated" if not data.empty else "⚠️ Updated (No New Data)"
            else:  # If no CSV was created
                status = "❌ Not Updated"
                
            row[category.capitalize()] = status

        status_data.append(row)

    return pd.DataFrame(status_data)

# Get the data status based on selected date
status_df = check_datastore_status(date_str)

# Apply color styling using map() instead of applymap()
def highlight_status(val):
    """Color cells based on update status."""
    if "✅" in val:
        return "background-color: green; color: white; font-weight: bold;"
    elif "⚠️" in val:
        return "background-color: orange; color: black; font-weight: bold;"  # Orange for no new data
    elif "❌" in val:
        return "background-color: red; color: white; font-weight: bold;"
    return ""

# ✅ Fixed: Use `.map()` instead of `.applymap()` to remove FutureWarning
st.dataframe(status_df.style.map(highlight_status, subset=["Jobs", "Courses", "Research"]))

# Show a summary
outdated = status_df[(status_df["Jobs"] == "❌ Not Updated") | 
                     (status_df["Courses"] == "❌ Not Updated") | 
                     (status_df["Research"] == "❌ Not Updated")]

if not outdated.empty:
    st.warning("⚠️ Some datasets are outdated. Consider updating the datastore.")
else:
    st.success("✅ All datasets are up to date for the selected date.")