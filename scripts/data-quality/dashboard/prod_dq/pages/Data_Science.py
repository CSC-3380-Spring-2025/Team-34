import streamlit as st
import pandas as pd
from utils import load_jobs

st.set_page_config(page_title="Data Science Jobs", layout="wide")

st.title("📊 Data Science Job Listings")

job_data = load_jobs("Data_Science")

if job_data.empty:
    st.warning("⚠️ No Data Science job listings available for today. Check back later.")
else:
    st.dataframe(job_data, height=500)
