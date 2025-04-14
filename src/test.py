import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
import io
import time
import plotly.express as px
from src.datastore.database import (
    save_csv_data, get_files, get_csv_preview, delete_file, search_csv_data, update_csv_data, authenticate_user
)
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
import base64
import re

# Load environment variables from .env file (for local development only)
if not os.getenv("IS_STREAMLIT_CLOUD", False):
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

# Set page configuration
st.set_page_config(page_title="📊 LSU Datastore", layout="wide")

# Determine color scheme based on login status
if st.session_state.get('logged_in', False):
    # Blue and Gray for logged-in state (RasCore-inspired)
    background_color = "#F5F6F5"  # Light gray
    main_background = "#FFFFFF"
    sidebar_background = "#E8ECEF"
    primary_color = "#0056D2"  # Blue
    secondary_color = "#003087"  # Darker blue for hover
    text_color = "#333333"
    text_light_color = "#666666"
else:
    # LSU Purple and Gold for pre-login state
    background_color = "url('bck.jpg')"  # Local image background
    main_background = "rgba(255, 255, 255, 0.9)"  # Semi-transparent white
    sidebar_background = "#461D7C"
    primary_color = "#461D7C"
    secondary_color = "#FABD00"
    text_color = "#000000"
    text_light_color = "#461D7C"

# Custom CSS with dynamic color scheme
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
        @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');

        /* General Styling */
        body, .stApp {{
            background: {background_color} !important;
            background-size: cover !important;
            background-position: center !important;
            color: {text_color} !important;
            font-family: 'Roboto', sans-serif !important;
        }}

        /* Main content area */
        .main {{
            background-color: {main_background};
            padding: 40px;
            margin: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}

        /* Sidebar */
        .stSidebar {{
            background-color: {sidebar_background} !important;
            padding: 20px !important;
        }}
        .stSidebar .sidebar-content {{
            width: 200px !important;
        }}
        .stSidebar h2 {{
            font-size: 18px !important;
            color: #FFFFFF !important;  /* White for contrast on purple sidebar */
            margin-bottom: 10px !important;
            font-weight: bold !important;
        }}
        .stSidebar a, .stSidebar .stSelectbox label {{
            color: {primary_color} !important;
            text-decoration: none !important;
            font-size: 14px !important;
        }}
        .stSidebar a:hover {{
            color: {secondary_color} !important;
            text-decoration: underline !important;
        }}

        /* Headers and text */
        h1, h2, h3 {{
            color: {text_color} !important;
            font-family: 'Roboto', sans-serif !important;
            font-weight: bold !important;
        }}
        h1 {{
            font-size: 32px !important;
            margin-bottom: 10px !important;
        }}
        h2 {{
            font-size: 24px !important;
            margin-top: 30px !important;
            margin-bottom: 15px !important;
        }}
        p {{
            font-size: 16px !important;
            line-height: 1.6 !important;
            color: {text_light_color} !important;
            font-weight: bold !important;
        }}

        /* Images */
        .ras-image {{
            max-width: 100%;
            border: 2px solid {primary_color};
            border-radius: 8px;
        }}

        /* Buttons */
        .stButton>button {{
            background-color: {primary_color};
            color: #FFFFFF;
            border-radius: 5px;
            padding: 8px 16px;
            font-weight: bold;
            border: none;
            transition: background-color 0.3s;
        }}
        .stButton>button:hover {{
            background-color: {secondary_color};
        }}

        /* Filter Dropdowns */
        .filter-container {{
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }}

        /* Demo Label */
        .demo-info {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
            justify-content: center;
        }}
        .demo-text {{
            font-size: 14px;
            color: {text_light_color};
            font-weight: bold;
        }}
        .live-demo-badge {{
            background: linear-gradient(45deg, {primary_color}, {secondary_color});
            color: #FFFFFF;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 700;
            text-transform: uppercase;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
            display: flex;
            align-items: center;
            gap: 5px;
            animation: pulse 2s infinite;
        }}
        .live-demo-badge i {{
            color: #FFFFFF;
        }}
        @keyframes pulse {{
            0% {{
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
            }}
            50% {{
                box-shadow: 0 2px 15px rgba(0, 0, 0, 0.5);
            }}
            100% {{
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
            }}
        }}
    </style>
