import streamlit as st
import pandas as pd
import io
import time
import plotly.express as px
from datastore.database import (
    save_csv_data, get_files, get_csv_preview, delete_file, search_csv_data, update_csv_data, authenticate_user
)

st.set_page_config(page_title="📊 Datastore CSV Dashboard", layout="wide")
st.title("📊 Datastore CSV Management")

# 🔹 User Authentication
st.sidebar.subheader("🔐 User Login")
username = st.sidebar.text_input("👤 Username")
password = st.sidebar.text_input("🔑 Password", type="password")

if st.sidebar.button("🔓 Login"):
    if authenticate_user(username, password):
        st.sidebar.success("✅ Logged in!")
    else:
        st.sidebar.error("❌ Invalid credentials")

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
                st.experimental_rerun()  # Refresh UI after deletion

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
