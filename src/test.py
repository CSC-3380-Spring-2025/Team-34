import streamlit as st
from datastore.database import save_csv_data, get_files, get_csv_preview

st.title("📊 Datastore CSV Preview")

# Upload File
uploaded_file = st.file_uploader("📂 Upload CSV file", type=["csv"])

if uploaded_file:
    # Save file to database
    file_size = len(uploaded_file.getvalue())
    file_format = "csv"
    user_id = 1  # Simulated User ID
    save_csv_data(uploaded_file.name, uploaded_file.getvalue(), file_size, file_format, user_id)

    st.success(f"✅ {uploaded_file.name} saved to the database!")

# Display Files
st.subheader("📁 Stored Files in Database")
files = get_files()

if files:
    for file_id, filename, file_size, file_format, uploaded_at in files:
        st.write(f"📄 **{filename}** ({file_size} bytes) - Uploaded: {uploaded_at}")

        if file_format == "csv":
            if st.button(f"👀 Preview {filename}", key=f"preview_{file_id}"):
                df = get_csv_preview(file_id)
                if df is not None:
                    st.write(f"📊 **Preview of {filename}:**")
                    st.dataframe(df)
                else:
                    st.error("❌ Could not retrieve CSV content.")
