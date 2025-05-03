import os
import sys
import psutil  # Added for system metrics
import pyarrow  # Added for Parquet support
import logging  # Added for logging
from logging.handlers import TimedRotatingFileHandler
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
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
import base64
import re

# Custom MemoryHandler to store logs in memory for live display
class MemoryHandler(logging.Handler):
    def __init__(self, capacity=1000):
        super().__init__()
        self.capacity = capacity
        self.logs = []
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    def emit(self, record):
        log_entry = self.format(record)
        self.logs.append(log_entry)
        if len(self.logs) > self.capacity:
            self.logs.pop(0)  # Remove oldest log to maintain capacity

    def get_logs(self):
        return self.logs

# Setup logging
log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_dir, exist_ok=True)  # Create logs directory if it doesn't exist

logger = logging.getLogger("LiveFeedLogger")
logger.setLevel(logging.INFO)

# CSV formatter for logs (for file handler)
class CSVFormatter(logging.Formatter):
    def format(self, record):
        timestamp = self.formatTime(record)
        username = getattr(record, 'username', 'Unknown')
        action = getattr(record, 'action', 'Unknown')
        details = getattr(record, 'details', 'No details')
        return f"{timestamp},{username},{action},{details}"

# Daily rotating file handler with header
class CustomTimedRotatingFileHandler(TimedRotatingFileHandler):
    def doRollover(self):
        super().doRollover()
        with open(self.baseFilename, 'a') as f:
            f.write("Timestamp,Username,Action,Details\n")

# File handler for CSV logs
log_file = os.path.join(log_dir, "live_feed_log")
file_handler = CustomTimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=30, encoding="utf-8")
file_handler.setFormatter(CSVFormatter())
file_handler.suffix = "%Y-%m-%d.csv"

if not os.path.exists(log_file + f".{datetime.now().strftime('%Y-%m-%d')}.csv"):
    with open(log_file + f".{datetime.now().strftime('%Y-%m-%d')}.csv", 'a') as f:
        f.write("Timestamp,Username,Action,Details\n")

# StreamHandler for terminal output
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# MemoryHandler for live display in Streamlit
memory_handler = MemoryHandler(capacity=1000)

# Add all handlers to logger
logger.addHandler(file_handler)
logger.addHandler(stream_handler)
logger.addHandler(memory_handler)

# Load environment variables from .env file (for local development only, excluding credentials)
if not os.getenv("IS_STREAMLIT_CLOUD", False):
    try:
        from dotenv import load_dotenv
        load_dotenv()  # Only for non-credential env vars like SENDGRID_API_KEY locally
    except ImportError:
        pass

# Set page configuration
st.set_page_config(page_title="📊 LSU Datastore", layout="centered")

# Determine color scheme based on login status
if st.session_state.get('logged_in', False):
    background_color = "#F5F6F5"
    main_background = "#FFFFFF"
    sidebar_background = "#E8ECEF"
    primary_color = "#0056D2"
    secondary_color = "#003087"
    text_color = "#333333"
    text_light_color = "#666666"
else:
    background_color = "url('bck.jpg')"
    main_background = "rgba(255, 255, 255, 0.9)"
    sidebar_background = "#461D7C"
    primary_color = "#461D7C"
    secondary_color = "#FABD00"
    text_color = "#000000"
    text_light_color = "#461D7C"

