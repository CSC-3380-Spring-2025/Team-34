import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from src.datastore.database import save_csv_data, init_db
import src.datastore.create_multi_department_data as lsudata
import schedule
import time

# Load environment variables
load_dotenv()

# API keys
LINKED_JOBS_API = "https://linkedin-data-api.p.rapidapi.com/get-jobs"
CORE_API_KEY = "XSfGz97ZsArORei8W6ov2EDyT0alhupm"
RAPIDAPI_KEY = "52b85dc6885msh339b181109c6d5p11beabjsnf61b2676da3"

MAJORS = ["software engineering", "cloud computing", "data science"]

def fetch_jobs(major):
    try:
        headers = {
            "x-rapidapi-host": "linkedin-data-api.p.rapidapi.com",
            "x-rapidapi-key": RAPIDAPI_KEY
        }
        params = {"description": major, "full_time": True}
        response = requests.get(LINKED_JOBS_API, headers=headers, params=params)
        response.raise_for_status()
        jobs = response.json()

        job_data = [{
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            "location": job.get("location", ""),
            "description": job.get("description", ""),
            "url": job.get("url", ""),
            "posted_date": job.get("created_at", "")
        } for job in jobs] if jobs else []
        return pd.DataFrame(job_data)
    except requests.RequestException as e:
        print(f"Error fetching jobs for {major}: {e}")
        return pd.DataFrame()

def fetch_courses(major):
    try:
        return pd.DataFrame([
            {"title": f"{major.capitalize()} Basics", "platform": "Coursera", "duration": "4 weeks", "url": "https://example.com"},
            {"title": f"Advanced {major.capitalize()}", "platform": "Udemy", "duration": "6 weeks", "url": "https://example.com"}
        ])
    except Exception as e:
        print(f"Error fetching courses for {major}: {e}")
        return pd.DataFrame()

def fetch_research(major):
    try:
        headers = {"Authorization": f"Bearer {CORE_API_KEY}"}
        params = {"q": major, "limit": 10}
        response = requests.get("https://api.core.ac.uk/v3/search/works", headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        research_data = [{
            "title": item.get("title", ""),
            "authors": ", ".join([author.get("name", "") for author in item.get("authors", [])]),
            "publication_date": item.get("publishedDate", ""),
            "url": item.get("doi", "")
        } for item in data.get("results", [])]
        return pd.DataFrame(research_data)
    except requests.RequestException as e:
        print(f"Error fetching research for {major}: {e}")
        return pd.DataFrame()

def fetch_lsu_courses(major):
    course_data = lsudata.collect_default_data()
    return pd.DataFrame(course_data)

def save_to_db_only(dataframe, filename, user_id=1):
    if dataframe.empty:
        print(f"No data to save for {filename}")
        return
    file_content = dataframe.to_csv(index=False).encode("utf-8")
    save_csv_data(filename, file_content, len(file_content), "csv", user_id)
    print(f"Stored {filename} in database")

def fetch_and_store_data():
    today = datetime.now().strftime("%Y-%m-%d")
    for major in MAJORS:
        print(f"Fetching data for {major} on {today}...")
        jobs_df = fetch_jobs(major)
        if not jobs_df.empty:
            save_to_db_only(jobs_df, f"jobs_{major.replace(' ', '_')}_{today}.csv")
        courses_df = fetch_courses(major)
        if not courses_df.empty:
            save_to_db_only(courses_df, f"courses_{major.replace(' ', '_')}_{today}.csv")
        research_df = fetch_research(major)
        if not research_df.empty:
            save_to_db_only(research_df, f"research_{major.replace(' ', '_')}_{today}.csv")
        lsu_df = fetch_lsu_courses(major)
        if not lsu_df.empty:
            save_to_db_only(lsu_df, f"lsu_{major.replace(' ', '_')}_{today}.csv")

def schedule_daily_fetch():
    schedule.every().day.at("08:00").do(fetch_and_store_data)
    print("Scheduled daily fetch at 8:00 AM...")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    init_db()
    fetch_and_store_data()
