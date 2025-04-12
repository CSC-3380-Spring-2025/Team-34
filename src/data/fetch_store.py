import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import requests
import pandas as pd
from datetime import datetime
import sqlite3
from dotenv import load_dotenv
from src.datastore.database import save_csv_data, init_db
import src.datastore.create_multi_department_data as lsudata

# Load environment variables
load_dotenv()

# API keys
LINKED_JOBS_API = "https://linkedin-data-api.p.rapidapi.com/get-jobs"
CORE_API_KEY = "XSfGz97ZsArORei8W6ov2EDyT0alhupm"
RAPIDAPI_KEY = "52b85dc6885msh339b181109c6d5p11beabjsnf61b2676da3"

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CSV_DIR = os.path.join(BASE_DIR, "csv_data")
DB_NAME = os.path.join(BASE_DIR, "datastore", "datastore.db")
if not os.path.exists(CSV_DIR):
    os.makedirs(CSV_DIR)

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
   """Fetch research papers for a given major (using a placeholder API; replace with real API)."""
   try:
       # Placeholder: Replace with actual API (e.g., arXiv, Google Scholar)
       research_data = [
           {"title": f"Latest Trends in {major.capitalize()}", "authors": "John Doe", "publication_date": "2025-01-01", "url": "https://example.com"},
           {"title": f"Future of {major.capitalize()}", "authors": "Jane Smith", "publication_date": "2025-02-01", "url": "https://example.com"}
       ]
       return pd.DataFrame(research_data)


   except Exception as e:
       print(f"Error fetching research for {major}: {e}")
       return pd.DataFrame()
def fetch_lsu_courses(major):
    course_data=lsudata.collect_default_data()
    return pd.DataFrame(course_data)

def save_to_csv_and_db(dataframe, filename, category, major, user_id=1):
    if dataframe.empty:
        print(f"No data to save for {category} - {major}")
        return
    csv_path = os.path.join(CSV_DIR, filename)
    dataframe.to_csv(csv_path, index=False)
    print(f"Saved {filename} to {csv_path}")
    with open(csv_path, "rb") as f:
        file_content = f.read()
        save_csv_data(filename, file_content, len(file_content), "csv", user_id)
    print(f"Stored {filename} in database at {DB_NAME}")

def fetch_and_store_data():
    today = datetime.now().strftime("%Y-%m-%d")
    for major in MAJORS:
        print(f"Fetching data for {major} on {today}...")
        jobs_df = fetch_jobs(major)
        if not jobs_df.empty:
            save_to_csv_and_db(jobs_df, f"jobs_{major.replace(' ', '_')}_{today}.csv", "jobs", major)
        courses_df = fetch_courses(major)
        if not courses_df.empty:
            save_to_csv_and_db(courses_df, f"courses_{major.replace(' ', '_')}_{today}.csv", "courses", major)
        research_df = fetch_research(major)
        if not research_df.empty:
            save_to_csv_and_db(research_df, f"research_{major.replace(' ', '_')}_{today}.csv", "research", major)
   """Fetch data for jobs, courses, and research, then save to CSV and database."""
   today = datetime.now().strftime("%Y-%m-%d")
   for major in MAJORS:
       print(f"Fetching data for {major} on {today}...")


       # Fetch and store jobs
       jobs_df = fetch_jobs(major)
       if not jobs_df.empty:
           jobs_filename = f"jobs_{major.replace(' ', '_')}_{today}.csv"
           save_to_csv_and_db(jobs_df, jobs_filename, "jobs", major)


       # Fetch and store courses
       courses_df = fetch_courses(major)
       if not courses_df.empty:
           courses_filename = f"courses_{major.replace(' ', '_')}_{today}.csv"
           save_to_csv_and_db(courses_df, courses_filename, "courses", major)

       # Fetch and store research
       research_df = fetch_research(major)
       if not research_df.empty:
           research_filename = f"research_{major.replace(' ', '_')}_{today}.csv"
           save_to_csv_and_db(research_df, research_filename, "research", major)

       # Fetch and store LSU course data
       lsu_df=fetch_lsu_courses(major)
       if not lsu_df.empty:
           lsu_filename = f"lsu_{major.replace(' ', '_')}_{today}.csv"
           save_to_csv_and_db(lsu_df, lsu_filename, "lsu", major)

def schedule_daily_fetch():
   """Schedule the data fetch to run daily at a specific time (e.g., 8:00 AM)."""
   schedule.every().day.at("08:00").do(fetch_and_store_data)
   print("Scheduled daily fetch at 8:00 AM...")


   while True:
       schedule.run_pending()
       time.sleep(60)  # Check every minute


if __name__ == "__main__":
    init_db()
    fetch_and_store_data()
