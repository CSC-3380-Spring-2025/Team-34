import streamlit as st

st.set_page_config(page_title="Data Quality Dashboard", layout="wide")

st.title("📊 Data Quality Dashboard")
st.write("Navigate to the job listings using the sidebar.")

st.sidebar.title("Job Listings")
st.sidebar.page_link("pages/Cloud_Computing.py", label="☁️ Cloud Computing")
st.sidebar.page_link("pages/Data_Science.py", label="📊 Data Science")
st.sidebar.page_link("pages/Software_Engineering.py", label="💻 Software Engineering")
