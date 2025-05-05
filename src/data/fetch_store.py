#!/usr/bin/env python3
"""Fetch and store job, course, research, and LSU course data for specified majors.

This module uses APIs (LinkedIn Jobs, Udemy, CORE) to fetch data, saves it as CSV
in a database, and schedules daily updates at 8:00 AM.
"""

import os
import sys
from datetime import datetime
from typing import List
from typing import Any
import pandas as pd
import requests
import schedule
import time
import streamlit as st
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.datastore.database import save_csv_to_database, init_db  # Updated from save_csv_data
import src.datastore.create_multi_department_data as lsudata

# Load environment variables
load_dotenv()

# API keys and constants
LINKED_JOBS_API : str = 'linkedin-jobs-search.p.rapidapi.com'
UDEMY_API : str = 'udemy-api2.p.rapidapi.com'
CORE_API_KEY : str = os.getenv("CORE_API_KEY")
#RAPIDAPI_KEY : str = os.getenv("RAPIDAPI_KEY", st.secrets.get("RAPIDAPI_KEY", ""))
RAPIDAPI_KEY : str = os.getenv("RAPIDAPI_KEY")

MAJORS : list[str] = ['software engineering', 'cloud computing', 'data science', 'cybersecurity']

def fetch_jobs_data(major: str) -> pd.DataFrame:
    """Fetch job listings for a given major from LinkedIn Jobs API.
    
    Args:
        major (str): The major to search for (e.g., 'software engineering').
    
    Returns:
        pd.DataFrame: DataFrame containing job data (title, company, location, url, posted_date).
    """
    # return pd.DataFrame()  # USE THIS IF NOT TESTING THIS FEATURE TO SAVE API CALLS
    try:
        url : str = 'https://linkedin-jobs-search.p.rapidapi.com/'
        payload : dict[str, str]= {
            'search_terms': major,
            'location': 'United States',
            'page': '1'
        }
        headers : dict[str, str] = {
            'x-rapidapi-key': RAPIDAPI_KEY,
            'x-rapidapi-host': LINKED_JOBS_API,
            'Content-Type': 'application/json'
        }

        response : str = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        jobs = response.json()
        job_data = [
            {
                'title': job.get('job_title', ''),
                'company': job.get('company_name', ''),
                'location': job.get('job_location', ''),
                'url': job.get('job_url', ''),
                'posted_date': job.get('posted_date', '')
            }
            for job in jobs
        ] if jobs else []
        return pd.DataFrame(job_data)
    except Exception as e:
        print(f'Error fetching jobs for {major}: {e}')
        return pd.DataFrame()

def fetch_courses_data(major: str) -> pd.DataFrame:
    """Fetch courses for a given major from Udemy API.
    
    Args:
        major (str): The major to search for (e.g., 'data science').
    
    Returns:
        pd.DataFrame: DataFrame containing course data (title, instructor, price, url, last_updated_date).
    """
    # return pd.DataFrame()  # USE THIS IF NOT TESTING THIS FEATURE TO SAVE API CALLS
    match major:
        case 'cybersecurity':
            category : str = 'network_and_security'
        case 'cloud computing':
            category : str = 'web_development'
        case _:
            category : str = major.lower().replace(' ', '_')
    try:
        url : str = f'https://udemy-api2.p.rapidapi.com/v1/udemy/category/{category}'
        payload : dict[str,Any] = {
            'page': 1,
            'page_size': 10,
            'ratings': '',
            'instructional_level': [],
            'lang': [],
            'price': [],
            'duration': [],
            'subtitles_lang': [],
            'sort': 'popularity',
            'features': [],
            'locale': 'en_US',
            'extract_pricing': True
        }
        headers : dict[str,str] = {
            'x-rapidapi-key': RAPIDAPI_KEY,
            'x-rapidapi-host': UDEMY_API,
            'Content-Type': 'application/json'
        }

        response : str = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        courses = data['data']['courses']
        course_data = [
            {
                'title': course.get('title', ''),
                'instructor': ', '.join([instr.get('display_name', '') for instr in course.get('instructors', [])]),
                'price': course['purchase']['price'].get('price_string'),
                'url': 'https://www.udemy.com' + course.get('url', ''),
                'last_updated_date': course.get('last_update_date', '')
            }
            for course in courses
        ] if courses else []
        return pd.DataFrame(course_data)
    except Exception as e:
        print(f'Error fetching courses for {major}: {e}')
        return pd.DataFrame()

