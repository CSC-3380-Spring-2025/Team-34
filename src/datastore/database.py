"""Database module for the LSU Datastore Dashboard.

This module manages SQLite database operations for user authentication, file metadata,
and CSV data storage in the Team-34 project. It relies on environment variables
(DATABASE_NAME, ADMIN_USERNAME, ADMIN_PASSWORD) loaded from a .env file (ignored by
.gitignore). CSV files stored in the database may be tracked by Git Large File Storage
(LFS) per .gitattributes. Operations are logged to LOG_DIR/LOG_FILE.
"""

import hashlib
import io
import os
from datetime import datetime
from typing import Any, List, Optional, Tuple

import pandas as pd
import sqlite3
from dotenv import load_dotenv

from src.utils import logger


# Load environment variables
load_dotenv()

# Database path configuration
BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
DB_NAME: str = os.path.join(BASE_DIR, os.getenv("DATABASE_NAME", "datastore.db"))


def init_db() -> None:
    """Initialize the SQLite database and create tables if they do not exist.

    Creates tables for users, file metadata, CSV data, and CSV column order.

    Returns:
        None

    Raises:
        sqlite3.Error: If a database connection or table creation fails.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # Users table for authentication
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
            """
        )

        # Files metadata table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_format TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # CSV data table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS csv_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                row_number INTEGER NOT NULL,
                column_name TEXT NOT NULL,
                value TEXT NOT NULL,
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
            )
            """
        )

        # CSV columns table for preserving column order
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS csv_columns (
                file_id INTEGER,
                column_index INTEGER,
                column_name TEXT
            )
            """
        )

        conn.commit()
        logger.info(
            "Database Initialization Success",
            extra={
                "username": "System",
                "action": "init_db",
                "details": "Database initialized successfully",
            },
        )
    except sqlite3.Error as e:
        logger.error(
            "Database Initialization Failed",
            extra={
                "username": "System",
                "action": "init_db",
                "details": f"Error: {e}",
            },
        )
        raise
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> bool:
    """Authenticate a user by checking their hashed password.

    Args:
        username: The username to authenticate.
        password: The password to verify.

    Returns:
        True if authentication succeeds, False otherwise.

    Raises:
        sqlite3.Error: If a database query fails.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        hashed_password: str = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        return bool(result and result[0] == hashed_password)
    except sqlite3.Error as e:
        logger.error(
            "User Authentication Failed",
            extra={
                "username": username or "Unknown",
                "action": "authenticate_user",
                "details": f"Error: {e}",
            },
        )
        raise
    finally:
        conn.close()


def save_csv_to_database(
    filename: str,
    content: bytes,
    file_size: int,
    file_format: str,
    user_id: int,
) -> None:
    """Save a CSV file and its data to the SQLite database.

    Stores file metadata in the files table, CSV data in the csv_data table, and
    column order in the csv_columns table.

    Args:
        filename: Name of the CSV file.
        content: Binary content of the CSV file.
        file_size: Size of the file in bytes.
        file_format: Format of the file (e.g., 'csv').
        user_id: ID of the user uploading the file.

    Raises:
        sqlite3.Error: If a database operation fails.
        pd.errors.ParserError: If the CSV content cannot be parsed.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # Insert metadata into files table
        cursor.execute(
            "INSERT INTO files (filename, file_size, file_format, user_id) "
            "VALUES (?, ?, ?, ?)",
            (filename, file_size, file_format, user_id),
        )
        file_id: Optional[int] = cursor.lastrowid

        # Read CSV content into pandas
        csv_data = io.BytesIO(content)
        df: pd.DataFrame = pd.read_csv(csv_data)
        df.replace("emptyvalue", "N/A", inplace=True)

        # Insert CSV data into csv_data table
        for row_idx, row in df.iterrows():
            for col_name, value in row.items():
                cursor.execute(
                    "INSERT INTO csv_data (file_id, row_number, column_name, value) "
                    "VALUES (?, ?, ?, ?)",
                    (file_id, row_idx, col_name, str(value)),
                )

        # Insert column order into csv_columns table
        for col_idx, col_name in enumerate(df.columns):
            cursor.execute(
                "INSERT INTO csv_columns (file_id, column_index, column_name) "
                "VALUES (?, ?, ?)",
                (file_id, col_idx, col_name),
            )

        conn.commit()
        logger.info(
            "CSV File Saved",
            extra={
                "username": "System",
                "action": "save_csv",
                "details": f"Saved {filename} (file_id: {file_id})",
            },
        )
    except (sqlite3.Error, pd.errors.ParserError) as e:
        logger.error(
            "CSV Save Failed",
            extra={
                "username": "System",
                "action": "save_csv",
                "details": f"Error saving {filename}: {e}",
            },
        )
        conn.rollback()
        raise
    finally:
        conn.close()