""", unsafe_allow_html=True)

# Session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'show_lsu_datastore' not in st.session_state:
    st.session_state.show_lsu_datastore = False

# Sidebar Navigation (mimicking RasCore with updated links)
with st.sidebar:
    st.header("DATABASE-RELATED LINKS")
    st.markdown("[GitHub Page](https://github.com)")

    st.header("SOFTWARE-RELATED LINKS")
    st.markdown("[BioPython](https://biopython.org/)")
    st.markdown("[RDKit](https://www.rdkit.org/)")
    st.markdown("[PDBrenum](https://pdbrenumbering.org/)")
    st.markdown("[fpocket](https://github.com/Discngine/fpocket)")
    st.markdown("[PyMOL](https://pymol.org/)")
    st.markdown("[3dmol](https://3dmol.csb.pitt.edu/)")
    st.markdown("[pandas](https://pandas.pydata.org/)")
    st.markdown("[NumPy](https://numpy.org/)")
    st.markdown("[SciPy](https://scipy.org/)")
    st.markdown("[sklearn](https://scikit-learn.org/)")
    st.markdown("[matplotlib](https://matplotlib.org/)")
    st.markdown("[seaborn](https://seaborn.pydata.org/)")
    st.markdown("[streamlit](https://streamlit.io/)")

    # Sidebar Login Panel
    st.header("USER LOGIN")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login"):
        # Clear the page and show a loading spinner for 3 seconds
        st.empty()
        with st.spinner("Logging in..."):
            time.sleep(3)  # 3-second delay with blank page
        if authenticate_user(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.show_lsu_datastore = (username == "admin" and password == "NewSecurePassword123")
            st.success(f"Logged in as {username}!")
            st.rerun()
        else:
            st.error("Invalid credentials")
            st.rerun()

    if st.session_state.logged_in:
        if st.button("Logout"):
            # Clear the page and show a loading spinner for 3 seconds
            st.empty()
            with st.spinner("Logging out..."):
                time.sleep(3)  # 3-second delay with blank page
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.show_lsu_datastore = False
            st.rerun()

# Main Content Area
with st.container():
    # Demo Label at the Top
    st.markdown(f"""
        <div class="demo-info">
            <span class="demo-text">Demo 1.0.0</span>
            <span class="live-demo-badge"><i class="fas fa-rocket"></i> Live Demo</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main">', unsafe_allow_html=True)

    # Header Section
    st.header("LSU Datastore")
    st.subheader("A tool for managing and analyzing data at LSU")
    st.markdown("Created by the LSU Data Science Team", unsafe_allow_html=True)
    st.markdown("Powered by Streamlit", unsafe_allow_html=True)

    # Placeholder for an image (replace with your actual image path)
    base_dir = os.path.dirname(__file__)
    try:
        st.image(os.path.join(base_dir, "lsu_data_icon.png"), caption="LSU Datastore Visualization", use_container_width=True, output_format="PNG")
    except FileNotFoundError:
        st.warning("Image not found. Please add 'lsu_data_icon.png' to your project directory.")

    # Filter Dropdowns (top left)
    st.markdown('<div class="filter-container">', unsafe_allow_html=True)
    col1, col2, _ = st.columns([1, 1, 3])
    with col1:
        majors = ["software_engineering", "cloud_computing", "data_science"]
        selected_major = st.selectbox("Filter by Major:", majors, format_func=lambda x: x.replace("_", " ").capitalize())
    with col2:
        categories = ["jobs", "courses", "research", "lsu"]
        selected_category = st.selectbox("Filter by Category:", categories, format_func=lambda x: x.upper() if x == "lsu" else x.capitalize())
    st.markdown('</div>', unsafe_allow_html=True)

    # Summary Section
    st.subheader("Summary")
    st.markdown("""
        The LSU Datastore is a tool for managing and analyzing datasets at LSU, including research projects, jobs, and courses. 
        The Datastore provides a continuously updated platform for accessing data, performing searches, and sharing insights. 
        Details of our work are provided in the LSU Data Science Repository. 
        We hope that researchers will use the LSU Datastore to gain insights into academic and professional opportunities.
    """)

    # Usage Section
    st.subheader("Usage")
    st.markdown("""
        To the left is a dropdown menu for navigating the LSU Datastore features:

        - **Home Page**: Overview of the LSU Datastore platform.
        - **Database Overview**: View and manage datasets stored in the LSU Datastore.
        - **Search Data**: Search for specific entries across all datasets.
        - **Visualize Data**: Explore data visualizations for numerical datasets.
        - **Share Data**: Share datasets via email with collaborators.
        - **Manage Data**: Upload, edit, and delete datasets (requires login).
    """)

    # Livestream Data Store Section with Filters and Calendar
    st.subheader("LSU Datastore - Livestream Data Store")
    st.markdown("Select a date to view Jobs, Courses, Research Projects, or LSU-specific data for that day.")

    # Calendar widget for date selection
    selected_date = st.date_input("Select a date:", value=datetime.now(), key="date_select")
    formatted_date = selected_date.strftime("%Y-%m-%d")

    files = get_files()
    if files:
        file_options = {}
        for file_id, filename, _, _, _ in files:
            # Check if the filename matches the selected date, major, and category
            if selected_category == "lsu":
                # For "lsu" category, match files starting with "lsu"
                if (filename.lower().startswith("lsu") and 
                    formatted_date in filename and 
                    selected_major in filename):
                    file_options[file_id] = filename
            else:
                # For other categories, match as before
                if (selected_category in filename and 
                    formatted_date in filename and 
                    selected_major in filename):
                    file_options[file_id] = filename

        if file_options:
            col1, col2 = st.columns([3, 1])
            with col1:
                selected_file_id = st.selectbox(
                    "Select a dataset to preview:",
                    options=file_options.keys(),
                    format_func=lambda x: file_options[x],
                    key="live_select"
                )
                if selected_file_id:
                    df = get_csv_preview(selected_file_id)
                    if not df.empty:
                        st.write(f"**Preview of {file_options[selected_file_id]}:**")
                        st.dataframe(df)

                        # Email functionality
                        st.subheader("Share Data via Email")
                        email_input = st.text_input("Enter your email address:", key="email_live")
                        if st.button("Send Data", key="send_live"):
                            if email_input:
                                email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
                                if not re.match(email_regex, email_input):
                                    st.error("Invalid email address format.")
                                else:
                                    try:
                                        csv_buffer = io.StringIO()
                                        df.to_csv(csv_buffer, index=False)
                                        csv_data = csv_buffer.getvalue().encode('utf-8')
                                        encoded_file = base64.b64encode(csv_data).decode()

                                        message = Mail(
                                            from_email='bdav213@lsu.edu',
                                            to_emails=email_input,
                                            subject=f'LSU Datastore: {file_options[selected_file_id]} Data',
                                            html_content=f'<p>Attached is the data from {file_options[selected_file_id]} as viewed on the LSU Datastore Dashboard.</p>'
                                        )

                                        attachment = Attachment(
                                            FileContent(encoded_file),
                                            FileName(file_options[selected_file_id]),
                                            FileType('text/csv'),
                                            Disposition('attachment')
                                        )
                                        message.attachment = attachment

                                        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
                                        response = sg.send(message)

                                        if response.status_code == 202:
                                            st.success(f"Data sent to {email_input}!")
                                        else:
                                            st.error(f"Failed to send email. Status code: {response.status_code}")
                                    except Exception as e:
                                        st.error(f"Error sending email: {str(e)}")
                            else:
                                st.warning("Please enter an email address.")
                    else:
                        st.error("No data found in the selected dataset.")
            with col2:
                try:
                    st.image(os.path.join(base_dir, "lsu_logo.png"), caption="LSU Datastore Process", use_container_width=True, output_format="PNG")
                except FileNotFoundError:
                    st.warning("Image not found. Please add 'lsu_logo.png' to your project directory.")
        else:
            st.warning(f"No {selected_category.upper() if selected_category == 'lsu' else selected_category.capitalize()} data available for {selected_major.replace('_', ' ').capitalize()} on {formatted_date}.")
    else:
        st.warning("No datasets uploaded yet.")

    # Data Visualization Section
    if files and file_options and selected_file_id and not df.empty:
        st.subheader("Visualize Data")
        numerical_cols = df.select_dtypes(include=["number"]).columns
        if len(numerical_cols) > 0:
            x_axis = st.selectbox("Select X-Axis:", numerical_cols, key="x_axis")
            y_axis = st.selectbox("Select Y-Axis:", numerical_cols, key="y_axis")
            fig = px.scatter(df, x=x_axis, y=y_axis, title=f"{x_axis} vs {y_axis}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No numerical columns found for visualization.")

    # Search Data Section
    st.subheader("Search Data")
    global_search = st.text_input("Search across all datasets:")
    if global_search:
        results = search_csv_data(global_search)
        if results:
            st.dataframe(pd.DataFrame(results, columns=["File ID", "Row", "Column", "Value"]))
        else:
            st.warning("No matches found.")

    # Manage Data Section (visible after login)
    if st.session_state.logged_in:
        st.subheader("Manage Data")
        uploaded_file = st.file_uploader("Upload dataset (CSV)", type=["csv"])
        if uploaded_file:
            with st.spinner("Uploading dataset..."):
                save_csv_data(uploaded_file.name, uploaded_file.getvalue(), len(uploaded_file.getvalue()), "csv", 1)
                time.sleep(1)
            st.success(f"{uploaded_file.name} saved to the database!")

        if files:
            st.write("**Manage Stored Datasets:**")
            manage_file_id = st.selectbox("Select a dataset to manage:", options=file_options.keys(), format_func=lambda x: file_options[x], key="manage_select")
            if manage_file_id:
                manage_df = get_csv_preview(manage_file_id)
                if not manage_df.empty:
                    st.write(f"**Preview of {file_options[manage_file_id]}:**")
                    st.dataframe(manage_df)

                    st.subheader("Edit Data")
                    edited_df = st.data_editor(manage_df)
                    if st.button("Save Changes"):
                        update_csv_data(manage_file_id, edited_df)
                        st.success("Changes saved!")

                    csv_data = manage_df.to_csv(index=False).encode("utf-8")
                    json_data = manage_df.to_json(orient="records")
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        manage_df.to_excel(writer, index=False)
                    excel_data = output.getvalue()

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.download_button("Download CSV", data=csv_data, file_name=f"{file_options[manage_file_id]}.csv", mime="text/csv")
                    with col2:
                        st.download_button("Download JSON", data=json_data, file_name=f"{file_options[manage_file_id]}.json", mime="application/json")
                    with col3:
                        st.download_button("Download Excel", data=excel_data, file_name=f"{file_options[manage_file_id]}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

                    if st.button("Delete This Dataset"):
                        delete_file(manage_file_id)
                        st.success(f"Dataset '{file_options[manage_file_id]}' deleted!")
                        st.rerun()
                else:
                    st.error("No data found in the selected dataset.")
        else:
            st.warning("No datasets uploaded yet.")

    st.markdown('</div>', unsafe_allow_html=True)

# Link to DAG Grid
st.markdown("---")
st.markdown("[Link to DAG Grid](https://animated-train-jjvx5x4q9g73p5v5-8080.app.github.dev/dags/fetch_store_dag/grid)")
