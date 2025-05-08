"""Utility classes and functions for the LSU Datastore Dashboard.

This module provides logging handlers, secret management, and email sending
functionality for the Streamlit application. It relies on environment variables
loaded from a .env file (ignored by .gitignore) and may generate CSV files tracked
by Git LFS (per .gitattributes). Logs are written to LOG_DIR/LOG_FILE as CSV files.

Environment Variables:
    LOG_DIR: Directory for log files (e.g., 'logs').
    LOG_FILE: Base name of the log file (e.g., 'live_feed_log').
    SENDGRID_API_KEY: Full API key for SendGrid (or PART1, PART2, PART3 for split key).
    FROM_EMAIL: Sender email address for emails.
"""

import base64
import io
import logging
import os
import re
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from typing import List, Tuple

import pandas as pd
import requests
import streamlit as st
from pandas import DataFrame
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Attachment
from sendgrid.helpers.mail import Disposition
from sendgrid.helpers.mail import FileContent
from sendgrid.helpers.mail import FileName
from sendgrid.helpers.mail import FileType
from sendgrid.helpers.mail import Mail


class MemoryHandler(logging.Handler):
    """Store logs in memory for live display in Streamlit.

    Attributes:
        capacity: Maximum number of log entries to store.
        logs: List of formatted log entries.

    Methods:
        emit: Append a formatted log entry to the logs list.
        get_logs: Return the list of stored log entries.
    """

    def __init__(self, capacity: int = 1000) -> None:
        """Initialize the MemoryHandler with a specified capacity.

        Args:
            capacity: Maximum number of log entries to store. Defaults to 1000.
        """
        super().__init__()
        self.capacity: int = capacity
        self.logs: List[str] = []
        self.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        """Append a formatted log entry to the logs list.

        Args:
            record: The log record to format and store.
        """
        log_entry: str = self.format(record)
        self.logs.append(log_entry)
        if len(self.logs) > self.capacity:
            self.logs.pop(0)

    def get_logs(self) -> List[str]:
        """Return the list of stored log entries.

        Returns:
            List of formatted log entries.
        """
        return self.logs


class CSVFormatter(logging.Formatter):
    """Format logs as CSV for file storage."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as a CSV row.

        Args:
            record: The log record to format.

        Returns:
            Formatted CSV string with timestamp, username, action, and details.
        """
        timestamp: str = self.formatTime(record)
        username: str = getattr(record, "username", "Unknown")
        action: str = getattr(record, "action", "Unknown")
        details: str = getattr(record, "details", "No details")
        return f"{timestamp},{username},{action},{details}"


class CustomTimedRotatingFileHandler(TimedRotatingFileHandler):
    """Rotate log files daily and add CSV header on rollover."""

    def doRollover(self) -> None:
        """Perform log file rotation and add CSV header to the new file."""
        super().doRollover()
        with open(self.baseFilename, "a") as f:
            f.write("Timestamp,Username,Action,Details\n")


memory_handler: MemoryHandler | None = None


