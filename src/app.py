#!/usr/bin/env python3
"""Streamlit application for the LSU Datastore Dashboard.

This module provides a web interface for managing, visualizing, and sharing datasets
at LSU, with user authentication, data upload, search, and live logging features.
It relies on environment variables loaded from a .env file (ignored by .gitignore)
and may load CSV files tracked by Git LFS (per .gitattributes). Logs are written to
LOG_DIR/LOG_FILE as CSV files.

Environment Variables:
    LOG_DIR: Directory for log files (e.g., 'logs').
    LOG_FILE: Base name of the log file (e.g., 'live_feed_log').
    USERNAME: Admin username for authentication (e.g., 'admin').
    PASSWORD: Admin password for authentication.
"""

import logging
import os
import sys
import time
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from typing import List

import streamlit as st
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.datastore.database import authenticate_user
from src.scripts.home import render_home_page
from src.scripts.data_page import render_data_page
from src.scripts.search_data import render_search_data_page
from src.scripts.visualize_data import render_visualize_data_page
from src.scripts.share_download import render_share_data_page
from src.scripts.share_download import render_download_data_page
from src.utils import get_secret, MemoryHandler, CSVFormatter, CustomTimedRotatingFileHandler
from src.utils import logger

# Load environment variables
load_dotenv()


# Set page configuration
st.set_page_config(page_title="📊 LSU Datastore", layout="centered")


