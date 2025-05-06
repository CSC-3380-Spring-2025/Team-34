import pandas as pd
import plotly.express as px
import streamlit as st

from src.utils import cached_get_files, cached_get_csv_preview

def render_visualize_data_page() -> None:
    """Render the Visualize Data page for exploring data visualizations."""
    st.markdown('<div class="main">', unsafe_allow_html=True)
    st.header('Visualize Data')
    st.subheader('Explore data visualizations')
    files = cached_get_files()
    if files:
        file_options = {file_id: filename for fileid, filename, , ,  in files}
        selected_file_id = st.selectbox(
            'Select a dataset to visualize:',
            options=file_options.keys(),
            format_func=lambda x: file_options[x],
            key='visualize_select',
        )
        if selected_file_id:
            df = cached_get_csv_preview(selected_file_id)
            if not df.empty:
                numerical_cols = df.select_dtypes(include=['number']).columns
                if len(numerical_cols) > 1:
                    x_axis = st.selectbox(
                        'Select X-Axis:', numerical_cols, index=1, key='x_axis'
                    )
                    y_axis = st.selectbox(
                        'Select Y-Axis:', numerical_cols, index=0, key='y_axis'
                    )
                    fig = px.scatter(df, x=x_axis, y=y_axis, title=f'{x_axis} vs {y_axis}')
                    st.plotly_chart(fig, use_container_width=True)
                elif len(numerical_cols) == 1:
                    st.warning('Only one numerical column was found; cannot plot.')
                else:
                    st.warning('No numerical columns found for visualization.')
            else:
                st.error('No data found in the selected dataset.')
    else:
        st.warning('No datasets uploaded yet.')
    st.markdown('</div>', unsafe_allow_html=True)
