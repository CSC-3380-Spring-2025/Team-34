import os
import sqlite3
import pandas as pd
import io
import hashlib

# Set up database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "datastore.db")

def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Users Table for Authentication
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Files Metadata Table
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

    # CSV Data Table
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

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

def authenticate_user(username, password):
    """Authenticate user login by checking hashed password."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()

    return result and result[0] == hashed_password

def save_csv_data(filename, content, file_size, file_format, user_id):
    """Save a CSV file and store its data in the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Insert metadata into files table
    cursor.execute("INSERT INTO files (filename, file_size, file_format, user_id) VALUES (?, ?, ?, ?)",
                   (filename, file_size, file_format, user_id))
    file_id = cursor.lastrowid

    # Read CSV content into Pandas
    csv_data = io.BytesIO(content)
    df = pd.read_csv(csv_data)

    # Insert CSV data into csv_data table
    for row_idx, row in df.iterrows():
        for col_name, value in row.items():
            cursor.execute("INSERT INTO csv_data (file_id, row_number, column_name, value) VALUES (?, ?, ?, ?)",
                           (file_id, row_idx, col_name, str(value)))

    conn.commit()
    conn.close()

def get_files():
    """Retrieve stored files metadata from the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename, file_size, file_format, uploaded_at FROM files ORDER BY uploaded_at DESC")
    files = cursor.fetchall()
    conn.close()
    return files

def get_csv_preview(file_id):
    """Retrieve and format CSV data for preview in Streamlit."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT row_number, column_name, value FROM csv_data WHERE file_id = ? ORDER BY row_number",
                   (file_id,))
    rows = cursor.fetchall()

    # Convert to DataFrame
    df = pd.DataFrame(rows, columns=["row_number", "column_name", "value"]).pivot(index="row_number",
                                                                                  columns="column_name",
                                                                                  values="value")
    conn.close()
    return df

def delete_file(file_id):
    """Delete a file and its associated CSV data from the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
    conn.commit()
    conn.close()

def search_csv_data(query):
    """Search all CSV data for a given keyword."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT file_id, row_number, column_name, value FROM csv_data WHERE value LIKE ?",
                       (f"%{query}%",))
        results = cursor.fetchall()
        return results

    except sqlite3.Error as e:
        print(f"❌ Error searching CSV data: {e}")
        return []

    finally:
        conn.close()

def update_csv_data(file_id, df):
    """Update modified CSV data in the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # Delete existing data for the file
        cursor.execute("DELETE FROM csv_data WHERE file_id = ?", (file_id,))

        # Insert updated CSV data
        for row_idx, row in df.iterrows():
            for col_name, value in row.items():
                cursor.execute("INSERT INTO csv_data (file_id, row_number, column_name, value) VALUES (?, ?, ?, ?)",
                               (file_id, row_idx, col_name, str(value)))

        conn.commit()
        print(f"✅ CSV file {file_id} updated successfully!")

    except sqlite3.Error as e:
        print(f"❌ Error updating CSV: {e}")

    finally:
        conn.close()

def reset_password(username, new_password):
    """Update a user's password with SHA-256 hashing."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    hashed_password = hashlib.sha256(new_password.encode()).hexdigest()

    cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_password, username))
    conn.commit()
    conn.close()

    print(f"✅ Password for '{username}' updated successfully!")

# Reset the admin password
reset_password("admin", "NewSecurePassword123")
if __name__ == "__main__":
    init_db()  # Initialize the database when running the script directly
