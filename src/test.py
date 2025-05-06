"""Streamlit application for the LSU Datastore Dashboard.

Provides a web interface for managing, visualizing, and sharing datasets at LSU,
with user authentication, data upload, search, and live logging features.
"""
import requests
import base64
import io
import logging
import os
import re
import sys
import time
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from typing import Dict, List, Optional, Tuple

import pandas as pd
import plotly.express as px
import psutil
import pyarrow
import streamlit as st
from pandas import DataFrame
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, Disposition, FileContent, FileName, FileType

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.datastore.database import (
    authenticate_user,
    delete_file,
    get_csv_preview,
    get_files,
    search_csv_data,
    update_csv_data,
    save_csv_to_database,
)

# Custom MemoryHandler for live log display
class MemoryHandler(logging.Handler):
    """Store logs in memory for live display in Streamlit."""

    def __init__(self, capacity: int = 1000) -> None:
        super().__init__()
        self.capacity = capacity
        self.logs: List[str] = []
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    def emit(self, record: logging.LogRecord) -> None:
        log_entry = self.format(record)
        self.logs.append(log_entry)
        if len(self.logs) > self.capacity:
            self.logs.pop(0)  # Remove oldest log

    def get_logs(self) -> List[str]:
        return self.logs

# CSV formatter for file logs
class CSVFormatter(logging.Formatter):
    """Format logs as CSV for file storage."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record)
        username = getattr(record, 'username', 'Unknown')
        action = getattr(record, 'action', 'Unknown')
        details = getattr(record, 'details', 'No details')
        return f'{timestamp},{username},{action},{details}'

# Daily rotating file handler with header
class CustomTimedRotatingFileHandler(TimedRotatingFileHandler):
    """Rotate log files daily and add CSV header on rollover."""

    def doRollover(self) -> None:
        super().doRollover()
        with open(self.baseFilename, 'a') as f:
            f.write('Timestamp,Username,Action,Details\n')

# Helper function to safely get secrets
def get_secret(key: str, default: str) -> str:
    """Retrieve a secret from environment variables, concatenating SendGrid API key parts if needed.

    Args:
        key (str): The key to look up.
        default (str): The default value if the key is not found.

    Returns:
        str: The value of the key or the default.
    """
    if key == 'SENDGRID_API_KEY':
        part1 = os.getenv('SENDGRID_API_KEY_PART1', '')
        part2 = os.getenv('SENDGRID_API_KEY_PART2', '')
        part3 = os.getenv('SENDGRID_API_KEY_PART3', '')
        if part1 and part2 and part3:
            return part1 + part2 + part3
        return default
    return os.getenv(key, default)

# Setup logging
log_dir = os.path.join(os.path.dirname(__file__), get_secret("LOG_DIR", "logs"))
os.makedirs(log_dir, exist_ok=True)

logger = logging.getLogger('LiveFeedLogger')
logger.setLevel(logging.INFO)

log_file = os.path.join(log_dir, get_secret("LOG_FILE", "live_feed_log"))
file_handler = CustomTimedRotatingFileHandler(
    log_file, when='midnight', interval=1, backupCount=30, encoding='utf-8'
)
file_handler.setFormatter(CSVFormatter())
file_handler.suffix = '%Y-%m-%d.csv'

log_file_path = f'{log_file}.{datetime.now().strftime("%Y-%m-%d")}.csv'
if not os.path.exists(log_file_path):
    with open(log_file_path, 'a') as f:
        f.write('Timestamp,Username,Action,Details\n')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

memory_handler = MemoryHandler(capacity=1000)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)
logger.addHandler(memory_handler)

# Set page configuration
st.set_page_config(page_title='📊 LSU Datastore', layout='centered')

# Color scheme based on login status
if st.session_state.get('logged_in', False):
    background_color = '#F5F6F5'
    main_background = '#FFFFFF'
    sidebar_background = '#E8ECEF'
    primary_color = '#0056D2'
    secondary_color = '#003087'
    text_color = '#333333'
    text_light_color = '#666666'
else:
    background_color = "url('bck.jpg')"
    main_background = 'rgba(255, 255, 255, 0.9)'
    sidebar_background = '#461D7C'
    primary_color = '#461D7C'
    secondary_color = '#FABD00'
    text_color = '#000000'
    text_light_color = '#461D7C'

# Custom CSS
st.markdown(
    f"""
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
            max-width: 50%;
            display: block;
            margin: 0 auto;
            border: 2px solid {primary_color};
            border-radius: 8px;
        }}
        /* Buttons */
        .stButton>button, .stDownloadButton>button {{
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
            0% {{ box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3); }}
            50% {{ box-shadow: 0 2px 15px rgba(0, 0, 0, 0.5); }}
            100% {{ box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3); }}
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
    """,
    unsafe_allow_html=True,
)

# Session state initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'show_lsu_datastore' not in st.session_state:
    st.session_state.show_lsu_datastore = False
if 'page' not in st.session_state:
    st.session_state.page = 'Home'

def send_dataset_email(email: str, filename: str, df: DataFrame) -> bool:
    """Send a dataset as a CSV attachment via email using SendGrid.

    Args:
        email (str): Recipient email address.
        filename (str): Name of the dataset file.
        df (DataFrame): DataFrame containing the dataset.

    Returns:
        bool: True if the email was sent successfully, False otherwise.
    """
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        st.error(f'Invalid email address format: {email}')
        logger.error(
            'Email Share Failed',
            extra={
                'username': st.session_state.username or 'Anonymous',
                'action': 'email_share',
                'details': f'Invalid email format: {email}',
            },
        )
        return False

    # Retrieve SendGrid API key from environment variables
    api_key = get_secret('SENDGRID_API_KEY', '')
    if not api_key:
        st.error("SendGrid API key not found in environment variables. Please set SENDGRID_API_KEY_PART1, SENDGRID_API_KEY_PART2, and SENDGRID_API_KEY_PART3 in .env.")
        logger.error(
            'Email Share Failed',
            extra={
                'username': st.session_state.username or 'Anonymous',
                'action': 'email_share',
                'details': 'No SendGrid API key found in environment variables',
            },
        )
        return False

    try:
        # Prepare the email data
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue().encode('utf-8')
        encoded_file = base64.b64encode(csv_data).decode()

        email_data = {
            "personalizations": [{"to": [{"email": email}]}],
            "from": {"email": get_secret("FROM_EMAIL", "default@example.com")},
            "subject": f"LSU Datastore: {filename} Data",
            "content": [
                {
                    "type": "text/html",
                    "value": f"<p>Attached is the data from {filename} as viewed on the LSU Datastore Dashboard.</p>",
                }
            ],
            "attachments": [
                {
                    "content": encoded_file,
                    "filename": filename,
                    "type": "text/csv",
                    "disposition": "attachment",
                }
            ],
        }

        # First attempt: Try with SSL verification enabled
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=email_data,
                headers=headers,
            )
            response.raise_for_status()  # Raise an exception for HTTP errors
        except requests.exceptions.SSLError as ssl_err:
            # SSL verification failed; retry with verification disabled
            st.warning(
                "SSL certificate verification failed. Retrying with SSL verification disabled. "
                "This is less secure and should be fixed by updating your system's CA certificates "
                "or configuring your network proxy certificates."
            )
            logger.warning(
                'SSL Verification Failed - Retrying with Disabled Verification',
                extra={
                    'username': st.session_state.username or 'Anonymous',
                    'action': 'email_share',
                    'details': f'SSL error: {str(ssl_err)}, retrying without verification',
                },
            )
            response = requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=email_data,
                headers=headers,
                verify=False,  # Disable SSL verification
            )
            response.raise_for_status()

        if response.status_code == 202:
            logger.info(
                'Email Share Success',
                extra={
                    'username': st.session_state.username or 'Anonymous',
                    'action': 'email_share',
                    'details': f'Sent to: {email}, Dataset: {filename}',
                },
            )
            return True
        st.error(f'Failed to send email. Status code: {response.status_code}')
        logger.error(
            'Email Share Failed',
            extra={
                'username': st.session_state.username or 'Anonymous',
                'action': 'email_share',
                'details': f'Failed, Status code: {response.status_code}, Dataset: {filename}',
            },
        )
        return False
    except Exception as e:
        st.error(f'Error sending email: {str(e)}')
        logger.error(
            'Email Share Error',
            extra={
                'username': st.session_state.username or 'Anonymous',
                'action': 'email_share',
                'details': f'Error: {str(e)}, Dataset: {filename}',
            },
        )
        return False

@st.cache_data
def cached_get_files() -> List[Tuple[int, str, int, str, datetime]]:
    """Retrieve cached file metadata from the database.

    Returns:
        List[Tuple[int, str, int, str, datetime]]: List of file metadata tuples.
    """
    return get_files()

@st.cache_data
def cached_get_csv_preview(file_id: int) -> DataFrame:
    """Retrieve cached CSV data preview for a file.

    Args:
        file_id (int): ID of the file to preview.

    Returns:
        DataFrame: Preview DataFrame or empty if no data.
    """
    return get_csv_preview(file_id)

def render_sidebar() -> None:
    """Render the sidebar with navigation and login panel."""
    with st.sidebar:
        st.header('DATABASE-RELATED LINKS')
        st.markdown('[GitHub Page](https://github.com/CSC-3380-Spring-2025/Team-34)')

        st.header('NAVIGATION')
        pages = ['Home', 'data Page', '🔍 Search Data', '📊 Visualize Data', '📤 Share Data']
        
        # Initialize session state if not already set
        if 'page' not in st.session_state:
            st.session_state.page = 'Home'

        # Use selectbox to navigate
        page = st.selectbox(
            'Navigate to:',
            pages,
            index=pages.index(st.session_state.page),
            key='page_select',
        )

        # Update session state only if the selection changes
        if page != st.session_state.page:
            st.session_state.page = page
            st.rerun()  # Force rerun to reflect the new page immediately

        if st.session_state.logged_in:
            st.header('SOFTWARE-RELATED LINKS')
            st.markdown('[BioPython](https://biopython.org/)')
            st.markdown('[RDKit](https://www.rdkit.org/)')
            st.markdown('[PDBrenum](https://pdbrenumbering.org/)')
            st.markdown('[fpocket](https://github.com/Discngine/fpocket)')
            st.markdown('[PyMOL](https://pymol.org/)')
            st.markdown('[3dmol](https://3dmol.csb.pitt.edu/)')
            st.markdown('[pandas](https://pandas.pydata.org/)')
            st.markdown('[NumPy](https://numpy.org/)')
            st.markdown('[SciPy](https://scipy.org/)')
            st.markdown('[sklearn](https://scikit-learn.org/)')
            st.markdown('[matplotlib](https://matplotlib.org/)')
            st.markdown('[seaborn](https://seaborn.pydata.org/)')
            st.markdown('[streamlit](https://streamlit.io/)')

        st.header('USER LOGIN')
        username = st.text_input('Username', key='login_username')
        password = st.text_input('Password', type='password', key='login_password')
        if st.button('Login'):
            with st.spinner('Logging in...'):
                time.sleep(3)
            try:
                toml_username = get_secret("USERNAME", "admin")
                toml_password = get_secret("PASSWORD", "NewSecurePassword123")
            except KeyError as e:
                st.error(f'Missing secret: {str(e)}. Ensure USERNAME and PASSWORD are defined.')
            else:
                auth_success = authenticate_user(username, password) or (
                    username == toml_username and password == toml_password
                )
                if auth_success:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.show_lsu_datastore = (
                        username == toml_username and password == toml_password
                    )
                    st.success(f'Logged in as {username}!')
                    st.rerun()
                else:
                    st.error('Invalid credentials')
                    st.rerun()

        if st.session_state.logged_in:
            if st.button('Logout'):
                with st.spinner('Logging out...'):
                    time.sleep(3)
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.show_lsu_datastore = False
                st.session_state.page = '🔍 Search Data'
                st.rerun()

def render_data_page() -> None:
    """Render the data Page for viewing CSV files."""
    st.markdown('<div class="main">', unsafe_allow_html=True)
    st.header('data Page')
    st.subheader('View all CSV files in the LSU Datastore')

    files = cached_get_files()
    if files:
        file_options = {file_id: filename for file_id, filename, _, _, _ in files}
        selected_file_id = st.selectbox(
            'Select a CSV file to preview:',
            options=file_options.keys(),
            format_func=lambda x: file_options[x],
            key='data_page_csv_select',
        )
        if selected_file_id:
            logger.info(
                'CSV File Selected',
                extra={
                    'username': st.session_state.username or 'Anonymous',
                    'action': 'data_page_csv_select',
                    'details': f'Selected dataset: {file_options[selected_file_id]}',
                },
            )
            df = cached_get_csv_preview(selected_file_id)
            if not df.empty:
                st.write(f'**Preview of {file_options[selected_file_id]}:**')
                st.dataframe(df, hide_index=True)

                st.subheader('Download Data')
                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    csv_data = df.to_csv(index=False).encode('utf-8')
                    if st.download_button(
                        label='Download CSV',
                        data=csv_data,
                        file_name=f'{file_options[selected_file_id]}.csv',
                        mime='text/csv',
                        key='download_csv_data_page',
                    ):
                        logger.info(
                            'CSV Downloaded',
                            extra={
                                'username': st.session_state.username or 'Anonymous',
                                'action': 'download_csv_data_page',
                                'details': f'Downloaded: {file_options[selected_file_id]}.csv',
                            },
                        )
                with col_dl2:
                    parquet_buffer = io.BytesIO()
                    df.to_parquet(parquet_buffer, engine='pyarrow', index=False)
                    parquet_data = parquet_buffer.getvalue()
                    if st.download_button(
                        label='Download Parquet',
                        data=parquet_data,
                        file_name=f'{file_options[selected_file_id]}.parquet',
                        mime='application/octet-stream',
                        key='download_parquet_data_page',
                    ):
                        logger.info(
                            'Parquet Downloaded',
                            extra={
                                'username': st.session_state.username or 'Anonymous',
                                'action': 'download_parquet_data_page',
                                'details': f'Downloaded: {file_options[selected_file_id]}.parquet',
                            },
                        )
            else:
                st.error('No data found in the selected dataset.')
    else:
        st.warning('No CSV files available in the database.')
    st.markdown('</div>', unsafe_allow_html=True)

def render_search_data_page() -> None:
    """Render the Search Data page for searching across datasets."""
    st.markdown('<div class="main">', unsafe_allow_html=True)
    st.header('Search Data')
    st.subheader('Search across all datasets')
    global_search = st.text_input('Search across all datasets:', key='global_search')
    if global_search:
        results = search_csv_data(global_search)
        if results:
            st.dataframe(
                pd.DataFrame(results, columns=['File ID', 'Row', 'Column', 'Value'])
            )
        else:
            st.warning('No matches found.')
    st.markdown('</div>', unsafe_allow_html=True)

def render_visualize_data_page() -> None:
    """Render the Visualize Data page for exploring data visualizations."""
    st.markdown('<div class="main">', unsafe_allow_html=True)
    st.header('Visualize Data')
    st.subheader('Explore data visualizations')
    files = cached_get_files()
    if files:
        file_options = {file_id: filename for file_id, filename, _, _, _ in files}
        selected_file_id = st.selectbox(
            'Select a dataset to visualize:',
            options=file_options.keys(),
            format_func=lambda x: file_options[x],
            key='visualize_select',
        )
        if selected_file_id:
            df = cached_get_csv_preview(selected_file_id)
            if not df.empty:
                numerical_cols = df.select_dtypes(include=['number']).columns
                if len(numerical_cols) > 1:
                    x_axis = st.selectbox(
                        'Select X-Axis:', numerical_cols, index=1, key='x_axis'
                    )
                    y_axis = st.selectbox(
                        'Select Y-Axis:', numerical_cols, index=0, key='y_axis'
                    )
                    fig = px.scatter(df, x=x_axis, y=y_axis, title=f'{x_axis} vs {y_axis}')
                    st.plotly_chart(fig, use_container_width=True)
                elif len(numerical_cols) == 1:
                    st.warning('Only one numerical column was found; cannot plot.')
                else:
                    st.warning('No numerical columns found for visualization.')
            else:
                st.error('No data found in the selected dataset.')
    else:
        st.warning('No datasets uploaded yet.')
    st.markdown('</div>', unsafe_allow_html=True)

def render_share_data_page() -> None:
    """Render the Share Data page for emailing datasets."""
    st.markdown('<div class="main">', unsafe_allow_html=True)
    st.header('Share Data')
    st.subheader('Share datasets via email')
    files = cached_get_files()
    if files:
        file_options = {file_id: filename for file_id, filename, _, _, _ in files}
        selected_file_id = st.selectbox(
            'Select a dataset to share:',
            options=file_options.keys(),
            format_func=lambda x: file_options[x],
            key='share_select',
        )
        if selected_file_id:
            df = cached_get_csv_preview(selected_file_id)
            if not df.empty:
                email_input = st.text_input('Enter your email address:', key='email_share')
                
                if st.button('Send Data', key='send_share'):
                    if email_input:
                        success = send_dataset_email(
                            email_input,
                            file_options[selected_file_id],
                            df
                        )
                        if success:
                            st.success(f"Data sent to {email_input}!")
                        else:
                            st.error("Failed to send email.")
                    else:
                        st.warning('Please enter an email address.')
                        logger.error(
                            'Email Share Failed',
                            extra={
                                'username': st.session_state.username or 'Anonymous',
                                'action': 'email_share',
                                'details': 'No email address provided',
                            },
                        )
            else:
                st.error('No data found in the selected dataset.')
    else:
        st.warning('No datasets uploaded yet.')
    st.markdown('</div>', unsafe_allow_html=True)

def render_home_page() -> None:
    """Render the Home page with data management and live features."""
    st.markdown('<div class="main">', unsafe_allow_html=True)

    st.header('LSU Datastore')
    st.subheader('A tool for managing and analyzing data at LSU')
    st.markdown('Created by the LSU Data Science Team', unsafe_allow_html=True)
    st.markdown('Powered by Streamlit', unsafe_allow_html=True)

    base_dir = os.path.dirname(__file__)
    try:
        st.image(
            os.path.join(base_dir, 'lsu_data_icon.png'),
            caption='LSU Datastore Visualization',
            use_container_width=True,
            output_format='PNG',
        )
    except FileNotFoundError:
        st.warning("Image not found. Please add 'lsu_data_icon.png' to your project directory.")

    if st.session_state.logged_in:
        st.subheader('Manage Data')
        uploaded_file = st.file_uploader(
            'Upload dataset (CSV)', type=['csv'], key='upload_csv'
        )
        if uploaded_file:
            with st.spinner('Uploading dataset...'):
                save_csv_to_database(
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    len(uploaded_file.getvalue()),
                    'csv',
                    1,
                )
                time.sleep(1)
            st.success(f'{uploaded_file.name} saved to the database!')

        manage_files = cached_get_files()
        if manage_files:
            manage_file_options = {
                file_id: filename for file_id, filename, _, _, _ in manage_files
            }
            manage_file_id = st.selectbox(
                'Select a dataset to manage:',
                options=manage_file_options.keys(),
                format_func=lambda x: manage_file_options[x],
                key='manage_select',
            )
            if manage_file_id:
                manage_df = cached_get_csv_preview(manage_file_id)
                if not manage_df.empty:
                    st.write(f'**Preview of {manage_file_options[manage_file_id]}:**')
                    st.dataframe(manage_df)

                    st.subheader('Edit Data')
                    edited_df = st.data_editor(manage_df)
                    if st.button('Save Changes'):
                        update_csv_data(manage_file_id, edited_df)
                        st.success('Changes saved!')

                    csv_data = manage_df.to_csv(index=False).encode('utf-8')
                    json_data = manage_df.to_json(orient='records')
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        manage_df.to_excel(writer, index=False)
                    excel_data = output.getvalue()

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.download_button(
                            'Download CSV',
                            data=csv_data,
                            file_name=f'{manage_file_options[manage_file_id]}.csv',
                            mime='text/csv',
                        )
                    with col2:
                        st.download_button(
                            'Download JSON',
                            data=json_data,
                            file_name=f'{manage_file_options[manage_file_id]}.json',
                            mime='application/json',
                        )
                    with col3:
                        st.download_button(
                            'Download Excel',
                            data=excel_data,
                            file_name=f'{manage_file_options[manage_file_id]}.xlsx',
                            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        )

                    if st.button('Delete This Dataset'):
                        delete_file(manage_file_id)
                        st.success(f"Dataset '{manage_file_options[manage_file_id]}' deleted!")
                        st.rerun()
                else:
                    st.error('No data found in the selected dataset.')
        else:
            st.warning('No datasets uploaded yet.')

    st.markdown('<div class="filter-container">', unsafe_allow_html=True)
    col1, col2, _ = st.columns([1, 1, 3])
    with col1:
        majors = ['software_engineering', 'cloud_computing', 'data_science', 'cybersecurity']
        selected_major = st.selectbox(
            'Filter by Major:',
            majors,
            format_func=lambda x: x.replace('_', ' ').title(),
        )
    with col2:
        categories = ['jobs', 'courses', 'research', 'lsu']
        selected_category = st.selectbox(
            'Filter by Category:',
            categories,
            format_func=lambda x: x.upper() if x == 'lsu' else x.title(),
        )
    st.markdown('</div>', unsafe_allow_html=True)

    st.subheader('Summary')
    st.markdown(
        """
        The LSU Datastore is a tool for managing and analyzing datasets at LSU, including research projects, jobs, and courses.
        The Datastore provides a continuously updated platform for accessing data, performing searches, and sharing insights.
        Details of our work are provided in the LSU Data Science Repository.
        We hope that researchers will use the LSU Datastore to gain insights into academic and professional opportunities.
        """
    )

    st.subheader('Usage')
    st.markdown(
        """
        To the left is a dropdown menu for navigating the LSU Datastore features:

        - **Home Page**: Overview of the LSU Datastore platform.
        - **data Page**: View all CSV files in the LSU Datastore (no login required).
        - **Search Data**: Search for specific entries across all datasets.
        - **Visualize Data**: Explore data visualizations for numerical datasets.
        - **Share Data**: Share datasets via email with collaborators.
        - **Manage Data**: Upload, edit, and delete datasets (requires login).
        """
    )

    st.subheader('LSU Datastore - Livestream Data Store')
    st.markdown('Select a date to view Jobs, Courses, Research Projects, or LSU-specific data for that day.')

    selected_date = st.date_input(
        'Select a date:', value=datetime.now(), key='date_select'
    )
    formatted_date = selected_date.strftime('%Y-%m-%d')

    files = cached_get_files()
    if files:
        file_options: Dict[int, str] = {}
        for file_id, filename, _, _, _ in files:
            if selected_category == 'lsu':
                if (
                    filename.lower().startswith('lsu')
                    and formatted_date in filename
                    and (selected_major in filename or 'relevant' in filename)
                ):
                    file_options[file_id] = filename
            else:
                if (
                    selected_category in filename
                    and formatted_date in filename
                    and selected_major in filename
                ):
                    file_options[file_id] = filename

        if file_options:
            col1, col2 = st.columns([3, 1])
            with col1:
                selected_file_id = st.selectbox(
                    'Select a dataset to preview:',
                    options=file_options.keys(),
                    format_func=lambda x: file_options[x],
                    key='live_select',
                )
                if selected_file_id:
                    logger.info(
                        'Dataset Selected',
                        extra={
                            'username': st.session_state.username or 'Anonymous',
                            'action': 'select_dataset',
                            'details': f'Selected dataset: {file_options[selected_file_id]}',
                        },
                    )
                    df = cached_get_csv_preview(selected_file_id)
                    if not df.empty:
                        st.write(f'**Preview of {file_options[selected_file_id]}:**')
                        st.dataframe(df, hide_index=True)

                        st.subheader('Download Data')
                        col_dl1, col_dl2 = st.columns(2)
                        with col_dl1:
                            csv_data = df.to_csv(index=False).encode('utf-8')
                            if st.download_button(
                                label='Download CSV',
                                data=csv_data,
                                file_name=f'{file_options[selected_file_id]}.csv',
                                mime='text/csv',
                                key='download_csv_live',
                            ):
                                logger.info(
                                    'CSV Downloaded',
                                    extra={
                                        'username': st.session_state.username or 'Anonymous',
                                        'action': 'download_csv',
                                        'details': f'Downloaded: {file_options[selected_file_id]}.csv',
                                    },
                                )
                        with col_dl2:
                            parquet_buffer = io.BytesIO()
                            df.to_parquet(parquet_buffer, engine='pyarrow', index=False)
                            parquet_data = parquet_buffer.getvalue()
                            if st.download_button(
                                label='Download Parquet',
                                data=parquet_data,
                                file_name=f'{file_options.get(selected_file_id, "dataset")}.parquet',
                                mime='application/octet-stream',
                                key='download_parquet_live',
                            ):
                                logger.info(
                                    'Parquet Downloaded',
                                    extra={
                                        'username': st.session_state.username or 'Anonymous',
                                        'action': 'download_parquet',
                                        'details': f'Downloaded: {file_options.get(selected_file_id, "dataset")}.parquet',
                                    },
                                )

                        st.subheader('Share Data via Email')
                        email_input = st.text_input(
                            'Enter your email address:', key='email_live'
                        )

                        if st.button('Send Data', key='send_live'):
                            if email_input:
                                success = send_dataset_email(
                                    email_input,
                                    file_options.get(selected_file_id, "dataset"),
                                    df
                                )
                                if success:
                                    st.success(f"Data sent to {email_input}!")
                                else:
                                    st.error("Failed to send email.")
                            else:
                                st.warning('Please enter an email address.')
                                logger.error(
                                    'Email Share Failed',
                                    extra={
                                        'username': st.session_state.username or 'Anonymous',
                                        'action': 'email_share',
                                        'details': 'No email address provided',
                                    },
                                )
                    else:
                        st.error('No data found in the selected dataset.')
            with col2:
                try:
                    st.markdown(
                        f'<div class="logo-image"><img src="data:image/png;base64,'
                        f'{base64.b64encode(open(os.path.join(base_dir, "lsu_logo.png"), "rb").read()).decode()}" '
                        f'alt="LSU Datastore Process" style="width:100%;"></div>',
                        unsafe_allow_html=True,
                    )
                    st.caption('LSU Datastore Process')
                except FileNotFoundError:
                    st.warning("Image not found. Please add 'lsu_logo.png' to your project directory.")
        else:
            st.warning(
                f"No {selected_category.upper() if selected_category == 'lsu' else selected_category.capitalize()} "
                f"data available for {selected_major.replace('_', ' ').capitalize()} on {formatted_date}."
            )
    else:
        st.warning('No datasets uploaded yet.')

    if files and file_options and selected_file_id and not df.empty:
        st.subheader('Visualize Data')
        numerical_cols = df.select_dtypes(include=['number']).columns
        if len(numerical_cols) > 1:
            x_axis = st.selectbox(
                'Select X-Axis:', numerical_cols, index=1, key='x_axis_home'
            )
            y_axis = st.selectbox(
                'Select Y-Axis:', numerical_cols, index=0, key='y_axis_home'
            )
            fig = px.scatter(df, x=x_axis, y=y_axis, title=f'{x_axis} vs {y_axis}')
            st.plotly_chart(fig, use_container_width=True)
        elif len(numerical_cols) == 1:
            st.warning('Only one numerical column was found; cannot plot.')
        else:
            st.warning('No numerical columns found for visualization.')

        st.subheader('Search Data')
        global_search = st.text_input('Search across all datasets:', key='global_search_home')
        if global_search:
            results = search_csv_data(global_search)
            if results:
                st.dataframe(
                    pd.DataFrame(results, columns=['File ID', 'Row', 'Column', 'Value'])
                )
            else:
                st.warning('No matches found.')

    if st.session_state.logged_in:
        st.subheader('Live Feed Logs')
        st.markdown('View and download daily logs of live feed activities for testing and optimization.')

        log_files = [
            f for f in os.listdir(log_dir) if f.startswith('live_feed_log') and f.endswith('.csv')
        ]
        if log_files:
            selected_log = st.selectbox(
                'Select a log file to view:', log_files, key='log_select'
            )
            if selected_log:
                log_path = os.path.join(log_dir, selected_log)
                try:
                    log_df = pd.read_csv(log_path)
                    st.write(f'**Log: {selected_log}**')
                    st.dataframe(log_df, hide_index=True)

                    log_csv = log_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label='Download Log as CSV',
                        data=log_csv,
                        file_name=selected_log,
                        mime='text/csv',
                        key='download_log_csv',
                    )
                except Exception as e:
                    st.error(f'Error reading log file: {str(e)}')
        else:
            st.warning('No log files available.')

        st.subheader('Live Terminal Logs')
        st.markdown('View live logs in a terminal-like interface.')
        log_placeholder = st.empty()
        for _ in range(60):
            logs = memory_handler.get_logs()
            log_text = '\n'.join(logs[-20:])
            log_placeholder.markdown(
                f'<div class="terminal-log">{log_text}</div>',
                unsafe_allow_html=True,
            )
            time.sleep(1)

    st.subheader('System Performance Metrics')
    placeholder = st.empty()
    for _ in range(60):
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_usage = psutil.virtual_memory().percent
        with placeholder.container():
            col1, col2 = st.columns(2)
            with col1:
                st.metric('CPU Usage', f'{cpu_usage}%')
            with col2:
                st.metric('Memory Usage', f'{memory_usage}%')

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('---')
    st.markdown(
        '[Link to DAG Grid](https://animated-train-jjvx5x4q9g73p5v5-8080.app.github.dev/dags/fetch_store_dag/grid)'
    )

# Main rendering
def main() -> None:
    """Render the main Streamlit application."""
    st.markdown(
        """
        <div class="demo-info">
            <span class="demo-text">Demo 1.3.8</span>
            <span class="live-demo-badge"><i class="fas fa-rocket"></i> Live Demo</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_sidebar()
    if st.session_state.page == 'data Page':
        render_data_page()
    elif st.session_state.page == '🔍 Search Data':
        render_search_data_page()
    elif st.session_state.page == '📊 Visualize Data':
        render_visualize_data_page()
    elif st.session_state.page == '📤 Share Data':
        render_share_data_page()
    else:
        render_home_page()

if __name__ == '__main__':
    main()
