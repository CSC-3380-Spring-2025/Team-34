# src/test.py
import sys
import os

# Ensure Python can find the datastore package
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from datastore.connector import load_data
from datastore.processor import process_data


st.set_page_config(page_title="Datastore Dev Environment", layout="wide")

st.title("📊 Datastore Testing Dashboard")
st.write("Load, process, and analyze data interactively.")

# File uploader for testing
uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file:
    df = load_data(uploaded_file)
    st.write("📂 **Raw Data Preview:**")
    st.dataframe(df.head())

    # Process Data
    processed_df = process_data(df)
    st.write("🛠 **Processed Data Preview:**")
    st.dataframe(processed_df.head())

    # Summary Statistics
    st.write("📈 **Summary Statistics:**")
    st.write(processed_df.describe())

st.success("✅ Datastore dev environment is ready!")