def fetch_research_data(major: str) -> pd.DataFrame:
    """Fetch research papers for a given major from CORE API.
    
    Args:
        major (str): The major to search for (e.g., 'cybersecurity').
    
    Returns:
        pd.DataFrame: DataFrame containing research data (title, authors, publication_date, url).
    """
    try:
        headers : dict[str,str]= {'Authorization': f'Bearer {CORE_API_KEY}'}
        params : dict[str,str] = {'q': major, 'limit': 10}
        response : str = requests.get('https://api.core.ac.uk/v3/search/works', headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        research_data = [
            {
                'title': item.get('title', ''),
                'authors': ', '.join([author.get('name', '') for author in item.get('authors', [])]),
                'publication_date': item.get('publishedDate', ''),
                'url': item.get('doi', '')
            }
            for item in data.get('results', [])
        ]
        return pd.DataFrame(research_data)
    except requests.RequestException as e:
        print(f'Error fetching research for {major}: {e}')
        return pd.DataFrame()

def fetch_lsu_course_data() -> pd.DataFrame:
    """Fetch LSU course data from the local data module.
    
    Returns:
        pd.DataFrame: DataFrame containing LSU course data.
    """
    course_data : List[dict[str,str]] = lsudata.collect_default_data()
    return pd.DataFrame(course_data)

def save_to_database(dataframe: pd.DataFrame, filename: str, user_id: int = 1) -> None:
    """Save a DataFrame as CSV to the database.
    
    Args:
        dataframe (pd.DataFrame): DataFrame to save.
        filename (str): Name of the CSV file.
        user_id (int, optional): User ID for database storage. Defaults to 1.
    """
    if dataframe.empty:
        print(f'No data to save for {filename}')
        return
    dataframe.replace('', 'emptyvalue', inplace=True)
    file_content : bytes = dataframe.to_csv(index=False).encode('utf-8')
    save_csv_to_database(filename, file_content, len(file_content), 'csv', user_id)  # Updated from save_csv_data
    print(f'Stored {filename} in database')

def fetch_and_store_all_data() -> None:
    """Fetch and store job, course, research, and LSU data for all majors."""
    today : str = datetime.now().strftime('%Y-%m-%d')
    for major in MAJORS:
        print(f'Fetching data for {major} on {today}...')
        jobs_df : pd.DataFrame = fetch_jobs_data(major)
        if not jobs_df.empty:
            save_to_database(jobs_df, f'jobs_{major.replace(" ", "_")}_{today}.csv')
        courses_df : pd.DataFrame = fetch_courses_data(major)
        if not courses_df.empty:
            save_to_database(courses_df, f'courses_{major.replace(" ", "_")}_{today}.csv')
        research_df : pd.DataFrame = fetch_research_data(major)
        if not research_df.empty:
            save_to_database(research_df, f'research_{major.replace(" ", "_")}_{today}.csv')
    lsu_df : pd.DataFrame = fetch_lsu_course_data()
    if not lsu_df.empty:
        save_to_database(lsu_df, f'lsu_relevant_{today}.csv')

def schedule_daily_data_fetch() -> None:
    """Schedule daily data fetching at 8:00 AM."""
    schedule.every().day.at('08:00').do(fetch_and_store_all_data)
    print('Scheduled daily fetch at 8:00 AM...')
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    init_db()
    fetch_and_store_all_data()
