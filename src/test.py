import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
import io
import time
import plotly.express as px
from src.datastore.database import (
    save_csv_data, get_files, get_csv_preview, delete_file, search_csv_data, update_csv_data, authenticate_user
)
from datetime import datetime

# Set page configuration
st.set_page_config(page_title="📊 Datastore CSV Dashboard", layout="wide")

# Add custom CSS for LSU colors to enhance visual appeal
st.markdown("""
    <style>
        h1 {
            color: #461D7C;
        }
        .stButton>button {
            background-color: #FABD00;
            color: white;
        }
        .stSubheader {
            color: #461D7C;
        }
    </style>
""", unsafe_allow_html=True)

# Session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'show_lsu_datastore' not in st.session_state:
    st.session_state.show_lsu_datastore = False

# Add LSU images at the top of the main area
base_dir = os.path.dirname(__file__)
col1, col2 = st.columns(2)
with col1:
    st.image(os.path.join(base_dir, "lsu_data_icon.png"), caption="LSU Data Icon")
with col2:
    st.image(os.path.join(base_dir, "lsu_logo.png"), caption="LSU Logo")

# LSU Datastore Feed Shown First (regardless of login)
st.title("🌭 LSU Datastore - Livestream Data Store")
st.write("Welcome to the LSU Datastore live feed! View the latest Jobs, Courses, and Research Projects for today.")

# Today's date
today = datetime.now().strftime("%Y-%m-%d")

# Fetch files
files = get_files()
if files:
    file_options = {}
    for file_id, filename, _, _, _ in files:
        if today in filename and any(major.replace(" ", "_") in filename for major in ["software_engineering", "cloud_computing", "data_science"]):
            file_options[file_id] = filename

    if file_options:
        st.sidebar.subheader("📋 Select Major")
        majors = ["software_engineering", "cloud_computing", "data_science"]
        selected_major = st.sidebar.selectbox("Choose a Major:", majors, format_func=lambda x: x.replace("_", " ").title())

        st.sidebar.subheader("📂 Select Category")
        categories = ["jobs", "courses", "research", "lsu"]
        selected_category = st.sidebar.selectbox("Choose a Category:", categories, format_func=lambda x: x.upper() if x=="lsu" else x.title())

        filtered_files = {
            file_id: fname for file_id, fname in file_options.items()
            if f"{selected_category}_{selected_major}" in fname
        }

        if filtered_files:
            selected_file_id = st.selectbox("📂 Select a file to preview:", options=filtered_files.keys(), format_func=lambda x: filtered_files[x])
            if selected_file_id:
                file_path = f"src/csv_data/{file_options[selected_file_id]}"
                df = pd.read_csv(file_path)
                if not df.empty:
                    search_query = st.text_input("🔍 Search CSV Data")
                    sort_column = st.selectbox("🔽 Sort by Column", df.columns)
                    df = df.sort_values(by=sort_column)
                    if search_query:
                        df = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]

                    st.write(f"📊 **Preview of {filtered_files[selected_file_id]}:**")
                    st.dataframe(df)

                    st.subheader("📊 Data Insights")
                    numerical_cols = df.select_dtypes(include=["number"]).columns
                    if len(numerical_cols) > 0:
                        x_axis = st.selectbox("📏 Select X-Axis:", numerical_cols)
                        y_axis = st.selectbox("📐 Select Y-Axis:", numerical_cols)
                        fig = px.scatter(df, x=x_axis, y=y_axis, title=f"{x_axis} vs {y_axis}")
                        st.plotly_chart(fig)
                    else:
                        st.warning("No numerical columns found for visualization.")
                else:
                    st.error("❌ No data found in the selected CSV.")
        else:
            st.warning(f"⚠️ No {selected_category.title()} data available for {selected_major.replace('_', ' ').title()} today.")
    else:
        st.warning(f"⚠️ No files uploaded for today ({today}).")
else:
    st.warning("⚠️ No files uploaded yet.")

st.success("✅ LSU Datastore System Ready!")

# Sidebar Login Panel
st.sidebar.subheader("🔐 User Login")
username = st.sidebar.text_input("👤 Username")
password = st.sidebar.text_input("🔑 Password", type="password")

if st.sidebar.button("🔓 Login"):
    if authenticate_user(username, password):
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.show_lsu_datastore = (username == "admin" and password == "NewSecurePassword123")
        st.sidebar.success("Logged in as " + username + "!")
        st.rerun()
    else:
        st.sidebar.error("❌ Invalid credentials")

if st.session_state.logged_in:
    if st.sidebar.button("🔒 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.show_lsu_datastore = False
        st.rerun()

    # Datastore CSV Upload/Edit Mode (visible after login)
    st.title("📊 Datastore CSV Management")
    st.write("Upload, preview, edit, and manage your CSV datasets.")

    uploaded_file = st.file_uploader("📂 Upload CSV file", type=["csv"])
    if uploaded_file:
        with st.spinner("Uploading file..."):
            save_csv_data(uploaded_file.name, uploaded_file.getvalue(), len(uploaded_file.getvalue()), "csv", 1)
            time.sleep(1)
        st.success(f"✅ {uploaded_file.name} saved to the database!")

    st.subheader("📁 Stored Files in Database")
    files = get_files()
    if files:
        file_options = {file_id: filename for file_id, filename, _, _, _ in files}
        selected_file_id = st.selectbox("📂 Select a file to preview:", options=file_options.keys(), format_func=lambda x: file_options[x])
        if selected_file_id:
            df = get_csv_preview(selected_file_id)
            if not df.empty:
                search_query = st.text_input("🔍 Search CSV Data", key="search_query_main")
                sort_column = st.selectbox("🔽 Sort by Column", df.columns, key="select_column")
                df = df.sort_values(by=sort_column)
                if search_query:
                    df = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]

                st.write(f"📊 **Preview of {file_options[selected_file_id]}:**")
                st.dataframe(df)

                st.subheader("✏️ Edit Data")
                edited_df = st.data_editor(df)
                if st.button("📏 Save Changes"):
                    update_csv_data(selected_file_id, edited_df)
                    st.success("✅ Changes saved!")

                csv_data = df.to_csv(index=False).encode("utf-8")
                json_data = df.to_json(orient="records")
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False)
                excel_data = output.getvalue()

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.download_button("📅 Download CSV", data=csv_data, file_name=f"{file_options[selected_file_id]}.csv", mime="text/csv")
                with col2:
                    st.download_button("📅 Download JSON", data=json_data, file_name=f"{file_options[selected_file_id]}.json", mime="application/json")
                with col3:
                    st.download_button("📅 Download Excel", data=excel_data, file_name=f"{file_options[selected_file_id]}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

                if st.button("🗑 Delete This File"):
                    delete_file(selected_file_id)
                    st.success(f"File '{file_options[selected_file_id]}' deleted!")
                    st.rerun()
            else:
                st.error("❌ No data found in the selected CSV.")
    else:
        st.warning("⚠️ No files uploaded yet.")

    st.subheader("🔍 Global Search Across All Stored CSVs")
    global_search = st.text_input("🔎 Search CSV Data Across All Files")
    if global_search:
        results = search_csv_data(global_search)
        if results:
            st.dataframe(pd.DataFrame(results, columns=["File ID", "Row", "Column", "Value"]))
        else:
            st.warning("❌ No matches found.")

    st.success("✅ Datastore System Ready!")


# Link to DAG Grid
st.markdown("---")
st.markdown("[Link to DAG Grid](https://animated-train-jjvx5x4q9g73p5v5-8080.app.github.dev/dags/fetch_store_dag/grid)")