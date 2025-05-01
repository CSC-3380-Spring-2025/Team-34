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
LINKED_JOBS_API = "linkedin-jobs-search.p.rapidapi.com"
UDEMY_API = "udemy-api2.p.rapidapi.com"
CORE_API_KEY = "eXSfGz97ZsArORei8W6ov2EDyT0alhupm"
RAPIDAPI_KEY = "bff529ced6mshe878b4a3ba0937fp18edbcjsn98c41db5431e"

MAJORS = ["software engineering", "cloud computing", "data science"]

def fetch_jobs(major):
    #return pd.DataFrame()
    #USE THIS IF NOT TESTING THIS FEATURE TO SAVE API CALLS
    try:
        url = "https://linkedin-jobs-search.p.rapidapi.com/"
        payload = {
            "search_terms": major,
            "location": "United States",
            "page": "1"
        }
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": LINKED_JOBS_API,
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)

        jobs=response.json()
        job_data = [{
            "title": job.get("job_title", ""),
            "company": job.get("company_name", ""),
            "location": job.get("job_location", ""),
            "url": job.get("job_url", ""),
            "posted_date": job.get("posted_date", "")
        } for job in jobs] if jobs else []
        return pd.DataFrame(job_data)
    except Exception as e:
        print(f"Error fetching jobs for {major}: {e}")
        return pd.DataFrame()

def fetch_courses(major):
    #return pd.Dataframe()
    #USE THIS IF NOT TESTING THIS FEATURE TO SAVE API CALLS
    match(major):
        case "cybersecurity":
            category="network_and_security"
        case "cloud computing":
            category="web_development"
        case _:
            category=major.lower().replace(' ', '_')
    try:
        url=f"https://udemy-api2.p.rapidapi.com/v1/udemy/category/{category}"
        payload = {
            "page": 1,
            "page_size": 10,
            "ratings": "",
            "instructional_level": [],
            "lang": [],
            "price": [],
            "duration": [],
            "subtitles_lang": [],
            "sort": "popularity",
            "features": [],
            "locale": "en_US",
            "extract_pricing": True
        }
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": UDEMY_API,
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)
        data=response.json()
        courses = data["data"]["courses"]
        course_data = [{
            "title": course.get("title", ""),
            "instructor": ", ".join([instr.get("display_name", "") for instr in course.get("instructors", [])]),
            "price": course["purchase"]["price"].get("price_string"),
            "url": "https://www.udemy.com" + course.get("url", ""),
            "last_updated_date": course.get("last_update_date", "")
        } for course in courses] if courses else []
        return pd.DataFrame(course_data)
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
    dataframe.replace('', "emptyvalue", inplace=True)
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
