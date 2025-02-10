import requests

def fetch_jobs():
    """Fetch job postings from Arbeitnow API."""
    url = 'https://www.arbeitnow.com/api/job-board-api'
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json().get('data', [])
    else:
        print(f"Error fetching data: {response.status_code}")
        return []
