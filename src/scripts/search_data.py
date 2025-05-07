import pandas as pd
import streamlit as st

from src.datastore.database import search_csv_data

def render_search_data_page() -> None:
    """Render the Search Data page for searching across datasets."""
    st.markdown('<div class="main">', unsafe_allow_html=True)
    st.header('Search Data')
    st.subheader('Search across all datasets')
    global_search = st.text_input('Search across all datasets:', key='global_search')
    if global_search:
        results = search_csv_data(global_search)
        if results:
            st.dataframe(
                pd.DataFrame(results, columns=['File ID', 'Row', 'Column', 'Value'])
            )
        else:
            st.warning('No matches found.')
    st.markdown('</div>', unsafe_allow_html=True)