# Custom CSS with dynamic color scheme and terminal styling
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
        @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');

        /* General Styling */
        body, .stApp {{
            background: {background_color} !important;
            background-size: cover !important;
            background-position: center !important;
            color: {text_color} !important;
            font-family: 'Roboto', sans-serif !important;
        }}

        /* Main content area */
        .main {{
            background-color: {main_background};
            padding: 40px;
            margin: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}

        p {{
            font-size: 16px !important;
            line-height: 1.6 !important;
            color: {text_light_color} !important;
            font-weight: bold !important;
        }}

        /* Sidebar */
        .stSidebar {{
            background-color: {sidebar_background} !important;
            padding: 20px !important;
        }}
        .stSidebar .sidebar-content {{
            width: 200px !important;
        }}
        .stSidebar h2 {{
            font-size: 18px !important;
            color: #FFFFFF !important;
            margin-bottom: 10px !important;
            font-weight: bold !important;
        }}
        .stSidebar a, .stSidebar .stSelectbox label {{
            color: {secondary_color} !important;
            text-decoration: underline !important;
            font-size: 14px !important;
        }}
        .stSidebar a:hover {{
            color: {secondary_color} !important;
            text-decoration: underline !important;
        }}
        .stSidebar p {{
            font-size: 16px !important;
            line-height: 1.6 !important;
            color: {secondary_color} !important;
            font-weight: bold !important;
        }}
        .stSidebar .stButton p {{
            font-size: 16px !important;
            line-height: 1.6 !important;
            color: {text_light_color} !important;
            font-weight: bold !important;
        }}

        /* Headers and text */
        h1, h2, h3 {{
            color: {text_color} !important;
            font-family: 'Roboto', sans-serif !important;
            font-weight: bold !important;
        }}
        h1 {{
            font-size: 32px !important;
            margin-bottom: 10px !important;
        }}
        h2 {{
            font-size: 24px !important;
            margin-top: 30px !important;
            margin-bottom: 15px !important;
        }}
        

        /* Images */
        .ras-image {{
            max-width: 100%;
            border: 2px solid {primary_color};
            border-radius: 8px;
        }}

        /* Logo Image */
        .logo-image {{
            max-width: 50%; /* Smaller size, proportional to container */
            display: block;
            margin: 0 auto;
            border: 2px solid {primary_color};
            border-radius: 8px;
        }}

        /* Buttons */
        .stButton>button, .stDownloadButton>button{{
            background-color: {secondary_color};
            color: #FFFFFF;
            border-radius: 5px;
            padding: 8px 16px;
            font-weight: bold;
            border: none;
            transition: background-color 0.3s;
        }}
        .stButton>button:hover, .stDownloadButton>button:hover {{
            background-color: {secondary_color};
        }}
        section[data-testid="stSidebar"] .stButton>button {{
            background-color: {secondary_color} !important;
            opacity: 1 !important;
            visibility: visible !important;
            display: block !important;
            margin-bottom: 10px !important;
        }}
        section[data-testid="stSidebar"] .stButton>button:hover {{
            background-color: {secondary_color} !important;
            opacity: 1 !important;
            visibility: visible !important;
        }}
        .filter-container {{
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }}

        .demo-info {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
            justify-content: center;
        }}
        .demo-text {{
            font-size: 14px;
            color: {text_light_color};
            font-weight: bold;
        }}
        .live-demo-badge {{
            background: linear-gradient(45deg, {primary_color}, {secondary_color});
            color: #FFFFFF;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 700;
            text-transform: uppercase;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
            display: flex;
            align-items: center;
            gap: 5px;
            animation: pulse 2s infinite;
        }}
        .live-demo-badge i {{
            color: #FFFFFF;
        }}
        @keyframes pulse {{
            0% {{
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
            }}
            50% {{
                box-shadow: 0 2px 15px rgba(0, 0, 0, 0.5);
            }}
            100% {{
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
            }}
        }}

        .terminal-log {{
            background-color: #000000;
            color: #FFFFFF;
            font-family: 'Courier New', Courier, monospace;
            font-size: 14px;
            padding: 15px;
            border-radius: 5px;
            height: 300px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
            border: 1px solid #333;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }}
    </style>
""", unsafe_allow_html=True)

# Session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'show_lsu_datastore' not in st.session_state:
    st.session_state.show_lsu_datastore = False
if 'page' not in st.session_state:
    st.session_state.page = "Home"  # Default page

# Sidebar Navigation
with st.sidebar:
    st.header("DATABASE-RELATED LINKS")
    st.markdown("[GitHub Page](https://github.com/CSC-3380-Spring-2025/Team-34)")

    # Navigation selectbox (replacing SOFTWARE-RELATED LINKS)
    st.header("NAVIGATION")
    page = st.selectbox(
        "Navigate to:",
        ["Home", "Blank Page"],
        key="page_select",
        index=["Home", "Blank Page"].index(st.session_state.page)
    )
    st.session_state.page = page

    # Show SOFTWARE-RELATED LINKS only after login
    if st.session_state.logged_in:
        st.header("SOFTWARE-RELATED LINKS")
        st.markdown("[BioPython](https://biopython.org/)")
        st.markdown("[RDKit](https://www.rdkit.org/)")
        st.markdown("[PDBrenum](https://pdbrenumbering.org/)")
        st.markdown("[fpocket](https://github.com/Discngine/fpocket)")
        st.markdown("[PyMOL](https://pymol.org/)")
        st.markdown("[3dmol](https://3dmol.csb.pitt.edu/)")
        st.markdown("[pandas](https://pandas.pydata.org/)")
        st.markdown("[NumPy](https://numpy.org/)")
        st.markdown("[SciPy](https://scipy.org/)")
        st.markdown("[sklearn](https://scikit-learn.org/)")
        st.markdown("[matplotlib](https://matplotlib.org/)")
        st.markdown("[seaborn](https://seaborn.pydata.org/)")
        st.markdown("[streamlit](https://streamlit.io/)")

    # Sidebar Login Panel
    st.header("USER LOGIN")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login"):
        st.empty()
        with st.spinner("Logging in..."):
            time.sleep(3)
        # Use credentials from TOML file via st.secrets
        try:
            toml_username = st.secrets["USERNAME"]
            toml_password = st.secrets["PASSWORD"]
        except KeyError as e:
            st.error(f"Missing secret in TOML file: {str(e)}. Please ensure USERNAME and PASSWORD are defined.")
            st.rerun()
        # First attempt authentication using authenticate_user
        auth_success = authenticate_user(username, password)
        # Fallback: compare against TOML secrets if authenticate_user fails
        if not auth_success:
            auth_success = (username == toml_username and password == toml_password)
        if auth_success:
            st.session_state.logged_in = True
            st.session_state.username = username
            # Check if the user matches the TOML secrets for special access
            st.session_state.show_lsu_datastore = (username == toml_username and password == toml_password)
            st.success(f"Logged in as {username}!")
            st.rerun()
        else:
            st.error("Invalid credentials")
            st.rerun()

    if st.session_state.logged_in:
        if st.button("Logout"):
            st.empty()
            with st.spinner("Logging out..."):
                time.sleep(3)
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.show_lsu_datastore = False
            st.rerun()

# Main Content Area
with st.container():
    st.markdown(f"""
        <div class="demo-info">
            <span class="demo-text">Demo 1.3.3</span>
            <span class="live-demo-badge"><i class="fas fa-rocket"></i> Live Demo</span>
        </div>
    """, unsafe_allow_html=True)

    if page == "Blank Page":
        st.markdown('<div class="main">', unsafe_allow_html=True)
        st.header("Blank Page")
        st.subheader("View all CSV files in the LSU Datastore")

        files = get_files()
        if files:
            file_options = {file_id: filename for file_id, filename, _, _, _ in files}
            selected_file_id = st.selectbox(
                "Select a CSV file to preview:",
                options=file_options.keys(),
                format_func=lambda x: file_options[x],
                key="blank_page_csv_select"
            )
            if selected_file_id:
                logger.info(
                    "CSV File Selected",
                    extra={
                        "username": st.session_state.username or "Anonymous",
                        "action": "blank_page_csv_select",
                        "details": f"Selected dataset: {file_options[selected_file_id]}"
                    }
                )
                df = get_csv_preview(selected_file_id)
                if not df.empty:
                    st.write(f"**Preview of {file_options[selected_file_id]}:**")
                    st.dataframe(df, hide_index=True)

                    # Download options
                    st.subheader("Download Data")
                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        csv_data = df.to_csv(index=False).encode("utf-8")
                        if st.download_button(
                            label="Download CSV",
                            data=csv_data,
                            file_name=f"{file_options[selected_file_id]}.csv",
                            mime="text/csv",
                            key="download_csv_blank_page"
                        ):
                            logger.info(
                                "CSV Downloaded",
                                extra={
                                    "username": st.session_state.username or "Anonymous",
                                    "action": "download_csv_blank_page",
                                    "details": f"Downloaded: {file_options[selected_file_id]}.csv"
                                }
                            )
                    with col_dl2:
                        parquet_buffer = io.BytesIO()
                        df.to_parquet(parquet_buffer, engine="pyarrow", index=False)
                        parquet_data = parquet_buffer.getvalue()
                        if st.download_button(
                            label="Download Parquet",
                            data=parquet_data,
                            file_name=f"{file_options[selected_file_id]}.parquet",
                            mime="application/octet-stream",
                            key="download_parquet_blank_page"
                        ):
                            logger.info(
                                "Parquet Downloaded",
                                extra={
                                    "username": st.session_state.username or "Anonymous",
                                    "action": "download_parquet_blank_page",
                                    "details": f"Downloaded: {file_options[selected_file_id]}.parquet"
                                }
                            )
                else:
                    st.error("No data found in the selected dataset.")
        else:
            st.warning("No CSV files available in the database.")
        st.markdown('</div>', unsafe_allow_html=True)

    else:  # Home page
        st.markdown('<div class="main">', unsafe_allow_html=True)

        st.header("LSU Datastore")
        st.subheader("A tool for managing and analyzing data at LSU")
        st.markdown("Created by the LSU Data Science Team", unsafe_allow_html=True)
        st.markdown("Powered by Streamlit", unsafe_allow_html=True)

        base_dir = os.path.dirname(__file__)
        try:
            st.image(os.path.join(base_dir, "lsu_data_icon.png"), caption="LSU Datastore Visualization", use_container_width=True, output_format="PNG")
        except FileNotFoundError:
            st.warning("Image not found. Please add 'lsu_data_icon.png' to your project directory.")

        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        col1, col2, _ = st.columns([1, 1, 3])
        with col1:
            majors = ["software_engineering", "cloud_computing", "data_science", "cybersecurity"]
            selected_major = st.selectbox("Filter by Major:", majors, format_func=lambda x: x.replace("_", " ").title())
        with col2:
            categories = ["jobs", "courses", "research", "lsu"]
            selected_category = st.selectbox("Filter by Category:", categories, format_func=lambda x: x.title() if x == "lsu" else x.capitalize())
        st.markdown('</div>', unsafe_allow_html=True)

        st.subheader("Summary")
        st.markdown("""
            The LSU Datastore is a tool for managing and analyzing datasets at LSU, including research projects, jobs, and courses.
            The Datastore provides a continuously updated platform for accessing data, performing searches, and sharing insights.
            Details of our work are provided in the LSU Data Science Repository.
            We hope that researchers will use the LSU Datastore to gain insights into academic and professional opportunities.
        """)

        st.subheader("Usage")
        st.markdown("""
            To the left is a dropdown menu for navigating the LSU Datastore features:

            - **Home Page**: Overview of the LSU Datastore platform.
            - **Blank Page**: View all CSV files in the LSU Datastore (no login required).
            - **Database Overview**: View and manage datasets stored in the LSU Datastore.
            - **Search Data**: Search for specific entries across all datasets.
            - **Visualize Data**: Explore data visualizations for numerical datasets.
            - **Share Data**: Share datasets via email with collaborators.
            - **Manage Data**: Upload, edit, and delete datasets (requires login).
        """)

        st.subheader("LSU Datastore - Livestream Data Store")
        st.markdown("Select a date to view Jobs, Courses, Research Projects, or LSU-specific data for that day.")

        selected_date = st.date_input("Select a date:", value=datetime.now(), key="date_select")
        formatted_date = selected_date.strftime("%Y-%m-%d")

        files = get_files()
        if files:
            file_options = {}
            for file_id, filename, _, _, _ in files:
                if selected_category == "lsu":
                    if (filename.lower().startswith("lsu") and
                        formatted_date in filename and
                        (selected_major in filename or "relevant" in filename)):
                        file_options[file_id] = filename
                else:
                    if (selected_category in filename and
                        formatted_date in filename and
                        selected_major in filename):
                        file_options[file_id] = filename

            if file_options:
                col1, col2 = st.columns([3, 1])
                with col1:
                    selected_file_id = st.selectbox(
                        "Select a dataset to preview:",
                        options=file_options.keys(),
                        format_func=lambda x: file_options[x],
                        key="live_select"
                    )
                    if selected_file_id:
                        logger.info(
                            "Dataset Selected",
                            extra={
                                "username": st.session_state.username or "Anonymous",
                                "action": "select_dataset",
                                "details": f"Selected dataset: {file_options[selected_file_id]}"
                            }
                        )
                        df = get_csv_preview(selected_file_id)
                        if not df.empty:
                            st.write(f"**Preview of {file_options[selected_file_id]}:**")
                            st.dataframe(df, hide_index=True)

                            st.subheader("Download Data")
                            col_dl1, col_dl2 = st.columns(2)
                            with col_dl1:
                                csv_data = df.to_csv(index=False).encode("utf-8")
                                if st.download_button(
                                    label="Download CSV",
                                    data=csv_data,
                                    file_name=f"{file_options[selected_file_id]}.csv",
                                    mime="text/csv",
                                    key="download_csv_live"
                                ):
                                    logger.info(
                                        "CSV Downloaded",
                                        extra={
                                            "username": st.session_state.username or "Anonymous",
                                            "action": "download_csv",
                                            "details": f"Downloaded: {file_options[selected_file_id]}.csv"
                                        }
                                    )
                            with col_dl2:
                                parquet_buffer = io.BytesIO()
                                df.to_parquet(parquet_buffer, engine="pyarrow", index=False)
                                parquet_data = parquet_buffer.getvalue()
                                if st.download_button(
                                    label="Download Parquet",
                                    data=parquet_data,
                                    file_name=f"{file_options[selected_file_id]}.parquet",
                                    mime="application/octet-stream",
                                    key="download_parquet_live"
                                ):
                                    logger.info(
                                        "Parquet Downloaded",
                                        extra={
                                            "username": st.session_state.username or "Anonymous",
                                            "action": "download_parquet",
                                            "details": f"Downloaded: {file_options[selected_file_id]}.parquet"
                                        }
                                    )

                            st.subheader("Share Data via Email")
                            email_input = st.text_input("Enter your email address:", key="email_live")
                            if st.button("Send Data", key="send_live"):
                                if email_input:
                                    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                                    if not re.match(email_regex, email_input):
                                        st.error("Invalid email address format.")
                                        logger.info(
                                            "Email Share Failed",
                                            extra={
                                                "username": st.session_state.username or "Anonymous",
                                                "action": "email_share",
                                                "details": f"Invalid email format: {email_input}"
                                            }
                                        )
                                    else:
                                        try:
                                            csv_buffer = io.StringIO()
                                            df.to_csv(csv_buffer, index=False)
                                            csv_data = csv_buffer.getvalue().encode('utf-8')
                                            encoded_file = base64.b64encode(csv_data).decode()

                                            message = Mail(
                                                from_email='bdav213@lsu.edu',
                                                to_emails=email_input,
                                                subject=f'LSU Datastore: {file_options[selected_file_id]} Data',
                                                html_content=f'<p>Attached is the data from {file_options[selected_file_id]} as viewed on the LSU Datastore Dashboard.</p>'
                                            )

                                            attachment = Attachment(
                                                FileContent(encoded_file),
                                                FileName(file_options[selected_file_id]),
                                                FileType('text/csv'),
                                                Disposition('attachment')
                                            )
                                            message.attachment = attachment

                                            sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
                                            response = sg.send(message)

                                            if response.status_code == 202:
                                                st.success(f"Data sent to {email_input}!")
                                                logger.info(
                                                    "Email Share Success",
                                                    extra={
                                                        "username": st.session_state.username or "Anonymous",
                                                        "action": "email_share",
                                                        "details": f"Sent to: {email_input}, Dataset: {file_options[selected_file_id]}"
                                                    }
                                                )
                                            else:
                                                st.error(f"Failed to send email. Status code: {response.status_code}")
                                                logger.info(
                                                    "Email Share Failed",
                                                    extra={
                                                        "username": st.session_state.username or "Anonymous",
                                                        "action": "email_share",
                                                        "details": f"Failed, Status code: {response.status_code}, Dataset: {file_options[selected_file_id]}"
                                                    }
                                                )
                                        except Exception as e:
                                            st.error(f"Error sending email: {str(e)}")
                                            logger.info(
                                                "Email Share Error",
                                                extra={
                                                    "username": st.session_state.username or "Anonymous",
                                                    "action": "email_share",
                                                    "details": f"Error: {str(e)}, Dataset: {file_options[selected_file_id]}"
                                                }
                                            )
                                else:
                                    st.warning("Please enter an email address.")
                                    logger.info(
                                        "Email Share Failed",
                                        extra={
                                            "username": st.session_state.username or "Anonymous",
                                            "action": "email_share",
                                            "details": "No email address provided"
                                        }
                                    )
                        else:
                            st.error("No data found in the selected dataset.")
                with col2:
                    try:
                        st.markdown(
                            f'<div class="logo-image"><img src="data:image/png;base64,{base64.b64encode(open(os.path.join(base_dir, "lsu_logo.png"), "rb").read()).decode()}" alt="LSU Datastore Process" style="width:100%;"></div>',
                            unsafe_allow_html=True
                        )
                        st.caption("LSU Datastore Process")
                    except FileNotFoundError:
                        st.warning("Image not found. Please add 'lsu_logo.png' to your project directory.")
            else:
                st.warning(f"No {selected_category.upper() if selected_category == 'lsu' else selected_category.capitalize()} data available for {selected_major.replace('_', ' ').capitalize()} on {formatted_date}.")
        else:
            st.warning("No datasets uploaded yet.")

        if files and file_options and selected_file_id and not df.empty:
            st.subheader("Visualize Data")
            numerical_cols = df.select_dtypes(include=["number"]).columns
            if len(numerical_cols) > 0:
                x_axis = st.selectbox("Select X-Axis:", numerical_cols, key="x_axis")
                y_axis = st.selectbox("Select Y-Axis:", numerical_cols, key="y_axis")
                fig = px.scatter(df, x=x_axis, y=y_axis, title=f"{x_axis} vs {y_axis}")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No numerical columns found for visualization.")

        st.subheader("Search Data")
        global_search = st.text_input("Search across all datasets:")
        if global_search:
            results = search_csv_data(global_search)
            if results:
                st.dataframe(pd.DataFrame(results, columns=["File ID", "Row", "Column", "Value"]))
            else:
                st.warning("No matches found.")

        st.subheader("System Performance Metrics")
        placeholder = st.empty()
        for _ in range(60):
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_usage = psutil.virtual_memory().percent
            with placeholder.container():
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("CPU Usage", f"{cpu_usage}%")
                with col2:
                    st.metric("Memory Usage", f"{memory_usage}%")

        if st.session_state.logged_in:
            st.subheader("Live Feed Logs")
            st.markdown("View and download daily logs of live feed activities for testing and optimization.")
           
            log_files = [f for f in os.listdir(log_dir) if f.startswith("live_feed_log") and f.endswith(".csv")]
            if log_files:
                selected_log = st.selectbox("Select a log file to view:", log_files, key="log_select")
                if selected_log:
                    log_path = os.path.join(log_dir, selected_log)
                    try:
                        log_df = pd.read_csv(log_path)
                        st.write(f"**Log: {selected_log}**")
                        st.dataframe(log_df, hide_index=True)
                       
                        log_csv = log_df.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            label="Download Log as CSV",
                            data=log_csv,
                            file_name=selected_log,
                            mime="text/csv",
                            key="download_log_csv"
                        )
                    except Exception as e:
                        st.error(f"Error reading log file: {str(e)}")
            else:
                st.warning("No log files available.")

        if st.session_state.logged_in:
            st.subheader("Live Terminal Logs")
            st.markdown("View live logs in a terminal-like interface.")
            log_placeholder = st.empty()
            for _ in range(60):
                logs = memory_handler.get_logs()
                log_text = "\n".join(logs[-20:])
                log_placeholder.markdown(
                    f'<div class="terminal-log">{log_text}</div>',
                    unsafe_allow_html=True
                )
                time.sleep(1)

        if st.session_state.logged_in:
            st.subheader("Manage Data")
            uploaded_file = st.file_uploader("Upload dataset (CSV)", type=["csv"])
            if uploaded_file:
                with st.spinner("Uploading dataset..."):
                    save_csv_data(uploaded_file.name, uploaded_file.getvalue(), len(uploaded_file.getvalue()), "csv", 1)
                    time.sleep(1)
                st.success(f"{uploaded_file.name} saved to the database!")

            if files:
                st.write("**Manage Stored Datasets:**")
                manage_file_id = st.selectbox("Select a dataset to manage:", options=file_options.keys(), format_func=lambda x: file_options[x], key="manage_select")
                if manage_file_id:
                    manage_df = get_csv_preview(manage_file_id)
                    if not manage_df.empty:
                        st.write(f"**Preview of {file_options[manage_file_id]}:**")
                        st.dataframe(manage_df)

                        st.subheader("Edit Data")
                        edited_df = st.data_editor(manage_df)
                        if st.button("Save Changes"):
                            update_csv_data(manage_file_id, edited_df)
                            st.success("Changes saved!")

                        csv_data = manage_df.to_csv(index=False).encode("utf-8")
                        json_data = manage_df.to_json(orient="records")
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            manage_df.to_excel(writer, index=False)
                        excel_data = output.getvalue()

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.download_button("Download CSV", data=csv_data, file_name=f"{file_options[manage_file_id]}.csv", mime="text/csv")
                        with col2:
                            st.download_button("Download JSON", data=json_data, file_name=f"{file_options[manage_file_id]}.json", mime="application/json")
                        with col3:
                            st.download_button("Download Excel", data=excel_data, file_name=f"{file_options[manage_file_id]}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

                        if st.button("Delete This Dataset"):
                            delete_file(manage_file_id)
                            st.success(f"Dataset '{file_options[manage_file_id]}' deleted!")
                            st.rerun()
                    else:
                        st.error("No data found in the selected dataset.")
            else:
                st.warning("No datasets uploaded yet.")

        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown("[Link to DAG Grid](https://animated-train-jjvx5x4q9g73p5v5-8080.app.github.dev/dags/fetch_store_dag/grid)")
