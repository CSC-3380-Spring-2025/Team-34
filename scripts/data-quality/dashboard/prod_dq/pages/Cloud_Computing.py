import streamlit as st
import pandas as pd
import sys
import os

# Ensure utils.py is found
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))
from utils import load_data

def show(date_selected):  # Accepts date argument
    st.title("☁️ Cloud Computing Job Listings")

    # Format date
    date_str = date_selected.strftime("%Y-%m-%d")

    # Load Data for Selected Date
    job_data = load_data("cloud_computing", "jobs", date_str)
    course_data = load_data("cloud_computing", "courses", date_str)
    research_data = load_data("cloud_computing", "research", date_str)

    # Display Job Listings
    if not job_data.empty:
        st.subheader(f"Job Listings for {date_str}")
        st.dataframe(job_data, height=300)
    else:
        st.warning(f"⚠️ No job listings available for {date_str}.")

    # Display Course Recommendations
    if not course_data.empty:
        st.subheader(f"Recommended Courses for {date_str}")
        st.dataframe(course_data, height=300)
    else:
        st.warning(f"⚠️ No course data available for {date_str}.")

    # Display Research Projects
    if not research_data.empty:
        st.subheader(f"Research Projects for {date_str}")
        st.dataframe(research_data, height=300)
    else:
        st.warning(f"⚠️ No research project data available for {date_str}.")
