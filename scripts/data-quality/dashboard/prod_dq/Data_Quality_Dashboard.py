import streamlit as st
import datetime
import os
import subprocess
import pandas as pd
from email_senderr import send_email
from utils import load_data, get_files_for_date, LSU_DATASTORE_PATH

LSU_DATASTORE_PATH = "C:/Users/Bdog/Team-34/lsuds/data/raw/"

# Define LSU-Themed Colors (Dark Mode)
BG_COLOR = "#0B132B"
CARD_COLOR = "#1C2541"
TEXT_COLOR = "#FFFFFF"
HIGHLIGHT_COLOR = "#3A506B"
LSU_GOLD = "#FDD023"
from_email = os.getenv("YOUR_EMAIL")
password = os.getenv("YOUR_EMAIL_PASSWORD")


# Page Configuration
st.set_page_config(page_title="Data Quality Dashboard", layout="wide")

# Sidebar Navigation
st.sidebar.image("company_logo.png", width=200)  # Replace with actual logo
st.sidebar.title("📊 Data Dashboard")
selected_date = st.sidebar.date_input("Choose a date", datetime.date.today())
date_str = selected_date.strftime("%Y%m%d")  # Use YYYYMMDD format for consistency

st.sidebar.write(f"📅 Displaying data for **{selected_date.strftime('%Y-%m-%d')}**")

# Refresh Button
if st.sidebar.button("🔄 Refresh Data"):
    fetch_script_path = "C:/Users/Bdog/Team-34/scripts/fetch_all.py"
    if os.path.exists(fetch_script_path):
        with st.spinner("Fetching latest data... Please wait."):
            try:
                subprocess.run(["python", fetch_script_path], check=True)
                st.success("✅ Data refreshed successfully!")
                st.rerun()
            except subprocess.CalledProcessError as e:
                st.error(f"❌ Failed to fetch data: {e}")
    else:
        st.error("❌ `fetch_all.py` script not found!")

with st.sidebar:
    user_email = st.text_input("Enter your email address")

    if st.button("Send Data to My Email"):
        if user_email:
            categories = ["data_science", "software_engineering", "cloud_computing"]
            features = ["jobs", "courses", "research"]
            combined_df = pd.DataFrame()  # Initialize empty DataFrame
            
            found_files = []

            for category in categories:
                for feature in features:
                    files = get_files_for_date(category, feature, date_str)  # Find files
                    
                    if files:  # If matching files exist
                        for file in files:
                            data = load_data(category, feature, date_str)  # Load data
                            data["category"] = category  # Add metadata
                            data["feature"] = feature
                            combined_df = pd.concat([combined_df, data], ignore_index=True)
                            found_files.append(file)

            if not found_files:
                st.error(f"No data files found for {date_str}.")
            else:
                # Save combined data to a CSV file
                combined_csv_path = os.path.join(LSU_DATASTORE_PATH, f"combined_data_{date_str}.csv")
                combined_df.to_csv(combined_csv_path, index=False)

                # Get sender email from environment variable
                EMAIL_FROM = os.getenv("EMAIL_FROM")

                if not EMAIL_FROM:
                    st.error("Email sending failed: Sender email is not configured.")
                else:
                    # Send the CSV file via email
                    send_status = send_email(
                        subject="Requested Data File",
                        body="Please find the attached data file.",
                        to_email=user_email,
			attachment_path=combined_csv_path
                    )

                    if "successfully" in send_status:
                        st.success("Email sent successfully!")
                    else:
                        st.error(send_status)
        else:
            st.error("Please enter a valid email address.")