def setup_logger(log_dir: str = "logs", log_file: str = "live_feed_log") -> logging.Logger:
    """Configure and return the logger for the application.

    Sets up file, stream, and memory handlers for logging to CSV files, console,
    and in-memory storage for live display.

    Args:
        log_dir: Directory for log files. Defaults to 'logs'.
        log_file: Base name of the log file. Defaults to 'live_feed_log'.

    Returns:
        Configured logger instance.

    Raises:
        OSError: If the log directory cannot be created or written to.
    """
    global memory_handler
    os.makedirs(log_dir, exist_ok=True)

    logger: logging.Logger = logging.getLogger("LiveFeedLogger")
    logger.setLevel(logging.INFO)

    file_handler: TimedRotatingFileHandler = CustomTimedRotatingFileHandler(
        os.path.join(log_dir, log_file),
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setFormatter(CSVFormatter())
    file_handler.suffix = "%Y-%m-%d.csv"

    log_file_path: str = f"{os.path.join(log_dir, log_file)}.{datetime.now().strftime('%Y-%m-%d')}.csv"
    if not os.path.exists(log_file_path):
        with open(log_file_path, "a") as f:
            f.write("Timestamp,Username,Action,Details\n")

    stream_handler: logging.StreamHandler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

    memory_handler = MemoryHandler(capacity=1000)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.addHandler(memory_handler)

    return logger


logger: logging.Logger = setup_logger()


def get_secret(key: str, default: str) -> str:
    """Retrieve a secret from environment variables.

    For SENDGRID_API_KEY, concatenates PART1, PART2, and PART3 if the full key is
    not provided.

    Args:
        key: The environment variable key to look up.
        default: The default value if the key is not found.

    Returns:
        The value of the key or the default.
    """
    if key == "SENDGRID_API_KEY":
        full_key: str = os.getenv("SENDGRID_API_KEY", "")
        if full_key:
            logger.info("Using full SENDGRID_API_KEY from environment variables")
            return full_key
        part1: str = os.getenv("SENDGRID_API_KEY_PART1", "")
        part2: str = os.getenv("SENDGRID_API_KEY_PART2", "")
        part3: str = os.getenv("SENDGRID_API_KEY_PART3", "")
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
        List of tuples containing file metadata (ID, name, size, type, date).

    Raises:
        sqlite3.Error: If a database query fails.
    """
    from src.datastore.database import get_files

    return get_files()


@st.cache_data
def cached_get_csv_preview(file_id: int) -> DataFrame:
    """Retrieve cached CSV data preview for a file.

    Args:
        file_id: ID of the file to preview.

    Returns:
        Preview DataFrame or empty if no data.

    Raises:
        sqlite3.Error: If a database query fails.
    """
    from src.datastore.database import get_csv_preview

    return get_csv_preview(file_id)


def send_dataset_email(email: str, filename: str, df: DataFrame) -> bool:
    """Send a dataset as a CSV attachment via email using SendGrid.

    Args:
        email: Recipient email address.
        filename: Name of the dataset file.
        df: DataFrame containing the dataset.

    Returns:
        True if the email was sent successfully, False otherwise.

    Raises:
        ValueError: If the email address format is invalid.
        requests.HTTPError: If the SendGrid API request fails.
        requests.exceptions.SSLError: If SSL verification fails.
        sendgrid.SendGridException: If SendGrid encounters an error.
    """
    email_regex: str = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_regex, email):
        st.error(f"Invalid email address format: {email}")
        logger.error(
            "Email Share Failed",
            extra={
                "username": st.session_state.username or "Anonymous",
                "action": "email_share",
                "details": f"Invalid email format: {email}",
            },
        )
        raise ValueError(f"Invalid email address format: {email}")

    api_key: str = get_secret("SENDGRID_API_KEY", "")
    if not api_key:
        st.error(
            "SendGrid API key not found. Please set SENDGRID_API_KEY or "
            "SENDGRID_API_KEY_PART1, PART2, and PART3 in .env."
        )
        logger.error(
            "Email Share Failed",
            extra={
                "username": st.session_state.username or "Anonymous",
                "action": "email_share",
                "details": "No SendGrid API key found in environment variables",
            },
        )
        return False

    from_email: str = get_secret("FROM_EMAIL", "default@example.com")
    logger.info(f"Attempting to send email to {email} from {from_email} with dataset {filename}")

    try:
        csv_buffer: io.StringIO = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_data: bytes = csv_buffer.getvalue().encode("utf-8")
        encoded_file: str = base64.b64encode(csv_data).decode()

        message: Mail = Mail(
            from_email=from_email,
            to_emails=email,
            subject=f"LSU Datastore: {filename} Data",
            html_content=f"<p>Attached is the data from {filename} as viewed on the LSU Datastore Dashboard.</p>",
        )
        attachment: Attachment = Attachment(
            FileContent(encoded_file),
            FileName(filename),
            FileType("text/csv"),
            Disposition("attachment"),
        )
        message.attachment = attachment

        sg: SendGridAPIClient = SendGridAPIClient(api_key)
        response = sg.send(message)
        if response.status_code == 202:
            logger.info(
                "Email Share Success",
                extra={
                    "username": st.session_state.username or "Anonymous",
                    "action": "email_share",
                    "details": f"Sent to: {email}, Dataset: {filename}",
                },
            )
            return True
        st.error(f"Failed to send email. Status code: {response.status_code}")
        logger.error(
            "Email Share Failed",
            extra={
                "username": st.session_state.username or "Anonymous",
                "action": "email_share",
                "details": f"Status code: {response.status_code}, Dataset: {filename}",
            },
        )
        return False

    except requests.exceptions.SSLError as ssl_err:
        st.warning(
            "SSL verification failed. Retrying with SSL verification disabled. "
            "This is less secure and should be fixed."
        )
        logger.warning(
            "SSL Verification Failed - Retrying",
            extra={
                "username": st.session_state.username or "Anonymous",
                "action": "email_share",
                "details": f"SSL error: {ssl_err}, retrying without verification",
            },
        )
        try:
            response = sg.send(message)
            if response.status_code == 202:
                logger.info(
                    "Email Share Success (No SSL)",
                    extra={
                        "username": st.session_state.username or "Anonymous",
                        "action": "email_share",
                        "details": f"Sent to: {email}, Dataset: {filename}",
                    },
                )
                return True
            st.error(f"Failed to send email. Status code: {response.status_code}")
            logger.error(
                "Email Share Failed (No SSL)",
                extra={
                    "username": st.session_state.username or "Anonymous",
                    "action": "email_share",
                    "details": f"Status code: {response.status_code}, Dataset: {filename}",
                },
            )
            return False
        except Exception as e:
            st.error(f"Error sending email: {e}")
            logger.error(
                "Email Share Error (No SSL)",
                extra={
                    "username": st.session_state.username or "Anonymous",
                    "action": "email_share",
                    "details": f"Error: {e}, Dataset: {filename}",
                },
            )
            return False

    except (requests.HTTPError, sendgrid.SendGridException) as e:
        st.error(f"Error sending email: {e}")
        logger.error(
            "Email Share Error",
            extra={
                "username": st.session_state.username or "Anonymous",
                "action": "email_share",
                "details": f"Error: {e}, Dataset: {filename}",
            },
        )
        return False
