import streamlit as st
import pandas as pd
import datetime
import sys
import os

# Ensure utils.py is found
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))

# ✅ `set_page_config` MUST be the first Streamlit command
st.set_page_config(page_title="📊 Data Quality Dashboard", layout="wide")

st.title("📊 Data Quality Dashboard")
st.write("Navigate to the listings using the sidebar.")

st.sidebar.title("Computer Science")

# Use Streamlit's session state to track the selected page
if "current_page" not in st.session_state:
    st.session_state.current_page = "📈 Datastore Status"

# Sidebar Navigation
page = st.sidebar.radio("Select a Page:", 
    ["☁️ Cloud Computing", "📊 Data Science", "💻 Software Engineering", "📈 Datastore Status"])

# If the page selection has changed, rerun Streamlit
if st.session_state.current_page != page:
    st.session_state.current_page = page
    st.rerun()

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

# Route to the Correct Page
if page == "☁️ Cloud Computing":
    import Cloud_Computing as cloud
    cloud.show(date_selected)

elif page == "📊 Data Science":
    import Data_Science as data
    data.show(date_selected)

elif page == "💻 Software Engineering":
    import Software_Engineering as software
    software.show(date_selected)