def get_files() -> List[Tuple[int, str, int, str, datetime]]:
    """Retrieve metadata for all stored files from the database.

    Returns:
        List of tuples containing file metadata (id, filename, file_size,
        file_format, uploaded_at).

    Raises:
        sqlite3.Error: If a database query fails.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT id, filename, file_size, file_format, uploaded_at "
            "FROM files ORDER BY uploaded_at DESC"
        )
        files = cursor.fetchall()
        return files
    except sqlite3.Error as e:
        logger.error(
            "File Retrieval Failed",
            extra={
                "username": "System",
                "action": "get_files",
                "details": f"Error: {e}",
            },
        )
        raise
    finally:
        conn.close()


def get_csv_preview(file_id: int) -> pd.DataFrame:
    """Retrieve and format CSV data for preview in Streamlit.

    Formats column names (title case, replace underscores) and converts numeric
    columns where possible, preserving column order from the csv_columns table.

    Args:
        file_id: ID of the file to preview.

    Returns:
        Formatted DataFrame with CSV data, or empty if no data exists.

    Raises:
        sqlite3.Error: If a database query fails.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT row_number, column_name, value FROM csv_data "
            "WHERE file_id = ? ORDER BY row_number",
            (file_id,),
        )
        rows = cursor.fetchall()

        # Convert to DataFrame
        df = pd.DataFrame(rows, columns=["row_number", "column_name", "value"]).pivot(
            index="row_number", columns="column_name", values="value"
        )
        df = df.reset_index(drop=True)

        # Check if csv_columns table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='csv_columns'"
        )
        table_exists = cursor.fetchone() is not None
        has_column_order: bool = False
        if table_exists:
            cursor.execute(
                "SELECT COUNT(*) FROM csv_columns WHERE file_id = ?", (file_id,)
            )
            has_column_order = cursor.fetchone()[0] > 0

        # Apply column order if available
        if has_column_order:
            cursor.execute(
                "SELECT column_name FROM csv_columns "
                "WHERE file_id = ? ORDER BY column_index",
                (file_id,),
            )
            ordered_columns = [row[0] for row in cursor.fetchall()]
            df = df[ordered_columns]

        # Format column names
        df.columns = [col.replace("_", " ").title() for col in df.columns]

        # Convert numeric columns
        for col in df.columns:
            non_na_values = df[col][df[col] != "N/A"]
            converted = pd.to_numeric(non_na_values, errors="coerce")
            if not converted.isna().any():
                df[col] = pd.to_numeric(df[col], errors="coerce")

        return df

    except sqlite3.Error as e:
        logger.error(
            "CSV Preview Failed",
            extra={
                "username": "System",
                "action": "get_csv_preview",
                "details": f"Error for file_id {file_id}: {e}",
            },
        )
        raise
    finally:
        conn.close()


def delete_file(file_id: int) -> None:
    """Delete a file and its associated CSV data from the database.

    Args:
        file_id: ID of the file to delete.

    Returns:
        None

    Raises:
        sqlite3.Error: If the deletion operation fails.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
        conn.commit()
        logger.info(
            "File Deleted",
            extra={
                "username": "System",
                "action": "delete_file",
                "details": f"Deleted file_id: {file_id}",
            },
        )
    except sqlite3.Error as e:
        logger.error(
            "File Deletion Failed",
            extra={
                "username": "System",
                "action": "delete_file",
                "details": f"Error for file_id {file_id}: {e}",
            },
        )
        conn.rollback()
        raise
    finally:
        conn.close()


def search_csv_data(query: str) -> List[Tuple[int, int, str, str]]:
    """Search all CSV data for a given keyword.

    Args:
        query: Keyword to search for in CSV values.

    Returns:
        List of tuples containing search results (file_id, row_number, column_name,
        value). Returns an empty list if no matches are found or an error occurs.

    Raises:
        sqlite3.Error: If a database query fails.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT file_id, row_number, column_name, value FROM csv_data "
            "WHERE value LIKE ?",
            (f"%{query}%",),
        )
        results = cursor.fetchall()
        return results
    except sqlite3.Error as e:
        logger.error(
            "CSV Search Failed",
            extra={
                "username": "System",
                "action": "search_csv_data",
                "details": f"Error for query {query}: {e}",
            },
        )
        return []
    finally:
        conn.close()


def update_csv_data(file_id: int, df: pd.DataFrame) -> None:
    """Update modified CSV data in the database.

    Args:
        file_id: ID of the file to update.
        df: Updated DataFrame to store.

    Returns:
        None

    Raises:
        sqlite3.Error: If a database operation fails.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # Delete existing data for the file
        cursor.execute("DELETE FROM csv_data WHERE file_id = ?", (file_id,))

        # Insert updated CSV data
        for row_idx, row in df.iterrows():
            for col_name, value in row.items():
                cursor.execute(
                    "INSERT INTO csv_data (file_id, row_number, column_name, value) "
                    "VALUES (?, ?, ?, ?)",
                    (file_id, row_idx, col_name, str(value)),
                )

        conn.commit()
        logger.info(
            "CSV File Updated",
            extra={
                "username": "System",
                "action": "update_csv_data",
                "details": f"Updated file_id: {file_id}",
            },
        )
    except sqlite3.Error as e:
        logger.error(
            "CSV Update Failed",
            extra={
                "username": "System",
                "action": "update_csv_data",
                "details": f"Error for file_id {file_id}: {e}",
            },
        )
        conn.rollback()
        raise
    finally:
        conn.close()


def reset_password(username: str, new_password: str) -> None:
    """Update a user's password with SHA-256 hashing.

    Args:
        username: Username whose password is to be updated.
        new_password: New password to set.

    Returns:
        None

    Raises:
        sqlite3.Error: If the update operation fails.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        hashed_password: str = hashlib.sha256(new_password.encode()).hexdigest()
        cursor.execute(
            "UPDATE users SET password = ? WHERE username = ?",
            (hashed_password, username),
        )
        conn.commit()
        logger.info(
            "Password Reset Success",
            extra={
                "username": username,
                "action": "reset_password",
                "details": f"Password updated for {username}",
            },
        )
    except sqlite3.Error as e:
        logger.error(
            "Password Reset Failed",
            extra={
                "username": username,
                "action": "reset_password",
                "details": f"Error: {e}",
            },
        )
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "default_password")
    reset_password(admin_username, admin_password)
