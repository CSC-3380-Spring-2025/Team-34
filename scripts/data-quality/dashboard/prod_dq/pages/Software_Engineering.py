import streamlit as st
import pandas as pd
from utils import load_jobs

st.set_page_config(page_title="Software Engineering Jobs", layout="wide")

st.title("💻 Software Engineering Job Listings")

job_data = load_jobs("Software_Engineering")

if job_data.empty:
    st.warning("⚠️ No Software Engineering job listings available for today. Check back later.")
else:
    st.dataframe(job_data, height=500)
