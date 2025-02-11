import streamlit as st
import pandas as pd
import sys
import os

# Ensure utils.py is accessible
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))  # Moves up one level

from utils import load_data  # Correct import for utils.py

def show(date_selected):
    st.title("💻 Software Engineering Job Listings")

    date_str = date_selected.strftime("%Y-%m-%d")

    job_data = load_data("software_engineering", "jobs", date_str)
    course_data = load_data("software_engineering", "courses", date_str)
    research_data = load_data("software_engineering", "research", date_str)

    if not job_data.empty:
        st.subheader(f"Job Listings for {date_str}")
        st.dataframe(job_data, height=300)
    else:
        st.warning(f"⚠️ No job listings available for {date_str}.")

    if not course_data.empty:
        st.subheader(f"Recommended Courses for {date_str}")
        st.dataframe(course_data, height=300)
    else:
        st.warning(f"⚠️ No course data available for {date_str}.")

    if not research_data.empty:
        st.subheader(f"Research Projects for {date_str}")
        st.dataframe(research_data, height=300)
    else:
        st.warning(f"⚠️ No research project data available for {date_str}.")

