"""Data Page rendering for the LSU Datastore Dashboard.

This module provides the render_data_page function to display a Streamlit page for
viewing, previewing, and downloading CSV and Parquet files from the database.
It relies on environment variables (e.g., DATABASE_NAME) loaded from a .env file
(ignored by .gitignore) and generates files tracked by Git LFS (per .gitattributes).
"""

import io
from typing import Dict

import pandas as pd
import streamlit as st

from src.utils import cached_get_files, cached_get_csv_preview, logger


def render_data_page() -> None:
    """Render the Data Page for viewing and downloading CSV and Parquet files.

    Displays a list of available CSV files, allows users to preview a selected file,
    and provides options to download the file as CSV or Parquet. Logs user actions
    (file selection, downloads) to LOG_DIR/LOG_FILE.

    Raises:
        sqlite3.Error: If a database query fails during file retrieval or preview.
    """
    st.markdown('<div class="main">', unsafe_allow_html=True)
    st.subheader("View all CSV files in the LSU Datastore")

    files = cached_get_files()
    if files:
        file_options: Dict[int, str] = {
            file_id: filename for file_id, filename, size, file_type, created_at in files
        }
        selected_file_id: int = st.selectbox(
            "Select a CSV file to preview:",
            options=file_options.keys(),
            format_func=lambda x: file_options[x],
            key="data_page_csv_select",
        )
        if selected_file_id:
            logger.info(
                "CSV File Selected",
                extra={
                    "username": st.session_state.username or "Anonymous",
                    "action": "data_page_csv_select",
                    "details": f"Selected dataset: {file_options[selected_file_id]}",
                },
            )
            df: pd.DataFrame = cached_get_csv_preview(selected_file_id)
            if not df.empty:
                st.write(f"Preview of {file_options[selected_file_id]}:")
                st.dataframe(df, hide_index=True)

                st.subheader("Download Data")
                csv_col, parquet_col = st.columns(2)
                with csv_col:
                    csv_data: bytes = df.to_csv(index=False).encode("utf-8")
                    if st.download_button(
                        label="Download CSV",
                        data=csv_data,
                        file_name=f"{file_options[selected_file_id]}.csv",
                        mime="text/csv",
                        key="download_csv_data_page",
                    ):
                        logger.info(
                            "CSV Downloaded",
                            extra={
                                "username": st.session_state.username or "Anonymous",
                                "action": "download_csv_data_page",
                                "details": f"Downloaded: {file_options[selected_file_id]}.csv",
                            },
                        )
                with parquet_col:
                    parquet_buffer: io.BytesIO = io.BytesIO()
                    df.to_parquet(parquet_buffer, engine="pyarrow", index=False)
                    parquet_data: bytes = parquet_buffer.getvalue()
                    if st.download_button(
                        label="Download Parquet",
                        data=parquet_data,
                        file_name=f"{file_options[selected_file_id]}.parquet",
                        mime="application/octet-stream",
                        key="download_parquet_data_page",
                    ):
                        logger.info(
                            "Parquet Downloaded",
                            extra={
                                "username": st.session_state.username or "Anonymous",
                                "action": "download_parquet_data_page",
                                "details": f"Downloaded: {file_options[selected_file_id]}.parquet",
                            },
                        )
            else:
                st.error("No data found in the selected dataset.")
    else:
        st.warning("No CSV files available in the database.")
    st.markdown("</div>", unsafe_allow_html=True)
