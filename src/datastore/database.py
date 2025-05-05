"""SQLite database management for the LSU Datastore Dashboard.

This module provides functions to initialize the SQLite database, manage user authentication
with bcrypt, store and retrieve CSV data, and perform searches and updates.

Dependencies:
    - os: For file path operations.
    - sqlite3: For database connectivity.
    - pandas: For DataFrame operations.
    - io: For handling CSV content.
    - bcrypt: For secure password hashing.
    - dotenv: For loading environment variables.
    - logging: For error and info logging.
    - typing: For type hints.
"""

import logging
import os
import sqlite3
import pandas as pd
import io
import bcrypt
from typing import List, Tuple, Optional
from dotenv import load_dotenv

# Configure logging at module level
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants
BASE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(BASE_DIRECTORY, "..", ".."))
DEFAULT_DATABASE_PATH = os.path.join(PROJECT_ROOT, "src", "database", "datastore.db")
DATABASE_PATH = os.path.normpath(os.path.join(PROJECT_ROOT, os.getenv("DB_PATH", DEFAULT_DATABASE_PATH)))
EMPTY_VALUE = "emptyvalue"
NA_VALUE = "N/A"
USERS_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
"""
FILES_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        file_format TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""
CSV_DATA_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS csv_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id INTEGER NOT NULL,
        row_number INTEGER NOT NULL,
        column_name TEXT NOT NULL,
        value TEXT NOT NULL,
        FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
    )
"""
CSV_COLUMNS_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS csv_columns (
        file_id INTEGER,
        column_index INTEGER,
        column_name TEXT
    )