def apply_custom_css() -> None:
    """Apply custom CSS styles based on login status."""
    if st.session_state.get("logged_in", False):
        background_color = "#F5F6F5"
        main_background = "#FFFFFF"
        sidebar_background = "#E8ECEF"
        primary_color = "#0056D2"
        secondary_color = "#003087"
        text_color = "#333333"
        text_light_color = "#666666"
    else:
        background_color = "url('bck.jpg')"
        main_background = "rgba(255, 255, 255, 0.9)"
        sidebar_background = "#461D7C"
        primary_color = "#461D7C"
        secondary_color = "#FABD00"
        text_color = "#000000"
        text_light_color = "#461D7C"

    css = f"""
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
        p {{
            font-size: 16px !important;
            line-height: 1.6 !important;
            color: {text_light_color} !important;
            font-weight: bold !important;
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
            color: #FFFFFF !important;
            margin-bottom: 10px !important;
            font-weight: bold !important;
        }}
        .stSidebar a, .stSidebar .stSelectbox label {{
            color: {secondary_color} !important;
            text-decoration: underline !important;
            font-size: 14px !important;
        }}
        .stSidebar a:hover {{
            color: {secondary_color} !important;
            text-decoration: underline !important;
        }}
        .stSidebar p {{
            font-size: 16px !important;
            line-height: 1.6 !important;
            color: {secondary_color} !important;
            font-weight: bold !important;
        }}
        .stSidebar .stButton p {{
            font-size: 16px !important;
            line-height: 1.6 !important;
            color: {text_light_color} !important;
            font-weight: bold !important;
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
        /* CPU Usage Metrics */
        .stMetric * {{
        color: {text_color} !important;
        }}
        /* Images */
        .ras-image {{
            max-width: 100%;
            border: 2px solid {primary_color};
            border-radius: 8px;
        }}
        /* Logo Image */
        .logo-image {{
            max-width: 50%;
            display: block;
            margin: 0 auto;
            border: 2px solid {primary_color};
            border-radius: 8px;
        }}
        /* Buttons */
        .stButton>button, .stDownloadButton>button {{
            background-color: {secondary_color};
            color: #FFFFFF;
            border-radius: 5px;
            padding: 8px 16px;
            font-weight: bold;
            border: none;
            transition: background-color 0.3s;
        }}
        .stButton>button:hover, .stDownloadButton>button:hover {{
            background-color: {secondary_color};
        }}
        section[data-testid="stSidebar"] .stButton>button {{
            background-color: {secondary_color} !important;
            opacity: 1 !important;
            visibility: visible !important;
            display: block !important;
            margin-bottom: 10px !important;
        }}
        section[data-testid="stSidebar"] .stButton>button:hover {{
            background-color: {secondary_color} !important;
            opacity: 1 !important;
            visibility: visible !important;
        }}
        .filter-container {{
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }}
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
            0% {{ box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3); }}
            50% {{ box-shadow: 0 2px 15px rgba(0, 0, 0, 0.5); }}
            100% {{ box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3); }}
        }}
        .terminal-log {{
            background-color: #000000;
            color: #FFFFFF;
            font-family: 'Courier New', Courier, monospace;
            font-size: 14px;
            padding: 15px;
            border-radius: 5px;
            height: 300px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
            border: 1px solid #333;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def initialize_session_state() -> None:
    """Initialize Streamlit session state variables."""
    defaults = {
        "logged_in": False,
        "username": None,
        "show_lsu_datastore": False,
        "page": "Home",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_sidebar() -> None:
    """Render the sidebar with navigation links and user authentication controls.

    Displays navigation options for different pages and a login/logout panel.
    Updates session state based on user actions.

    Raises:
        KeyError: If required secrets (USERNAME, PASSWORD) are missing.
    """
    with st.sidebar:
        st.header("DATABASE-RELATED LINKS")
        st.markdown("[GitHub Page](https://github.com/CSC-3380-Spring-2025/Team-34)")

        st.header("NAVIGATION")
        pages: List[str] = [
            "Home",
            "Data Page",
            "🔍 Search Data",
            "📊 Visualize Data",
            "📤 Share Data",
            "📥 Download Data",
        ]
        page: str = st.selectbox(
            "Navigate to:",
            pages,
            index=pages.index(st.session_state.page),
            key="page_select",
        )

        if page != st.session_state.page:
            st.session_state.page = page
            st.rerun()

        if st.session_state.logged_in:
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

        st.header("USER LOGIN")
        username: str = st.text_input("Username", key="login_username")
        password: str = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            with st.spinner("Logging in..."):
                time.sleep(3)
            try:
                toml_username: str = get_secret("USERNAME", "admin")
                toml_password: str = get_secret("PASSWORD", "NewSecurePassword123")
            except KeyError as e:
                st.error(f"Missing secret: {e}. Ensure USERNAME and PASSWORD are defined.")
                logger.error(f"Login failed: Missing secret {e}")
            else:
                auth_success: bool = authenticate_user(username, password) or (
                    username == toml_username and password == toml_password
                )
                if auth_success:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.show_lsu_datastore = (
                        username == toml_username and password == toml_password
                    )
                    st.success(f"Logged in as {username}!")
                    logger.info(f"User {username} logged in")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
                    logger.warning(f"Failed login attempt for username: {username}")
                    st.rerun()

        if st.session_state.logged_in:
            if st.button("Logout"):
                with st.spinner("Logging out..."):
                    time.sleep(3)
                logger.info(f"User {st.session_state.username} logged out")
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.show_lsu_datastore = False
                #Temporarily disable performance metrics to allow page to flush
                if st.session_state.page=="Home":
                    st.session_state.dont_perf = True
                st.rerun()


def main() -> None:
    """Render the main Streamlit application.

    Displays a demo badge and delegates rendering to page-specific functions based
    on the selected page in session state.
    """
    st.markdown(
        """
        <div class="demo-info">
            <span class="demo-text">Demo 1.4.6</span>
            <span class="live-demo-badge"><i class="fas fa-rocket"></i> Live Demo</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_sidebar()
    page: str = st.session_state.page
    if page == "Data Page":
        render_data_page()
    elif page == "🔍 Search Data":
        render_search_data_page()
    elif page == "📊 Visualize Data":
        render_visualize_data_page()
    elif page == "📤 Share Data":
        render_share_data_page()
    elif page == "📥 Download Data":
        render_download_data_page()
    else:
        render_home_page()


if __name__ == "__main__":
    initialize_session_state()
    apply_custom_css()
    main()
