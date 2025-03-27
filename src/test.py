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
import requests
import base64

# Set page configuration
st.set_page_config(page_title="📊 Datastore CSV Dashboard", layout="wide")

# Global session state to track login and page
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'show_lsu_datastore' not in st.session_state:
    st.session_state.show_lsu_datastore = False

# 🔹 User Authentication
st.sidebar.subheader("🔐 User Login")
username = st.sidebar.text_input("👤 Username")
password = st.sidebar.text_input("🔑 Password", type="password")

if st.sidebar.button("🔓 Login"):
    if authenticate_user(username, password):
        st.session_state.logged_in = True
        st.session_state.username = username
        # Check for admin credentials
        if username == "admin" and password == "NewSecurePassword123":
            st.session_state.show_lsu_datastore = True
        st.sidebar.success("✅ Logged in as " + username + "!")
        st.rerun()  # Refresh the page after login
    else:
        st.sidebar.error("❌ Invalid credentials")

# 🔹 Logout Button (Visible only when logged in)
if st.session_state.logged_in:
    if st.sidebar.button("🔒 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.show_lsu_datastore = False
        st.rerun()  # Refresh the page after logout

# Function to fetch files from GitHub
def fetch_from_github(repo_owner, repo_name, file_path, token):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = response.json()['content']
        return base64.b64decode(content)
    else:
        st.error(f"Failed to fetch {file_path} from GitHub: {response.status_code}")
        return None

# Function to update local files from GitHub
def update_from_github():
    repo_owner = "CSC-3380-Spring-2025"  # Replace with your GitHub username
    repo_name = "Team-34"  # Replace with your GitHub repo name
    token = st.secrets["GITHUB_TOKEN"]  # Access the token from Streamlit secrets

    # Ensure directories exist
    os.makedirs("datastore", exist_ok=True)
    os.makedirs("csv_data", exist_ok=True)

    # Fetch and update datastore.db
    db_content = fetch_from_github(repo_owner, repo_name, "datastore/datastore.db", token)
    if db_content:
        with open("datastore/datastore.db", "wb") as f:
            f.write(db_content)
        st.success("✅ Database file updated from GitHub!")

    # Fetch and update CSV files from csv_data directory
    csv_files = ["file1.csv", "file2.csv"]  # Replace with your actual CSV file names
    for csv_file in csv_files:
        csv_content = fetch_from_github(repo_owner, repo_name, f"csv_data/{csv_file}", token)
        if csv_content:
            with open(f"csv_data/{csv_file}", "wb") as f:
                f.write(csv_content)
            st.success(f"✅ {csv_file} updated from GitHub!")

# 🔹 Main Content Based on Login and Page State
if not st.session_state.logged_in:
    # Default page: Original Datastore CSV Management
    st.title("📊 Datastore CSV Management")
    st.write("Please log in to access additional features or the LSU Datastore.")

    # 🔹 File Uploader
    uploaded_file = st.file_uploader("📂 Upload CSV file", type=["csv"])

    if uploaded_file:
        with st.spinner("Uploading file..."):
            file_size = len(uploaded_file.getvalue())
            file_format = "csv"
            user_id = 1  # Simulated User ID
            save_csv_data(uploaded_file.name, uploaded_file.getvalue(), file_size, file_format, user_id)
            time.sleep(1)  # Simulating processing time
        st.success(f"✅ {uploaded_file.name} saved to the database!")

    # 🔹 Display Stored Files
    st.subheader("📁 Stored Files in Database")
    files = get_files()

    if files:
        file_options = {file_id: filename for file_id, filename, _, _, _ in files}
        selected_file_id = st.selectbox("📂 Select a file to preview:", options=file_options.keys(), format_func=lambda x: file_options[x])

        if selected_file_id:
            df = get_csv_preview(selected_file_id)

            if not df.empty:
                # 🔹 Sorting & Filtering
                search_query = st.text_input("🔍 Search CSV Data")
                sort_column = st.selectbox("🔽 Sort by Column", df.columns)
                df = df.sort_values(by=sort_column)

                if search_query:
                    df = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]

                st.write(f"📊 **Preview of {file_options[selected_file_id]}:**")
                st.dataframe(df)

                # 🔹 Data Visualization
                st.subheader("📊 Data Insights")
                numerical_cols = df.select_dtypes(include=["number"]).columns
                if len(numerical_cols) > 0:
                    x_axis = st.selectbox("📏 Select X-Axis:", numerical_cols)
                    y_axis = st.selectbox("📐 Select Y-Axis:", numerical_cols)
                    fig = px.scatter(df, x=x_axis, y=y_axis, title=f"{x_axis} vs {y_axis}")
                    st.plotly_chart(fig)
                else:
                    st.warning("No numerical columns found for visualization.")

                # 🔹 CSV Editing
                st.subheader("✏️ Edit Data")
                edited_df = st.data_editor(df)

                if st.button("💾 Save Changes"):
                    update_csv_data(selected_file_id, edited_df)
                    st.success("✅ Changes saved!")

                # 🔹 File Download Options
                csv_data = df.to_csv(index=False).encode("utf-8")
                json_data = df.to_json(orient="records")
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False)
                excel_data = output.getvalue()

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.download_button("📥 Download CSV", data=csv_data, file_name=f"{file_options[selected_file_id]}.csv", mime="text/csv")
                with col2:
                    st.download_button("📥 Download JSON", data=json_data, file_name=f"{file_options[selected_file_id]}.json", mime="application/json")
                with col3:
                    st.download_button("📥 Download Excel", data=excel_data, file_name=f"{file_options[selected_file_id]}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

                # 🔹 Delete File Option
                if st.button("🗑 Delete This File"):
                    delete_file(selected_file_id)
                    st.success(f"File '{file_options[selected_file_id]}' deleted!")
                    st.rerun()  # Refresh UI after deletion
            else:
                st.error("❌ No data found in the selected CSV.")
    else:
        st.warning("⚠️ No files uploaded yet.")

    # 🔹 Global CSV Search
    st.subheader("🔍 Global Search Across All Stored CSVs")
    search_query = st.text_input("🔎 Search CSV Data Across All Files")

    if search_query:
        results = search_csv_data(search_query)
        if results:
            df_results = pd.DataFrame(results, columns=["File ID", "Row", "Column", "Value"])
            st.dataframe(df_results)
        else:
            st.warning("❌ No matches found.")

    st.success("✅ Datastore System Ready!")
else:
    # New page: LSU Datastore Live Feed (only for admin with correct credentials)
    if st.session_state.show_lsu_datastore:
        st.title("🏫 LSU Datastore - Livestream Data Store")
        st.write("Welcome to the LSU Datastore live feed! View the latest Jobs, Courses, and Research Projects for today.")

        # 🔹 Button to Fetch Latest Data from GitHub
        if st.button("🔄 Fetch Latest Data from GitHub"):
            with st.spinner("Fetching latest data from GitHub..."):
                update_from_github()
            st.rerun()  # Refresh the dashboard to reflect the new data

        # Get today's date
        today = datetime.now().strftime("%Y-%m-%d")

        # Fetch files from the database
        files = get_files()
        if files:
            # Filter files for today and categorize by major and type
            file_options = {}
            for file_id, filename, _, _, _ in files:
                if today in filename:
                    if any(major.replace(" ", "_") in filename for major in ["software_engineering", "cloud_computing", "data_science"]):
                        file_options[file_id] = filename

            if file_options:
                # Sidebar for Major Selection
                st.sidebar.subheader("📋 Select Major")
                majors = ["software_engineering", "cloud_computing", "data_science"]
                selected_major = st.sidebar.selectbox("Choose a Major:", majors, format_func=lambda x: x.replace("_", " ").capitalize())

                # Sidebar for Category Selection
                st.sidebar.subheader("📂 Select Category")
                categories = ["jobs", "courses", "research"]
                selected_category = st.sidebar.selectbox("Choose a Category:", categories, format_func=lambda x: x.capitalize())

                # Filter files based on selected major and category
                filtered_files = {
                    file_id: fname for file_id, fname in file_options.items()
                    if f"{selected_category}_{selected_major}" in fname
                }

                if filtered_files:
                    selected_file_id = st.selectbox(
                        "📂 Select a file to preview:",
                        options=filtered_files.keys(),
                        format_func=lambda x: filtered_files[x]
                    )

                    if selected_file_id:
                        df = get_csv_preview(selected_file_id)

                        if not df.empty:
                            # 🔹 Sorting & Filtering
                            search_query = st.text_input("🔍 Search CSV Data")
                            sort_column = st.selectbox("🔽 Sort by Column", df.columns)
                            df = df.sort_values(by=sort_column)

                            if search_query:
                                df = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]

                            st.write(f"📊 **Preview of {filtered_files[selected_file_id]}:**")
                            st.dataframe(df)

                            # 🔹 Data Visualization
                            st.subheader("📊 Data Insights")
                            numerical_cols = df.select_dtypes(include=["number"]).columns
                            if len(numerical_cols) > 0:
                                x_axis = st.selectbox("📏 Select X-Axis:", numerical_cols)
                                y_axis = st.selectbox("📐 Select Y-Axis:", numerical_cols)
                                fig = px.scatter(df, x=x_axis, y=y_axis, title=f"{x_axis} vs {y_axis}")
                                st.plotly_chart(fig)
                            else:
                                st.warning("No numerical columns found for visualization.")

                            # 🔹 CSV Editing
                            st.subheader("✏️ Edit Data")
                            edited_df = st.data_editor(df)

                            if st.button("💾 Save Changes"):
                                update_csv_data(selected_file_id, edited_df)
                                st.success("✅ Changes saved!")

                            # 🔹 File Download Options
                            csv_data = df.to_csv(index=False).encode("utf-8")
                            json_data = df.to_json(orient="records")
                            output = io.BytesIO()
                            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                                df.to_excel(writer, index=False)
                            excel_data = output.getvalue()

                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.download_button("📥 Download CSV", data=csv_data, file_name=f"{filtered_files[selected_file_id]}.csv", mime="text/csv")
                            with col2:
                                st.download_button("📥 Download JSON", data=json_data, file_name=f"{filtered_files[selected_file_id]}.json", mime="application/json")
                            with col3:
                                st.download_button("📥 Download Excel", data=excel_data, file_name=f"{filtered_files[selected_file_id]}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

                            # 🔹 Delete File Option
                            if st.button("🗑 Delete This File"):
                                delete_file(selected_file_id)
                                st.success(f"File '{filtered_files[selected_file_id]}' deleted!")
                                st.rerun()  # Refresh UI after deletion
                        else:
                            st.error("❌ No data found in the selected CSV.")
                else:
                    st.warning(f"⚠️ No {selected_category.capitalize()} data available for {selected_major.replace('_', ' ').capitalize()} today.")
            else:
                st.warning(f"⚠️ No files uploaded for today ({today}).")
        else:
            st.warning("⚠️ No files uploaded yet.")

        st.success("✅ LSU Datastore System Ready!")
    else:
        # Non-admin logged-in users see the original page
        st.title("📊 Datastore CSV Management")
        st.write("Logged in, but access to LSU Datastore is restricted to admin with 'NewSecurePassword123'.")

        # 🔹 File Uploader
        uploaded_file = st.file_uploader("📂 Upload CSV file", type=["csv"])

        if uploaded_file:
            with st.spinner("Uploading file..."):
                file_size = len(uploaded_file.getvalue())
                file_format = "csv"
                user_id = 1  # Simulated User ID
                save_csv_data(uploaded_file.name, uploaded_file.getvalue(), file_size, file_format, user_id)
                time.sleep(1)  # Simulating processing time
            st.success(f"✅ {uploaded_file.name} saved to the database!")

        # 🔹 Display Stored Files
        st.subheader("📁 Stored Files in Database")
        files = get_files()

        if files:
            file_options = {file_id: filename for file_id, filename, _, _, _ in files}
            selected_file_id = st.selectbox("📂 Select a file to preview:", options=file_options.keys(), format_func=lambda x: file_options[x])

            if selected_file_id:
                df = get_csv_preview(selected_file_id)

                if not df.empty:
                    # 🔹 Sorting & Filtering
                    search_query = st.text_input("🔍 Search CSV Data")
                    sort_column = st.selectbox("🔽 Sort by Column", df.columns)
                    df = df.sort_values(by=sort_column)

                    if search_query:
                        df = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]

                    st.write(f"📊 **Preview of {file_options[selected_file_id]}:**")
                    st.dataframe(df)

                    # 🔹 Data Visualization
                    st.subheader("📊 Data Insights")
                    numerical_cols = df.select_dtypes(include=["number"]).columns
                    if len(numerical_cols) > 0:
                        x_axis = st.selectbox("📏 Select X-Axis:", numerical_cols)
                        y_axis = st.selectbox("📐 Select Y-Axis:", numerical_cols)
                        fig = px.scatter(df, x=x_axis, y=y_axis, title=f"{x_axis} vs {y_axis}")
                        st.plotly_chart(fig)
                    else:
                        st.warning("No numerical columns found for visualization.")

                    # 🔹 CSV Editing
                    st.subheader("✏️ Edit Data")
                    edited_df = st.data_editor(df)

                    if st.button("💾 Save Changes"):
                        update_csv_data(selected_file_id, edited_df)
                        st.success("✅ Changes saved!")

                    # 🔹 File Download Options
                    csv_data = df.to_csv(index=False).encode("utf-8")
                    json_data = df.to_json(orient="records")
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False)
                    excel_data = output.getvalue()

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.download_button("📥 Download CSV", data=csv_data, file_name=f"{file_options[selected_file_id]}.csv", mime="text/csv")
                    with col2:
                        st.download_button("📥 Download JSON", data=json_data, file_name=f"{file_options[selected_file_id]}.json", mime="application/json")
                    with col3:
                        st.download_button("📥 Download Excel", data=excel_data, file_name=f"{file_options[selected_file_id]}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

                    # 🔹 Delete File Option
                    if st.button("🗑 Delete This File"):
                        delete_file(selected_file_id)
                        st.success(f"File '{file_options[selected_file_id]}' deleted!")
                        st.rerun()  # Refresh UI after deletion
                else:
                    st.error("❌ No data found in the selected CSV.")
        else:
            st.warning("⚠️ No files uploaded yet.")

        # 🔹 Global CSV Search
        st.subheader("🔍 Global Search Across All Stored CSVs")
        search_query = st.text_input("🔎 Search CSV Data Across All Files")

        if search_query:
            results = search_csv_data(search_query)
            if results:
                df_results = pd.DataFrame(results, columns=["File ID", "Row", "Column", "Value"])
                st.dataframe(df_results)
            else:
                st.warning("❌ No matches found.")

        st.success("✅ Datastore System Ready!")


       st.success("✅ Datastore System Ready!")
