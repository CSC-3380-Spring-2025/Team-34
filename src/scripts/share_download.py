import io
import pandas as pd
import streamlit as st

from src.utils import cached_get_files, cached_get_csv_preview, send_dataset_email, logger

def render_share_data_page() -> None:
    """Render the Share Data page for emailing datasets."""
    st.markdown('<div class="main">', unsafe_allow_html=True)
    st.header('Share Data')
    st.subheader('Share datasets via email')
    files = cached_get_files()
    if files:
        file_options = {file_id: filename for file_id, filename, _, _, _ in files}
        selected_file_id = st.selectbox(
            'Select a dataset to share:',
            options=file_options.keys(),
            format_func=lambda x: file_options[x],
            key='share_select',
        )
        if selected_file_id:
            df = cached_get_csv_preview(selected_file_id)
            if not df.empty:
                email_input = st.text_input('Enter your email address:', key='email_share')
                
                if st.button('Send Data', key='send_share'):
                    if email_input:
                        success = send_dataset_email(
                            email_input,
                            file_options[selected_file_id],
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
    else:
        st.warning('No datasets uploaded yet.')
    st.markdown('</div>', unsafe_allow_html=True)

def render_download_data_page() -> None:
    """Render the Download Data page for downloading datasets."""
    st.markdown('<div class="main">', unsafe_allow_html=True)
    st.header('Download Data')
    st.subheader('Download datasets as CSV, Parquet, JSON, and Excel files.')
    files = cached_get_files()
    if files:
        file_options = {file_id: filename for file_id, filename, _, _, _ in files}
        selected_file_id = st.selectbox(
            'Select a dataset to download:',
            options=file_options.keys(),
            format_func=lambda x: file_options[x],
            key='download_select',
        )
        if selected_file_id:
            df = cached_get_csv_preview(selected_file_id)
            if not df.empty:
                col_dl1, col_dl2 = st.columns(2)
                col_dl3, col_dl4 = st.columns(2)
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
                with col_dl3:
                    json_data=df.to_json(orient='records', indent=2).encode('utf-8')
                    if st.download_button(
                        label='Download JSON',
                        data=json_data,
                        file_name=f'{file_options.get(selected_file_id, "dataset")}.json',
                        mime='application/json',
                        key='download_json_live',
                    ):
                        logger.info(
                            'JSON Downloaded',
                            extra={
                                'username': st.session_state.username or 'Anonymous',
                                'action': 'download_json',
                                'details': f'Downloaded: {file_options.get(selected_file_id, "dataset")}.json',
                            },
                        )
                with col_dl4:
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False)
                    excel_data = excel_buffer.getvalue()
                    if st.download_button(
                        label='Download Excel',
                        data=excel_data,
                        file_name=f'{file_options.get(selected_file_id, "dataset")}.xlsx',
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        key='download_excel_live',
                    ):
                        logger.info(
                            'Excel Downloaded',
                            extra={
                                'username': st.session_state.username or 'Anonymous',
                                'action': 'download_excel',
                                'details': f'Downloaded: {file_options.get(selected_file_id, "dataset")}.xlsx',
                            },
                        )
                    
            else:
                st.error('No data found in the selected dataset.')
    else:
        st.warning('No datasets uploaded yet.')
    st.markdown('</div>', unsafe_allow_html=True)
