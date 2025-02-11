import streamlit as st
import pandas as pd
import os
from datetime import datetime
from utils import load_data

def show(date_selected):
    """Display Cloud Computing job listings, courses, and research projects for a selected date."""
    
    st.title("☁️ Cloud Computing Listings")

    date_str = date_selected.strftime("%Y-%m-%d")

    def check_cloud_computing_data(date_str):
        """Check if data exists for Cloud Computing on the selected date."""
        categories = ["jobs", "courses", "research"]
        status_data = []

        for category in categories:
            data = load_data("cloud_computing", category, date_str)
            status = "✅ Updated" if not data.empty else "❌ Not Updated"
            status_data.append({"Category": category.capitalize(), "Status": status, "Records": len(data)})

        return pd.DataFrame(status_data)

    st.subheader(f"Data Status for {date_str}")
    status_df = check_cloud_computing_data(date_str)

    def highlight_status(val):
        """Color the cells based on update status."""
        color = "green" if "✅" in val else "red"
        return f"background-color: {color}; color: white; font-weight: bold;"

    st.dataframe(status_df.style.map(highlight_status, subset=["Status"]))

    def display_data(category, title):
        """Show data table with formatted URLs."""
        data = load_data("cloud_computing", category, date_str)
        if not data.empty:
            st.subheader(f"{title} for {date_str}")
            
            if "url" in data.columns:
                data["url"] = data["url"].apply(lambda x: f'<a href="{x}" target="_blank">{x}</a>')

            if "link" in data.columns:
                data["link"] = data["link"].apply(lambda x: f'<a href="{x}" target="_blank">{x}</a>')
            
            st.markdown(
                data.to_html(escape=False, index=False),
                unsafe_allow_html=True
            )
        else:
            st.warning(f"⚠️ No {title.lower()} available for {date_str}.")

    display_data("jobs", "Job Listings")
    display_data("courses", "Recommended Courses")
    display_data("research", "Research Projects")
 