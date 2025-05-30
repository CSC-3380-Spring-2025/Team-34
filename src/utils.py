import base64
import io
import logging
import os
import re
import requests
from logging.handlers import TimedRotatingFileHandler
from typing import List, Tuple

import pandas as pd
import streamlit as st
from datetime import datetime
from pandas import DataFrame
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, Disposition, FileContent, FileName, FileType

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

# Define memory_handler globally
memory_handler = None

# Setup logging
def setup_logger(log_dir: str = "logs", log_file: str = "live_feed_log") -> logging.Logger:
    """Configure and return the logger for the application."""
    global memory_handler
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger('LiveFeedLogger')
    logger.setLevel(logging.INFO)

    file_handler = CustomTimedRotatingFileHandler(
        os.path.join(log_dir, log_file), when='midnight', interval=1, backupCount=30, encoding='utf-8'
    )
    file_handler.setFormatter(CSVFormatter())
    file_handler.suffix = '%Y-%m-%d.csv'

    log_file_path = f'{os.path.join(log_dir, log_file)}.{datetime.now().strftime("%Y-%m-%d")}.csv'
    if not os.path.exists(log_file_path):
        with open(log_file_path, 'a') as f:
            f.write('Timestamp,Username,Action,Details\n')

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    memory_handler = MemoryHandler(capacity=1000)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.addHandler(memory_handler)

    return logger

# Initialize logger
logger = setup_logger()

def get_secret(key: str, default: str) -> str:
    """Retrieve a secret from environment variables, concatenating SendGrid API key parts if needed.

    Args:
        key (str): The key to look up.
        default (str): The default value if the key is not found.

    Returns:
        str: The value of the key or the default.
    """
    if key == 'SENDGRID_API_KEY':
        full_key = os.getenv('SENDGRID_API_KEY', '')
        if full_key:
            logger.info("Using full SENDGRID_API_KEY from environment variables")
            return full_key
        part1 = os.getenv('SENDGRID_API_KEY_PART1', '')
        part2 = os.getenv('SENDGRID_API_KEY_PART2', '')
        part3 = os.getenv('SENDGRID_API_KEY_PART3', '')
        if part1 and part2 and part3:
            logger.info("Using split SENDGRID_API_KEY parts from environment variables")
            return part1 + part2 + part3
        logger.error("No valid SENDGRID_API_KEY found in environment variables")
        return default
    return os.getenv(key, default)

@st.cache_data
def cached_get_files() -> List[Tuple[int, str, int, str, datetime]]:
    """Retrieve cached file metadata from the database.

    Returns:
        List[Tuple[int, str, int, str, datetime]]: List of file metadata tuples.
    """
    from src.datastore.database import get_files
    return get_files()

@st.cache_data
def cached_get_csv_preview(file_id: int) -> DataFrame:
    """Retrieve cached CSV data preview for a file.

    Args:
        file_id (int): ID of the file to preview.

    Returns:
        DataFrame: Preview DataFrame or empty if no data.
    """
    from src.datastore.database import get_csv_preview
    return get_csv_preview(file_id)

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

    api_key = get_secret('SENDGRID_API_KEY', '')
    if not api_key:
        st.error("SendGrid API key not found in environment variables. Please set SENDGRID_API_KEY or SENDGRID_API_KEY_PART1, SENDGRID_API_KEY_PART2, and SENDGRID_API_KEY_PART3 in .env.")
        logger.error(
            'Email Share Failed',
            extra={
                'username': st.session_state.username or 'Anonymous',
                'action': 'email_share',
                'details': 'No SendGrid API key found in environment variables',
            },
        )
        return False

    from_email = get_secret('FROM_EMAIL', 'default@example.com')
    logger.info(f"Attempting to send email to {email} from {from_email} with dataset {filename}")

    try:
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue().encode('utf-8')
        encoded_file = base64.b64encode(csv_data).decode()

        email_data = {
            "personalizations": [{"to": [{"email": email}]}],
            "from": {"email": from_email},
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

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        logger.debug(f"Sending email with headers: {headers} and data: {email_data}")
        try:
            response = requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=email_data,
                headers=headers,
            )
            response.raise_for_status()
            logger.info(f"Email sent successfully. Status code: {response.status_code}")
        except requests.exceptions.SSLError as ssl_err:
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
                verify=False,
            )
            response.raise_for_status()
            logger.info(f"Email sent successfully with disabled SSL verification. Status code: {response.status_code}")

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
        st.error(f'Failed to send email. Status code: {response.status_code}, Response: {response.text}')
        logger.error(
            'Email Share Failed',
            extra={
                'username': st.session_state.username or 'Anonymous',
                'action': 'email_share',
                'details': f'Failed, Status code: {response.status_code}, Response: {response.text}, Dataset: {filename}',
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
