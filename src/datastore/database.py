import os
import sqlite3
import pandas as pd
import io

# Get absolute path for database file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "datastore.db")


def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create Files Table with metadata (without content)
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
    # Create CSV Data Table for Structured Storage
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


def save_csv_data(filename, content, file_size, file_format, user_id):
    """Store CSV metadata and structured row data (without BLOB content)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # Insert file metadata (without content)
        cursor.execute(
            "INSERT INTO files (filename, file_size, file_format, user_id) VALUES (?, ?, ?, ?)",
            (filename, file_size, file_format, user_id)
        )
        file_id = cursor.lastrowid

        # Convert BLOB to Pandas DataFrame
        csv_data = io.BytesIO(content)
        df = pd.read_csv(csv_data)

        # Store CSV Row Data
        for row_idx, row in df.iterrows():
            for col_name, value in row.items():
                cursor.execute(
                    "INSERT INTO csv_data (file_id, row_number, column_name, value) VALUES (?, ?, ?, ?)",
                    (file_id, row_idx, col_name, str(value))
                )

        conn.commit()
        print(f"✅ CSV file '{filename}' stored successfully!")

    except Exception as e:
        print(f"❌ Error saving CSV '{filename}': {e}")

    finally:
        conn.close()

def search_csv_data(query):
    """Search all CSV data for a given keyword."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT file_id, row_number, column_name, value FROM csv_data WHERE value LIKE ?",
            (f"%{query}%",)
        )
        results = cursor.fetchall()
        return results

    except sqlite3.Error as e:
        print(f"❌ Error searching CSV data: {e}")
        return []

    finally:
        conn.close()


def get_files():
    """Retrieve stored files metadata from the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, filename, file_size, file_format, uploaded_at FROM files ORDER BY uploaded_at DESC")
        files = cursor.fetchall()
        return files

    except Exception as e:
        print(f"❌ Error retrieving files: {e}")
        return []

    finally:
        conn.close()

def delete_file(file_id):
    """Deletes a file and its associated CSV data."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM csv_data WHERE file_id = ?", (file_id,))
        cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
        conn.commit()
        print(f"✅ File {file_id} deleted successfully!")

    except sqlite3.Error as e:
        print(f"❌ Error deleting file {file_id}: {e}")

    finally:
        conn.close()



def get_csv_preview(file_id):
    """Retrieve first 5 rows of a CSV from the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # Retrieve distinct columns
        cursor.execute("SELECT DISTINCT column_name FROM csv_data WHERE file_id = ?", (file_id,))
        columns = [row[0] for row in cursor.fetchall()]

        # Retrieve first 5 rows of CSV data
        cursor.execute(
            "SELECT row_number, column_name, value FROM csv_data WHERE file_id = ? ORDER BY row_number LIMIT 5",
            (file_id,)
        )
        rows = cursor.fetchall()

        # Convert to Pandas DataFrame
        if rows:
            df = pd.DataFrame(rows, columns=["row_number", "column_name", "value"])
            df = df.pivot(index="row_number", columns="column_name", values="value")
            return df
        else:
            return pd.DataFrame()

    except Exception as e:
        print(f"❌ Error retrieving CSV preview for file ID {file_id}: {e}")
        return pd.DataFrame()

    finally:
        conn.close()


if __name__ == "__main__":
    init_db()  # Initialize the database when running the script