"""

# Flag to track database initialization
_database_initialized = False

def ensure_database_directory() -> None:
    """Ensure the directory for DATABASE_PATH exists.

    Raises:
        OSError: If directory creation fails.
    """
    database_directory = os.path.dirname(DATABASE_PATH)
    if database_directory and not os.path.exists(database_directory):
        try:
            os.makedirs(database_directory)
            logger.info(f"Created database directory: {database_directory}")
        except OSError as error:
            logger.error(f"Failed to create database directory {database_directory}: {error}")
            raise

def execute_sql(connection: sqlite3.Connection, query: str, params: tuple = ()) -> None:
    """Execute an SQL query with optional parameters.

    Args:
        connection: SQLite database connection.
        query: SQL query string.
        params: Tuple of query parameters.

    Raises:
        sqlite3.Error: If the query execution fails.
    """
    try:
        cursor = connection.cursor()
        cursor.execute(query, params)
        connection.commit()
    except sqlite3.Error as error:
        logger.error(f"SQL execution failed: {query}, Error: {error}")
        raise

def test_database_connection() -> None:
    """Test the connection to the SQLite database.

    Raises:
        sqlite3.Error: If the connection fails.
    """
    try:
        ensure_database_directory()
        connection = sqlite3.connect(DATABASE_PATH)
        logger.info(f"Successfully connected to database at {DATABASE_PATH}")
        connection.close()
    except sqlite3.Error as error:
        logger.error(f"Failed to connect to database at {DATABASE_PATH}: {error}")
        raise

def initialize_database() -> None:
    """Initialize the database and create tables if they don't exist.

    Raises:
        sqlite3.Error: If database initialization fails.
    """
    global _database_initialized
    if _database_initialized:
        logger.debug("Database already initialized")
        return
    try:
        ensure_database_directory()
        connection = sqlite3.connect(DATABASE_PATH)
        execute_sql(connection, USERS_TABLE_SQL)
        execute_sql(connection, FILES_TABLE_SQL)
        execute_sql(connection, CSV_DATA_TABLE_SQL)
        execute_sql(connection, CSV_COLUMNS_TABLE_SQL)
        _database_initialized = True
        logger.info(f"Database initialized successfully at {DATABASE_PATH}")
    except sqlite3.Error as error:
        logger.error(f"Database initialization failed: {error}")
        raise
    finally:
        if 'connection' in locals():
            connection.close()

def authenticate_user(username: str, password: str) -> bool:
    """Authenticate user by checking hashed password.

    Args:
        username: Username to authenticate.
        password: Password to verify.

    Returns:
        bool: True if authentication succeeds, False otherwise.

    Raises:
        sqlite3.Error: If the database query fails.
        ValueError: If username or password is empty.
    """
    if not username or not password:
        logger.error("Username or password is empty")
        raise ValueError("Username and password cannot be empty")
    try:
        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        if result and bcrypt.checkpw(password.encode(), result[0].encode()):
            logger.info(f"User {username} authenticated successfully")
            return True
        logger.warning(f"Authentication failed for user {username}")
        return False
    except sqlite3.Error as error:
        logger.error(f"Authentication error for user {username}: {error}")
        raise
    finally:
        if 'connection' in locals():
            connection.close()

def save_csv_data(filename: str, content: bytes, file_size: int, file_format: str, user_id: int) -> None:
    """Save a CSV file and store its data in the database.

    Args:
        filename: Name of the CSV file.
        content: CSV file content in bytes.
        file_size: Size of the file in bytes.
        file_format: File format (e.g., 'csv').
        user_id: ID of the user uploading the file.

    Raises:
        ValueError: If input parameters are invalid.
        sqlite3.Error: If database operations fail.
        pd.errors.ParserError: If CSV parsing fails.
    """
    if not filename or not content or file_size < 0 or not file_format or user_id < 1:
        logger.error("Invalid input parameters for save_csv_data")
        raise ValueError("Invalid input parameters")
    try:
        ensure_database_directory()
        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()
        execute_sql(
            connection,
            "INSERT INTO files (filename, file_size, file_format, user_id) VALUES (?, ?, ?, ?)",
            (filename, file_size, file_format, user_id)
        )
        file_identifier = cursor.lastrowid
        csv_data_stream = io.BytesIO(content)
        try:
            data_frame = pd.read_csv(csv_data_stream)
        except pd.errors.ParserError as error:
            logger.error(f"Failed to parse CSV file {filename}: {error}")
            raise
        data_frame.replace(EMPTY_VALUE, NA_VALUE, inplace=True)
        for row_index, row in data_frame.iterrows():
            for column_name, value in row.items():
                execute_sql(
                    connection,
                    "INSERT INTO csv_data (file_id, row_number, column_name, value) VALUES (?, ?, ?, ?)",
                    (file_identifier, row_index, column_name, str(value))
                )
        execute_sql(connection, CSV_COLUMNS_TABLE_SQL)
        for column_index, column_name in enumerate(data_frame.columns):
            execute_sql(
                connection,
                "INSERT INTO csv_columns (file_id, column_index, column_name) VALUES (?, ?, ?)",
                (file_identifier, column_index, column_name)
            )
        logger.info(f"Stored {filename} in database with file_id {file_identifier}")
    except (sqlite3.Error, pd.errors.ParserError) as error:
        logger.error(f"Error saving CSV data for {filename}: {error}")
        raise
    finally:
        if 'connection' in locals():
            connection.close()

def get_files() -> List[Tuple[int, str, int, str, str]]:
    """Retrieve stored files metadata from the database.

    Returns:
        List of tuples containing file metadata (id, filename, file_size, file_format, uploaded_at).

    Raises:
        sqlite3.Error: If the database query fails.
    """
    try:
        initialize_database()
        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()
        cursor.execute("SELECT id, filename, file_size, file_format, uploaded_at FROM files ORDER BY uploaded_at DESC")
        records = cursor.fetchall()
        logger.info(f"Fetched {len(records)} file records from database")
        return records
    except sqlite3.Error as error:
        logger.error(f"Error retrieving files: {error}")
        raise
    finally:
        if 'connection' in locals():
            connection.close()

def get_csv_preview(file_identifier: int) -> pd.DataFrame:
    """Retrieve and format CSV data for preview in Streamlit.

    Args:
        file_identifier: ID of the file to retrieve.

    Returns:
        pandas.DataFrame: Formatted DataFrame with CSV data.

    Raises:
        ValueError: If file_identifier is invalid or no data is found.
        sqlite3.Error: If the database query fails.
    """
    if file_identifier < 1:
        logger.error("Invalid file_identifier provided")
        raise ValueError("Invalid file_identifier")
    try:
        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()
        cursor.execute("SELECT row_number, column_name, value FROM csv_data WHERE file_id = ? ORDER BY row_number",
                       (file_identifier,))
        rows = cursor.fetchall()
        data_frame = pd.DataFrame(rows, columns=["row_number", "column_name", "value"]).pivot(
            index="row_number", columns="column_name", values="value"
        )
        data_frame = data_frame.reset_index(drop=True)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='csv_columns'")
        table_exists = cursor.fetchone() is not None
        has_column_order = False
        if table_exists:
            cursor.execute("SELECT COUNT(*) FROM csv_columns WHERE file_id = ?", (file_identifier,))
            has_column_order = cursor.fetchone()[0] > 0
        if has_column_order:
            cursor.execute("SELECT column_name FROM csv_columns WHERE file_id = ? ORDER BY column_index",
                           (file_identifier,))
            ordered_columns = [row[0] for row in cursor.fetchall()]
            data_frame = data_frame[ordered_columns]
        data_frame.columns = [col.replace("_", " ").title() for col in data_frame.columns]
        for column in data_frame.columns:
            non_na_values = data_frame[column][data_frame[column] != NA_VALUE]
            converted = pd.to_numeric(non_na_values, errors="coerce")
            if not converted.isna().any():
                data_frame[column] = pd.to_numeric(data_frame[column], errors="coerce")
        if data_frame.empty:
            logger.warning(f"No data found for file_identifier {file_identifier}")
            raise ValueError(f"No data found for file_identifier {file_identifier}")
        logger.info(f"Fetched {len(data_frame)} rows for file_identifier {file_identifier}")
        return data_frame
    except sqlite3.Error as error:
        logger.error(f"Error retrieving CSV preview for file_identifier {file_identifier}: {error}")
        raise
    finally:
        if 'connection' in locals():
            connection.close()

def delete_file(file_identifier: int) -> None:
    """Delete a file and its associated CSV data from the database.

    Args:
        file_identifier: ID of the file to delete.

    Raises:
        ValueError: If file_identifier is invalid.
        sqlite3.Error: If the database operation fails.
    """
    if file_identifier < 1:
        logger.error("Invalid file_identifier provided")
        raise ValueError("Invalid file_identifier")
    try:
        connection = sqlite3.connect(DATABASE_PATH)
        execute_sql(connection, "DELETE FROM files WHERE id = ?", (file_identifier,))
        logger.info(f"Deleted file with file_identifier {file_identifier}")
    except sqlite3.Error as error:
        logger.error(f"Error deleting file with file_identifier {file_identifier}: {error}")
        raise
    finally:
        if 'connection' in locals():
            connection.close()

def search_csv_data(search_query: str) -> List[Tuple[int, int, str, str]]:
    """Search all CSV data for a given keyword.

    Args:
        search_query: Keyword to search for in CSV values.

    Returns:
        List of tuples containing (file_id, row_number, column_name, value) for matching entries.

    Raises:
        sqlite3.Error: If the database query fails.
    """
    try:
        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()
        cursor.execute("SELECT file_id, row_number, column_name, value FROM csv_data WHERE value LIKE ?",
                       (f"%{search_query}%",))
        results = cursor.fetchall()
        logger.info(f"Search for '{search_query}' returned {len(results)} results")
        return results
    except sqlite3.Error as error:
        logger.error(f"Error searching CSV data: {error}")
        raise
    finally:
        if 'connection' in locals():
            connection.close()

def update_csv_data(file_identifier: int, data_frame: pd.DataFrame) -> None:
    """Update modified CSV data in the database.

    Args:
        file_identifier: ID of the file to update.
        data_frame: DataFrame containing updated CSV data.

    Raises:
        ValueError: If file_identifier is invalid or data_frame is empty.
        sqlite3.Error: If the database operation fails.
    """
    if file_identifier < 1:
        logger.error("Invalid file_identifier provided")
        raise ValueError("Invalid file_identifier")
    if data_frame.empty:
        logger.error("Empty data_frame provided for update")
        raise ValueError("DataFrame cannot be empty")
    try:
        connection = sqlite3.connect(DATABASE_PATH)
        execute_sql(connection, "DELETE FROM csv_data WHERE file_id = ?", (file_identifier,))
        for row_index, row in data_frame.iterrows():
            for column_name, value in row.items():
                execute_sql(
                    connection,
                    "INSERT INTO csv_data (file_id, row_number, column_name, value) VALUES (?, ?, ?, ?)",
                    (file_identifier, row_index, column_name, str(value))
                )
        logger.info(f"Updated CSV data for file_identifier {file_identifier}")
    except sqlite3.Error as error:
        logger.error(f"Error updating CSV data for file_identifier {file_identifier}: {error}")
        raise
    finally:
        if 'connection' in locals():
            connection.close()

def reset_password(username: str, new_password: str) -> None:
    """Update a user's password with bcrypt hashing.

    Args:
        username: Username to update.
        new_password: New password to hash and store.

    Raises:
        ValueError: If username or new_password is empty.
        sqlite3.Error: If the database operation fails.
    """
    if not username or not new_password:
        logger.error("Username or new_password is empty")
        raise ValueError("Username and new_password cannot be empty")
    try:
        hashed_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        connection = sqlite3.connect(DATABASE_PATH)
        execute_sql(connection, "UPDATE users SET password = ? WHERE username = ?", (hashed_password, username))
        logger.info(f"Password updated for user {username}")
    except sqlite3.Error as error:
        logger.error(f"Error updating password for user {username}: {error}")
        raise
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    initialize_database()
    reset_password("admin", "NewSecurePassword123")
