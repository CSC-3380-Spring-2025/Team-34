# src/test.py
import sys
import os
import sqlite3

from database import DB_NAME

# Ensure Python can find the datastore package
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from datastore.connector import Connector
from datastore.processor import process_data

# Initialize Streamlit app
st.set_page_config(page_title="📊 Datastore Dev Environment", layout="wide")
st.title("📊 Datastore Testing Dashboard")
st.write("Load, process, and analyze data interactively.")

# Initialize Database
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            content BLOB
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Function to save file to the database
def save_file_to_db(filename, content):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO files (filename, content) VALUES (?, ?)", (filename, content))
    conn.commit()
    conn.close()

# Function to retrieve files from the database
def get_saved_files():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT filename FROM files")
    files = cursor.fetchall()
    conn.close()
    return [file[0] for file in files]

# File uploader for testing
uploaded_file = st.file_uploader("📂 Upload CSV file", type=["csv"])

if uploaded_file:
    df = Connector.load_data(uploaded_file)
    st.write("📂 **Raw Data Preview:**")
    st.dataframe(df.head())

    # Process Data
    processed_df = process_data(df)
    st.write("🛠 **Processed Data Preview:**")
    st.dataframe(processed_df.head())

    # Summary Statistics
    st.write("📈 **Summary Statistics:**")
    st.write(processed_df.describe())

    # Save file to database
    save_file_to_db(uploaded_file.name, uploaded_file.getvalue())
    st.success(f"✅ {uploaded_file.name} saved to the database!")

# Display stored files
st.subheader("📁 Stored Files in Database")
saved_files = get_saved_files()

if saved_files:
    for file in saved_files:
        st.write(f"- {file}")
else:
    st.write("No files saved in the database yet.")

st.success("✅ Datastore dev environment is ready!")
