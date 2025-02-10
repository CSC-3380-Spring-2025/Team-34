from fetch_jobs import fetch_jobs
from filter_jobs import filter_jobs, keywords
from save_jobs import save_jobs_to_csv

def main():
    """Main function to fetch, filter, and save job listings."""
    jobs = fetch_jobs()

    for category, keyword_list in keywords.items():
        filtered_jobs = filter_jobs(jobs, keyword_list)
        save_jobs_to_csv(filtered_jobs, category)

if __name__ == "__main__":
    main()
