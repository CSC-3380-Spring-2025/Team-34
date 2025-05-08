"""Search Data Page rendering for the LSU Datastore Dashboard.

This module provides the render_search_data_page function to display a Streamlit
page for searching across all datasets in the database. It relies on environment
variables (e.g., DATABASE_NAME) loaded from a .env file (ignored by .gitignore)
and searches CSV files tracked by Git LFS (per .gitattributes).
"""

import pandas as pd
import streamlit as st

from src.utils import logger
from src.datastore.database import search_csv_data


def render_search_data_page() -> None:
    """Render the Search Data page for searching across datasets.

    Allows users to enter a search query, displays matching results from all datasets
    in a DataFrame, and logs the search action. Results include file ID, row, column,
    and value for each match.

    Raises:
        sqlite3.Error: If a database query fails during search.
    """
    st.markdown('<div class="main">', unsafe_allow_html=True)
    st.header("Search Data")
    st.subheader("Search across all datasets")

    global_search: str = st.text_input("Search across all datasets:", key="global_search")
    if global_search:
        logger.info(
            "Search Performed",
            extra={
                "username": st.session_state.username or "Anonymous",
                "action": "search_data",
                "details": f"Query: {global_search}",
            },
        )
        results = search_csv_data(global_search)
        if results:
            st.dataframe(
                pd.DataFrame(
                    results,
                    columns=["File ID", "Row", "Column", "Value"],
                ),
                hide_index=True,
            )
        else:
            st.warning("No matches found.")

    st.markdown("</div>", unsafe_allow_html=True)
