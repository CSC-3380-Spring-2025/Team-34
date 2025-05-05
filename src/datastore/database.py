"""Database module for Team-34 project.

Manages SQLite database operations for user authentication, file metadata, and CSV data
storage for the LSU Datastore Dashboard.
"""

import hashlib
import io
import os
import pandas as pd
import sqlite3
from datetime import datetime
from typing import Any, List, Optional, Tuple
from dotenv import load_dotenv


load_dotenv()


# Database path configuration
BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, os.getenv("DATABASE_NAME", "datastore.db"))


def init_db() -> None:
    """Initialize the SQLite database and create tables if they do not exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Users table for authentication
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Files metadata table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            file_format TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # CSV data table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS csv_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            row_number INTEGER NOT NULL,
            column_name TEXT NOT NULL,
            value TEXT NOT NULL,
            FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
        )
    """)

    # CSV columns table for preserving column order
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS csv_columns (
            file_id INTEGER,
            column_index INTEGER,
            column_name TEXT
        )
    """)

    conn.commit()
    conn.close()
    print('✅ Database initialized successfully!')


def authenticate_user(username: str, password: str) -> bool:
    """Authenticate a user by checking their hashed password.

    Args:
        username (str): The username to authenticate.
        password (str): The password to verify.

    Returns:
        bool: True if authentication succeeds, False otherwise.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()

    return bool(result and result[0] == hashed_password)


def save_csv_to_database(
    filename: str, content: bytes, file_size: int, file_format: str, user_id: int
) -> None:
    """Save a CSV file and its data to the SQLite database.

    Args:
        filename (str): Name of the CSV file.
        content (bytes): Binary content of the CSV file.
        file_size (int): Size of the file in bytes.
        file_format (str): Format of the file (e.g., 'csv').
        user_id (int): ID of the user uploading the file.

    Raises:
        sqlite3.Error: If a database operation fails.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # Insert metadata into files table
        cursor.execute(
            'INSERT INTO files (filename, file_size, file_format, user_id) VALUES (?, ?, ?, ?)',
            (filename, file_size, file_format, user_id),
        )
        file_id = cursor.lastrowid

        # Read CSV content into pandas
        csv_data = io.BytesIO(content)
        df = pd.read_csv(csv_data)
        df.replace('emptyvalue', 'N/A', inplace=True)

        # Insert CSV data into csv_data table
        for row_idx, row in df.iterrows():
            for col_name, value in row.items():
                cursor.execute(
                    'INSERT INTO csv_data (file_id, row_number, column_name, value) '
                    'VALUES (?, ?, ?, ?)',
                    (file_id, row_idx, col_name, str(value)),
                )

        # Insert column order into csv_columns table
        for col_idx, col_name in enumerate(df.columns):
            cursor.execute(
                'INSERT INTO csv_columns (file_id, column_index, column_name) '
                'VALUES (?, ?, ?)',
                (file_id, col_idx, col_name),
            )

        conn.commit()
    except (sqlite3.Error, pd.errors.ParserError) as e:
        print(f'❌ Error saving CSV data for {filename}: {e}')
        conn.rollback()
    finally:
        conn.close()


def get_files() -> List[Tuple[int, str, int, str, datetime]]:
    """Retrieve metadata for all stored files from the database.

    Returns:
        List[Tuple[int, str, int, str, datetime]]: List of tuples containing file metadata
            (id, filename, file_size, file_format, uploaded_at).
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, filename, file_size, file_format, uploaded_at '
        'FROM files ORDER BY uploaded_at DESC'
    )
    files = cursor.fetchall()
    conn.close()
    return files


