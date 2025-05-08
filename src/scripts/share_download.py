"""Share and Download Data Pages rendering for the LSU Datastore Dashboard.

This module provides functions to display Streamlit pages for sharing datasets via
email and downloading datasets in CSV, Parquet, JSON, and Excel formats. It relies
on environment variables (e.g., DATABASE_NAME, SENDGRID_API_KEY, FROM_EMAIL) loaded
from a .env file (ignored by .gitignore) and generates files tracked by Git LFS
(per .gitattributes).
"""

import io
from typing import Dict

import pandas as pd
import streamlit as st

from src.utils import cached_get_files
from src.utils import cached_get_csv_preview
from src.utils import logger
from src.utils import send_dataset_email


def render_share_data_page() -> None:
    """Render the Share Data page for emailing datasets.

    Allows users to select a dataset and send it as a CSV attachment via email using
    SendGrid. Logs user actions (dataset selection, email sharing) to LOG_DIR/LOG_FILE.

    Raises:
        sqlite3.Error: If a database query fails during file retrieval or preview.
        ValueError: If the email address format is invalid.
        sendgrid.SendGridException: If email sending fails.
    """
    st.markdown('<div class="main">', unsafe_allow_html=True)
    st.header("Share Data")
    st.subheader("Share datasets via email")

    files = cached_get_files()
    if files:
        file_options: Dict[int, str] = {
            file_id: filename for file_id, filename, _, _, _ in files
        }
        selected_file_id: int = st.selectbox(
            "Select a dataset to share:",
            options=file_options.keys(),
            format_func=lambda x: file_options[x],
            key="share_select",
        )
        if selected_file_id:
            logger.info(
                "Dataset Selected",
                extra={
                    "username": st.session_state.username or "Anonymous",
                    "action": "share_select",
                    "details": f"Selected dataset: {file_options[selected_file_id]}",
                },
            )
            df: pd.DataFrame = cached_get_csv_preview(selected_file_id)
            if not df.empty:
                email_input: str = st.text_input("Enter your email address:", key="email_share")
                if st.button("Send Data", key="send_share"):
                    if email_input:
                        try:
                            send_dataset_email(
                                email_input,
                                file_options[selected_file_id],
                                df,
                            )
                            st.success(f"Data sent to {email_input}!")
                        except (ValueError, sendgrid.SendGridException) as e:
                            st.error(f"Failed to send email: {e}")
                    else:
                        st.warning("Please enter an email address.")
                        logger.error(
                            "Email Share Failed",
                            extra={
                                "username": st.session_state.username or "Anonymous",
                                "action": "email_share",
                                "details": "No email address provided",
                            },
                        )
            else:
                st.error("No data found in the selected dataset.")
    else:
        st.warning("No datasets uploaded yet.")

    st.markdown("</div>", unsafe_allow_html=True)


def render_download_data_page() -> None:
    """Render the Download Data page for downloading datasets.

    Allows users to select a dataset and download it as CSV, Parquet, JSON, or Excel
    files. Logs download actions to LOG_DIR/LOG_FILE.

    Raises:
        sqlite3.Error: If a database query fails during file retrieval or preview.
    """
    st.markdown('<div class="main">', unsafe_allow_html=True)
    st.header("Download Data")
    st.subheader("Download datasets as CSV, Parquet, JSON, or Excel files")

    files = cached_get_files()
    if files:
        file_options: Dict[int, str] = {
            file_id: filename for file_id, filename, _, _, _ in files
        }
        selected_file_id: int = st.selectbox(
            "Select a dataset to download:",
            options=file_options.keys(),
            format_func=lambda x: file_options[x],
            key="download_select",
        )
        if selected_file_id:
            logger.info(
                "Dataset Selected",
                extra={
                    "username": st.session_state.username or "Anonymous",
                    "action": "download_select",
                    "details": f"Selected dataset: {file_options[selected_file_id]}",
                },
            )
            df: pd.DataFrame = cached_get_csv_preview(selected_file_id)
            if not df.empty:
                csv_col, parquet_col = st.columns(2)
                json_col, excel_col = st.columns(2)

                with csv_col:
                    csv_data: bytes = df.to_csv(index=False).encode("utf-8")
                    if st.download_button(
                        label="Download CSV",
                        data=csv_data,
                        file_name=f"{file_options[selected_file_id]}.csv",
                        mime="text/csv",
                        key="download_csv_live",
                    ):
                        logger.info(
                            "CSV Downloaded",
                            extra={
                                "username": st.session_state.username or "Anonymous",
                                "action": "download_csv",
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
                        key="download_parquet_live",
                    ):
                        logger.info(
                            "Parquet Downloaded",
                            extra={
                                "username": st.session_state.username or "Anonymous",
                                "action": "download_parquet",
                                "details": f"Downloaded: {file_options[selected_file_id]}.parquet",
                            },
                        )

                with json_col:
                    json_data: bytes = df.to_json(
                        orient="records", indent=2
                    ).encode("utf-8")
                    if st.download_button(
                        label="Download JSON",
                        data=json_data,
                        file_name=f"{file_options[selected_file_id]}.json",
                        mime="application/json",
                        key="download_json_live",
                    ):
                        logger.info(
                            "JSON Downloaded",
                            extra={
                                "username": st.session_state.username or "Anonymous",
                                "action": "download_json",
                                "details": f"Downloaded: {file_options[selected_file_id]}.json",
                            },
                        )

                with excel_col:
                    excel_buffer: io.BytesIO = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
                        df.to_excel(writer, index=False)
                    excel_data: bytes = excel_buffer.getvalue()
                    if st.download_button(
                        label="Download Excel",
                        data=excel_data,
                        file_name=f"{file_options[selected_file_id]}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_excel_live",
                    ):
                        logger.info(
                            "Excel Downloaded",
                            extra={
                                "username": st.session_state.username or "Anonymous",
                                "action": "download_excel",
                                "details": f"Downloaded: {file_options[selected_file_id]}.xlsx",
                            },
                        )
            else:
                st.error("No data found in the selected dataset.")
    else:
        st.warning("No datasets uploaded yet.")

    st.markdown("</div>", unsafe_allow_html=True)
