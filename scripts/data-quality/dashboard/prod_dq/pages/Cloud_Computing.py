import streamlit as st
import pandas as pd
from utils import load_jobs

st.set_page_config(page_title="Cloud Computing Jobs", layout="wide")

st.title("☁️ Cloud Computing Job Listings")

job_data = load_jobs("Cloud_Computing")

if job_data.empty:
    st.warning("⚠️ No Cloud Computing job listings available for today. Check back later.")
else:
    st.dataframe(job_data, height=500)