def get_csv_preview(file_id: int) -> pd.DataFrame:
    """Retrieve and format CSV data for preview in Streamlit.

    Args:
        file_id (int): ID of the file to preview.

    Returns:
        pd.DataFrame: Formatted DataFrame with CSV data, or empty if no data exists.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT row_number, column_name, value FROM csv_data '
        'WHERE file_id = ? ORDER BY row_number',
        (file_id,),
    )
    rows = cursor.fetchall()

    # Convert to DataFrame
    df = pd.DataFrame(rows, columns=['row_number', 'column_name', 'value']).pivot(
        index='row_number', columns='column_name', values='value'
    )
    df = df.reset_index(drop=True)

    # Check if csv_columns table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='csv_columns'"
    )
    table_exists = cursor.fetchone() is not None
    has_column_order = False
    if table_exists:
        cursor.execute('SELECT COUNT(*) FROM csv_columns WHERE file_id = ?', (file_id,))
        has_column_order = cursor.fetchone()[0] > 0

    # Apply column order if available
    if has_column_order:
        cursor.execute(
            'SELECT column_name FROM csv_columns '
            'WHERE file_id = ? ORDER BY column_index',
            (file_id,),
        )
        ordered_columns = [row[0] for row in cursor.fetchall()]
        df = df[ordered_columns]

    # Format column names
    df.columns = [col.replace('_', ' ').title() for col in df.columns]

    # Convert numeric columns
    for col in df.columns:
        non_na_values = df[col][df[col] != 'N/A']
        converted = pd.to_numeric(non_na_values, errors='coerce')
        if not converted.isna().any():
            df[col] = pd.to_numeric(df[col], errors='coerce')

    conn.close()
    return df


def delete_file(file_id: int) -> None:
    """Delete a file and its associated CSV data from the database.

    Args:
        file_id (int): ID of the file to delete.

    Raises:
        sqlite3.Error: If the deletion operation fails.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM files WHERE id = ?', (file_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f'❌ Error deleting file {file_id}: {e}')
        conn.rollback()
    finally:
        conn.close()


def search_csv_data(query: str) -> List[Tuple[int, int, str, str]]:
    """Search all CSV data for a given keyword.

    Args:
        query (str): Keyword to search for in CSV values.

    Returns:
        List[Tuple[int, int, str, str]]: List of tuples containing search results
            (file_id, row_number, column_name, value).
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute(
            'SELECT file_id, row_number, column_name, value FROM csv_data '
            'WHERE value LIKE ?',
            (f'%{query}%',),
        )
        results = cursor.fetchall()
        return results
    except sqlite3.Error as e:
        print(f'❌ Error searching CSV data: {e}')
        return []
    finally:
        conn.close()


def update_csv_data(file_id: int, df: pd.DataFrame) -> None:
    """Update modified CSV data in the database.

    Args:
        file_id (int): ID of the file to update.
        df (pd.DataFrame): Updated DataFrame to store.

    Raises:
        sqlite3.Error: If a database operation fails.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # Delete existing data for the file
        cursor.execute('DELETE FROM csv_data WHERE file_id = ?', (file_id,))

        # Insert updated CSV data
        for row_idx, row in df.iterrows():
            for col_name, value in row.items():
                cursor.execute(
                    'INSERT INTO csv_data (file_id, row_number, column_name, value) '
                    'VALUES (?, ?, ?, ?)',
                    (file_id, row_idx, col_name, str(value)),
                )

        conn.commit()
        print(f'✅ CSV file {file_id} updated successfully!')
    except sqlite3.Error as e:
        print(f'❌ Error updating CSV file {file_id}: {e}')
        conn.rollback()
    finally:
        conn.close()


def reset_password(username: str, new_password: str) -> None:
    """Update a user's password with SHA-256 hashing.

    Args:
        username (str): Username whose password is to be updated.
        new_password (str): New password to set.

    Raises:
        sqlite3.Error: If the update operation fails.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
        cursor.execute(
            'UPDATE users SET password = ? WHERE username = ?',
            (hashed_password, username),
        )
        conn.commit()
        print(f"✅ Password for '{username}' updated successfully!")
    except sqlite3.Error as e:
        print(f'❌ Error updating password for {username}: {e}')
        conn.rollback()
    finally:
        conn.close()


if __name__ == '__main__':
    init_db()
    admin_username = os.getenv("ADMIN_USERNAME", st.secrets.get("ADMIN_USERNAME", "admin"))
    admin_password = os.getenv("ADMIN_PASSWORD", st.secrets.get("ADMIN_PASSWORD", "default_password"))
    reset_password(admin_username, admin_password)
