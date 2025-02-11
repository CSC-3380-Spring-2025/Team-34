import streamlit as st
import pandas as pd
import datetime
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))  # Ensure utils is found
from utils import load_data

st.set_page_config(page_title="📊 Data Quality Dashboard", layout="wide")

st.title("📊 Data Quality Dashboard")
st.write("Navigate to the job listings using the sidebar.")

st.sidebar.title("Job Listings")

# Sidebar Navigation
page = st.sidebar.radio("Select a Major:", 
    ["☁️ Cloud Computing", "📊 Data Science", "💻 Software Engineering"])

# Calendar Filter (Excludes Weekends)
today = datetime.date.today()

def is_weekend(date):
    """Check if a date is a weekend (Saturday or Sunday)."""
    return date.weekday() in [5, 6]

# Default to today but allow the user to select past weekdays
date_selected = today
while is_weekend(date_selected):  # If today is a weekend, go to the last Friday
    date_selected -= datetime.timedelta(days=1)

date_selected = st.sidebar.date_input(
    "Select a Date (Weekdays Only)",
    value=date_selected,
    min_value=today - datetime.timedelta(days=30),  # Allow last 30 days
    max_value=today,
)

# Prevent selecting weekends in the calendar
if is_weekend(date_selected):
    st.sidebar.warning("⚠️ Weekends are excluded. Please select a weekday.")
    st.stop()

# Convert selected date to string format for file search
formatted_date = date_selected.strftime("%Y-%m-%d")

# Route to the Correct Page
if page == "☁️ Cloud Computing":
    import pages.Cloud_Computing as cloud
    cloud.show(date_selected)

elif page == "📊 Data Science":
    import pages.Data_Science as data
    data.show(date_selected)

elif page == "💻 Software Engineering":
    import pages.Software_Engineering as software
    software.show(date_selected)
