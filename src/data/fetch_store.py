import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


import requests
import pandas as pd
from datetime import datetime
import sqlite3
import time
import schedule
from dotenv import load_dotenv
from src.datastore.database import save_csv_data, init_db


# Rest of the script remains the same...


# Load environment variables (for API keys)
load_dotenv()


# API keys (store these in a .env file for security)
GITHUB_JOBS_API = "https://jobs.github.com/positions.json"
COURSERA_API_KEY = os.getenv("COURSERA_API_KEY")
RESEARCH_API_KEY = os.getenv("RESEARCH_API_KEY")


# Base directory for the project (src)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CSV_DIR = os.path.join(BASE_DIR, "csv_data")
DB_NAME = os.path.join(BASE_DIR, "datastore", "datastore.db")


# Create csv_data directory if it doesn't exist (optional, for local storage)
if not os.path.exists(CSV_DIR):
   os.makedirs(CSV_DIR)


# Majors to fetch data for
MAJORS = ["software engineering", "cloud computing", "data science"]


def fetch_jobs(major):
   """Fetch job listings for a given major using the GitHub Jobs API."""
   try:
       params = {"description": major, "full_time": True}
       response = requests.get(GITHUB_JOBS_API, params=params)
       response.raise_for_status()
       jobs = response.json()


       if not jobs:
           print(f"No job listings found for {major}")
           return pd.DataFrame()


       # Normalize data into a DataFrame
       job_data = []
       for job in jobs:
           job_entry = {
               "title": job.get("title", ""),
               "company": job.get("company", ""),
               "location": job.get("location", ""),
               "description": job.get("description", ""),
               "url": job.get("url", ""),
               "posted_date": job.get("created_at", "")
           }
           job_data.append(job_entry)
       return pd.DataFrame(job_data)


   except requests.RequestException as e:
       print(f"Error fetching jobs for {major}: {e}")
       return pd.DataFrame()


def fetch_courses(major):
   """Fetch courses for a given major (using a placeholder API; replace with real API)."""
   try:
       # Placeholder: Replace with actual API (e.g., Coursera, Udemy)
       course_data = [
           {"title": f"{major.capitalize()} Basics", "platform": "Coursera", "duration": "4 weeks", "url": "https://example.com"},
           {"title": f"Advanced {major.capitalize()}", "platform": "Udemy", "duration": "6 weeks", "url": "https://example.com"}
       ]
       return pd.DataFrame(course_data)


   except Exception as e:
       print(f"Error fetching courses for {major}: {e}")
       return pd.DataFrame()


def fetch_research(major):
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


def save_to_csv_and_db(dataframe, filename, category, major, user_id=1):
   """Save DataFrame to CSV and store in database."""
   if dataframe.empty:
       print(f"No data to save for {category} - {major}")
       return


   # Save to CSV locally (optional, for reference or debugging)
   csv_path = os.path.join(CSV_DIR, filename)
   dataframe.to_csv(csv_path, index=False)
   print(f"Saved {filename} to {csv_path}")


   # Store in database
   with open(csv_path, "rb") as f:
       file_content = f.read()
       file_size = len(file_content)
       file_format = "csv"
       save_csv_data(filename, file_content, file_size, file_format, user_id)
   print(f"Stored {filename} in database at {DB_NAME}")


def fetch_and_store_data():
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


def schedule_daily_fetch():
   """Schedule the data fetch to run daily at a specific time (e.g., 8:00 AM)."""
   schedule.every().day.at("08:00").do(fetch_and_store_data)
   print("Scheduled daily fetch at 8:00 AM...")


   while True:
       schedule.run_pending()
       time.sleep(60)  # Check every minute


if __name__ == "__main__":
   # Initialize the database (if not already initialized)
   init_db()


   # Run the fetch once immediately (for testing)
   fetch_and_store_data()


   # Uncomment the line below to enable daily scheduling
   # schedule_daily_fetch()
