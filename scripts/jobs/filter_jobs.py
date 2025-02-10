def filter_jobs(jobs, keywords):
    """Filter job listings based on relevant keywords."""
    return [job for job in jobs if any(keyword.lower() in job['title'].lower() for keyword in keywords)]

# Example usage:
keywords = {
    "Software_Engineering": ["Software Engineer", "Backend", "Frontend", "Developer"],
    "Data_Science": ["Data Scientist", "Machine Learning", "AI Engineer"],
    "Cloud_Computing": ["Cloud Engineer", "AWS", "Azure", "GCP"]
}
