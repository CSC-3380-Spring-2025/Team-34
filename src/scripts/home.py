import base64
import io
import os
import time
from datetime import datetime
from typing import Dict

import pandas as pd
import plotly.express as px
import psutil
import streamlit as st
from pandas import DataFrame

from src.datastore.database import (
    delete_file,
    save_csv_to_database,
    search_csv_data,
    update_csv_data,
)
from src.utils import cached_get_files, cached_get_csv_preview, logger, send_dataset_email

def render_home_page() -> None:
    """Render the Home page with data management and live features."""
    st.markdown('<div class="main">', unsafe_allow_html=True)

    st.header('LSU Datastore')
    st.subheader('A tool for managing and analyzing data at LSU')
    st.markdown('Created by the LSU Data Science Team', unsafe_allow_html=True)
    st.markdown('Powered by Streamlit', unsafe_allow_html=True)

    base_dir = os.path.dirname(__file__)
    try:
        st.image(
            os.path.join(base_dir, '../lsu_data_icon.png'),
            caption='LSU Datastore Visualization',
            use_container_width=True,
            output_format='PNG',
        )
    except FileNotFoundError:
        st.warning("Image not found. Please add 'lsu_data_icon.png' to your project directory.")

    if st.session_state.logged_in:
        st.subheader('Manage Data')
        uploaded_file = st.file_uploader(
            'Upload dataset (CSV)', type=['csv'], key='upload_csv'
        )
        if uploaded_file:
            with st.spinner('Uploading dataset...'):
                save_csv_to_database(
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    len(uploaded_file.getvalue()),
                    'csv',
                    1,
                )
                time.sleep(1)
            st.success(f'{uploaded_file.name} saved to the database!')

        manage_files = cached_get_files()
        if manage_files:
            manage_file_options = {
                file_id: filename for file_id, filename, size, file_type, created_at in manage_files
            }
            manage_file_id = st.selectbox(
                'Select a dataset to manage:',
                options=manage_file_options.keys(),
                format_func=lambda x: manage_file_options[x],
                key='manage_select',
            )
            if manage_file_id:
                manage_df = cached_get_csv_preview(manage_file_id)
                if not manage_df.empty:
                    st.write(f'**Preview of {manage_file_options[manage_file_id]}:**')
                    st.dataframe(manage_df)

                    st.subheader('Edit Data')
                    edited_df = st.data_editor(manage_df)
                    if st.button('Save Changes'):
                        update_csv_data(manage_file_id, edited_df)
                        st.success('Changes saved!')

                    csv_data = manage_df.to_csv(index=False).encode('utf-8')
                    json_data = manage_df.to_json(orient='records')
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        manage_df.to_excel(writer, index=False)
                    excel_data = output.getvalue()

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.download_button(
                            'Download CSV',
                            data=csv_data,
                            file_name=f'{manage_file_options[manage_file_id]}.csv',
                            mime='text/csv',
                        )
                    with col2:
                        st.download_button(
                            'Download JSON',
                            data=json_data,
                            file_name=f'{manage_file_options[manage_file_id]}.json',
                            mime='application/json',
                        )
                    with col3:
                        st.download_button(
                            'Download Excel',
                            data=excel_data,
                            file_name=f'{manage_file_options[manage_file_id]}.xlsx',
                            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        )

                    if st.button('Delete This Dataset'):
                        delete_file(manage_file_id)
                        st.success(f"Dataset '{manage_file_options[manage_file_id]}' deleted!")
                        st.rerun()
                else:
                    st.error('No data found in the selected dataset.')
        else:
            st.warning('No datasets uploaded yet.')

    st.markdown('<div class="filter-container">', unsafe_allow_html=True)
    col1, col2, _ = st.columns([1, 1, 3])
    with col1:
        majors = ['software_engineering', 'cloud_computing', 'data_science', 'cybersecurity']
        selected_major = st.selectbox(
            'Filter by Major:',
            majors,
            format_func=lambda x: x.replace('_', ' ').title(),
        )
    with col2:
        categories = ['jobs', 'courses', 'research', 'lsu']
        selected_category = st.selectbox(
            'Filter by Category:',
            categories,
            format_func=lambda x: x.upper() if x == 'lsu' else x.title(),
        )
    st.markdown('</div>', unsafe_allow_html=True)

    st.subheader('Summary')
    st.markdown(
        """
        The LSU Datastore is a tool for managing and analyzing datasets at LSU, including research projects, jobs, and courses.
        The Datastore provides a continuously updated platform for accessing data, performing searches, and sharing insights.
        Details of our work are provided in the LSU Data Science Repository.
        We hope that researchers will use the LSU Datastore to gain insights into academic and professional opportunities.
        """
    )

    st.subheader('Usage')
    st.markdown(
        """
        To the left is a dropdown menu for navigating the LSU Datastore features:

        - **Home Page**: Overview of the LSU Datastore platform.
        - **Data Page**: View all CSV files in the LSU Datastore (no login required).
        - **Search Data**: Search for specific entries across all datasets.
        - **Visualize Data**: Explore data visualizations for numerical datasets.
        - **Share Data**: Share datasets via email with collaborators.
        - **Download Data**: Download datasets in CSV or Parquet format.
        """
    )

    st.subheader('LSU Datastore - Livestream Data Store')
    st.markdown('Select a date to view Jobs, Courses, Research Projects, or LSU-specific data for that day.')

    selected_date = st.date_input(
        'Select a date:', value=datetime.now(), key='date_select'
    )
    formatted_date = selected_date.strftime('%Y-%m-%d')

    files = cached_get_files()
    if files:
        file_options: Dict[int, str] = {}
        for file_id, filename, size, file_type, created_at in files:
            if selected_category == 'lsu':
                if (
                    filename.lower().startswith('lsu')
                    and formatted_date in filename
                    and (selected_major in filename or 'relevant' in filename)
                ):
                    file_options[file_id] = filename
            else:
                if (
                    selected_category in filename
                    and formatted_date in filename
                    and selected_major in filename
                ):
                    file_options[file_id] = filename

        if file_options:
            col1, col2 = st.columns([3, 1])
            with col1:
                selected_file_id = st.selectbox(
                    'Select a dataset to preview:',
                    options=file_options.keys(),
                    format_func=lambda x: file_options[x],
                    key='live_select',
                )
                if selected_file_id:
                    logger.info(
                        'Dataset Selected',
                        extra={
                            'username': st.session_state.username or 'Anonymous',
                            'action': 'select_dataset',
                            'details': f'Selected dataset: {file_options[selected_file_id]}',
                        },
                    )
                    df = cached_get_csv_preview(selected_file_id)
                    if not df.empty:
                        st.write(f'**Preview of {file_options[selected_file_id]}:**')
                        st.dataframe(df, hide_index=True)

                        st.subheader('Download Data')
                        col_dl1, col_dl2 = st.columns(2)
                        with col_dl1:
                            csv_data = df.to_csv(index=False).encode('utf-8')
                            if st.download_button(
                                label='Download CSV',
                                data=csv_data,
                                file_name=f'{file_options[selected_file_id]}.csv',
                                mime='text/csv',
                                key='download_csv_live',
                            ):
                                logger.info(
                                    'CSV Downloaded',
                                    extra={
                                        'username': st.session_state.username or 'Anonymous',
                                        'action': 'download_csv',
                                        'details': f'Downloaded: {file_options[selected_file_id]}.csv',
                                    },
                                )
                        with col_dl2:
                            parquet_buffer = io.BytesIO()
                            df.to_parquet(parquet_buffer, engine='pyarrow', index=False)
                            parquet_data = parquet_buffer.getvalue()
                            if st.download_button(
                                label='Download Parquet',
                                data=parquet_data,
                                file_name=f'{file_options.get(selected_file_id, "dataset")}.parquet',
                                mime='application/octet-stream',
                                key='download_parquet_live',
                            ):
                                logger.info(
                                    'Parquet Downloaded',
                                    extra={
                                        'username': st.session_state.username or 'Anonymous',
                                        'action': 'download_parquet',
                                        'details': f'Downloaded: {file_options.get(selected_file_id, "dataset")}.parquet',
                                    },
                                )

                        st.subheader('Share Data via Email')
                        email_input = st.text_input(
                            'Enter your email address:', key='email_live'
                        )

                        if st.button('Send Data', key='send_live'):
                            if email_input:
                                success = send_dataset_email(
                                    email_input,
                                    file_options.get(selected_file_id, "dataset"),
                                    df
                                )
                                if success:
                                    st.success(f"Data sent to {email_input}!")
                                else:
                                    st.error("Failed to send email.")
                            else:
                                st.warning('Please enter an email address.')
                                logger.error(
                                    'Email Share Failed',
                                    extra={
                                        'username': st.session_state.username or 'Anonymous',
                                        'action': 'email_share',
                                        'details': 'No email address provided',
                                    },
                                )
                    else:
                        st.error('No data found in the selected dataset.')
            with col2:
                try:
                    st.markdown(
                        f'<div class="logo-image"><img src="data:image/png;base64,'
                        f'{base64.b64encode(open(os.path.join(base_dir, "../lsu_logo.png"), "rb").read()).decode()}" '
                        f'alt="LSU Datastore Process" style="width:100%;"></div>',
                        unsafe_allow_html=True,
                    )
                    st.caption('LSU Datastore Process')
                except FileNotFoundError:
                    st.warning("Image not found. Please add 'lsu_logo.png' to your project directory.")
        else:
            st.warning(
                f"No {selected_category.upper() if selected_category == 'lsu' else selected_category.capitalize()} "
                f"data available for {selected_major.replace('_', ' ').capitalize()} on {formatted_date}."
            )
    else:
        st.warning('No datasets uploaded yet.')

    if files and file_options and selected_file_id and not df.empty:
        st.subheader('Visualize Data')
        numerical_cols = df.select_dtypes(include=['number']).columns
        if len(numerical_cols) > 1:
            x_axis = st.selectbox(
                'Select X-Axis:', numerical_cols, index=1, key='x_axis_home'
            )
            y_axis = st.selectbox(
                'Select Y-Axis:', numerical_cols, index=0, key='y_axis_home'
            )
            fig = px.scatter(df, x=x_axis, y=y_axis, title=f'{x_axis} vs {y_axis}')
            st.plotly_chart(fig, use_container_width=True)
        elif len(numerical_cols) == 1:
            st.warning('Only one numerical column was found; cannot plot.')
        else:
            st.warning('No numerical columns found for visualization.')

        st.subheader('Search Data')
        global_search = st.text_input('Search across all datasets:', key='global_search_home')
        if global_search:
            results = search_csv_data(global_search)
            if results:
                st.dataframe(
                    pd.DataFrame(results, columns=['File ID', 'Row', 'Column', 'Value'])
                )
            else:
                st.warning('No matches found.')

    if st.session_state.logged_in:
        st.subheader('Live Feed Logs')
        st.markdown('View and download daily logs of live feed activities for testing and optimization.')

        log_files = [
            f for f in os.listdir(log_dir) if f.startswith('live_feed_log') and f.endswith('.csv')
        ]
        if log_files:
            selected_log = st.selectbox(
                'Select a log file to view:', log_files, key='log_select'
            )
            if selected_log:
                log_path = os.path.join(log_dir, selected_log)
                try:
                    log_df = pd.read_csv(log_path)
                    st.write(f'**Log: {selected_log}**')
                    st.dataframe(log_df, hide_index=True)

                    log_csv = log_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label='Download Log as CSV',
                        data=log_csv,
                        file_name=selected_log,
                        mime='text/csv',
                        key='download_log_csv',
                    )
                except Exception as e:
                    st.error(f'Error reading log file: {str(e)}')
        else:
            st.warning('No log files available.')

        st.subheader('Live Terminal Logs')
        st.markdown('View live logs in a terminal-like interface.')
        log_placeholder = st.empty()
        for _ in range(60):
            logs = memory_handler.get_logs()
            log_text = '\n'.join(logs[-20:])
            log_placeholder.markdown(
                f'<div class="terminal-log">{log_text}</div>',
                unsafe_allow_html=True,
            )
            time.sleep(1)

    st.subheader('System Performance Metrics')
    placeholder = st.empty()
    for _ in range(60):
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_usage = psutil.virtual_memory().percent
        with placeholder.container():
            col1, col2 = st.columns(2)
            with col1:
                st.metric('CPU Usage', f'{cpu_usage}%')
            with col2:
                st.metric('Memory Usage', f'{memory_usage}%')

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('---')
    st.markdown(
        '[Link to DAG Grid](https://animated-train-jjvx5x4q9g73p5v5-8080.app.github.dev/dags/fetch_store_dag/grid)'
    )