# Last Updated Timestamp
st.sidebar.text(f"Last Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Metrics Overview at the Top
st.markdown(
    f"""
    <style>
        .metric-container {{
            background-color: {CARD_COLOR};
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            color: {TEXT_COLOR};
            font-size: 20px;
        }}
        .metric-number {{
            font-size: 28px;
            font-weight: bold;
            color: {LSU_GOLD};
        }}
    </style>
    """,
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns(3)

def get_data_count(df):
    return len(df) if not df.empty else 0

# Load data for all three majors
majors = ["data_science", "software_engineering", "cloud_computing"]
major_titles = {
    "data_science": "📊 Data Science",
    "software_engineering": "💻 Software Engineering",
    "cloud_computing": "☁️ Cloud Computing"
}

# Fetch and count data for each major
data_counts = {major: {
    "jobs": get_data_count(load_data(major, "jobs", date_str)),
    "courses": get_data_count(load_data(major, "courses", date_str)),
    "research": get_data_count(load_data(major, "research", date_str))
} for major in majors}

col1.markdown(f"<div class='metric-container'>Jobs<br><span class='metric-number'>{sum(data['jobs'] for data in data_counts.values())}</span></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='metric-container'>Courses<br><span class='metric-number'>{sum(data['courses'] for data in data_counts.values())}</span></div>", unsafe_allow_html=True)
col3.markdown(f"<div class='metric-container'>Research<br><span class='metric-number'>{sum(data['research'] for data in data_counts.values())}</span></div>", unsafe_allow_html=True)

# Content Section with Tables Side-by-Side
st.markdown("---")
st.subheader(f"📄 Data Overview for {selected_date.strftime('%Y-%m-%d')}")

# Function to highlight missing values
def highlight_missing(s):
    return ['background-color: yellow' if pd.isna(v) else '' for v in s]

# Function to shorten long text
def shorten_text(text, max_length=80):
    if isinstance(text, str) and len(text) > max_length:
        return text[:max_length] + "..."
    return text

# Search Box for Filtering
search_query = st.text_input("🔍 Search Titles", "")

# Display data for each major separately
for major in majors:
    st.markdown(f"## {major_titles[major]}")

    jobs_data = load_data(major, "jobs", date_str)
    courses_data = load_data(major, "courses", date_str)
    research_data = load_data(major, "research", date_str)

    # Apply search filter
    if search_query:
        jobs_data = jobs_data[jobs_data.apply(lambda row: row.astype(str).str.contains(search_query, case=False, na=False).any(), axis=1)]
        courses_data = courses_data[courses_data.apply(lambda row: row.astype(str).str.contains(search_query, case=False, na=False).any(), axis=1)]
        research_data = research_data[research_data.apply(lambda row: row.astype(str).str.contains(search_query, case=False, na=False).any(), axis=1)]

    def format_dataframe(df):
        if df.empty:
            return pd.DataFrame(columns=["No Data Available"])
        if "description" in df.columns:
            df["description"] = df["description"].apply(lambda x: shorten_text(x, 100))
        if "summary" in df.columns:
            df["summary"] = df["summary"].apply(lambda x: shorten_text(x, 100))
        if "link" in df.columns:
            df["link"] = df["link"].apply(lambda x: f'<a href="{x}" target="_blank">{x}</a>' if pd.notna(x) else x)
        return df

    # Display tables using expanders and improved styling
    with st.expander(f"🏢 Jobs ({len(jobs_data)})"):
        if not jobs_data.empty:
            st.data_editor(jobs_data.style.apply(highlight_missing), hide_index=True, width=900)
        else:
            st.warning("⚠️ No Jobs Data Available")

    with st.expander(f"📚 Courses ({len(courses_data)})"):
        if not courses_data.empty:
            st.data_editor(courses_data.style.apply(highlight_missing), hide_index=True, width=900)
        else:
            st.warning("⚠️ No Courses Data Available")

    with st.expander(f"🔬 Research ({len(research_data)})"):
        if not research_data.empty:
            st.data_editor(research_data.style.apply(highlight_missing), hide_index=True, width=900)
        else:
            st.warning("⚠️ No Research Data Available")

# Footer
st.markdown("<br><br><p style='text-align: center; color: gray;'>Developed by Group 34 🚀</p>", unsafe_allow_html=True)

