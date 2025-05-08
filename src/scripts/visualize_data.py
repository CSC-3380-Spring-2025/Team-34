"""Visualize Data Page rendering for the LSU Datastore Dashboard.

This module provides the render_visualize_data_page function to display a Streamlit
page for exploring scatter plot visualizations of numerical data in datasets. It
relies on environment variables (e.g., DATABASE_NAME) loaded from a .env file
(ignored by .gitignore) and visualizes CSV files tracked by Git LFS (per
.gitattributes).
"""

from typing import Dict

import pandas as pd
import plotly.express as px
import streamlit as st

from src.utils import cached_get_files
from src.utils import cached_get_csv_preview
from src.utils import logger


def render_visualize_data_page() -> None:
    """Render the Visualize Data page for exploring data visualizations.

    Allows users to select a dataset and create scatter plots for numerical columns
    using Plotly. Logs dataset selection to LOG_DIR/LOG_FILE.

    Raises:
        sqlite3.Error: If a database query fails during file retrieval or preview.
    """
    st.markdown('<div class="main">', unsafe_allow_html=True)
    st.header("Visualize Data")
    st.subheader("Explore data visualizations")

    files = cached_get_files()
    if files:
        file_options: Dict[int, str] = {
            file_id: filename
            for file_id, filename, size, file_type, created_at in files
        }
        selected_file_id: int = st.selectbox(
            "Select a dataset to visualize:",
            options=file_options.keys(),
            format_func=lambda x: file_options[x],
            key="visualize_select",
        )
        if selected_file_id:
            logger.info(
                "Dataset Selected",
                extra={
                    "username": st.session_state.username or "Anonymous",
                    "action": "visualize_select",
                    "details": f"Selected dataset: {file_options[selected_file_id]}",
                },
            )
            df: pd.DataFrame = cached_get_csv_preview(selected_file_id)
            if not df.empty:
                numerical_cols = df.select_dtypes(include=["number"]).columns
                if len(numerical_cols) > 1:
                    x_axis: str = st.selectbox(
                        "Select X-Axis:",
                        numerical_cols,
                        index=1,
                        key="x_axis",
                    )
                    y_axis: str = st.selectbox(
                        "Select Y-Axis:",
                        numerical_cols,
                        index=0,
                        key="y_axis",
                    )
                    fig = px.scatter(df, x=x_axis, y=y_axis, title=f"{x_axis} vs {y_axis}")
                    st.plotly_chart(fig, use_container_width=True)
                elif len(numerical_cols) == 1:
                    st.warning("Only one numerical column was found; cannot plot.")
                else:
                    st.warning("No numerical columns found for visualization.")
            else:
                st.error("No data found in the selected dataset.")
    else:
        st.warning("No datasets uploaded yet.")

    st.markdown("</div>", unsafe_allow_html=True)
