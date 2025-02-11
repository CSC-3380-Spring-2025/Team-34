import requests
from bs4 import BeautifulSoup

def fetch_courses():
    """Fetch free online courses from Class Central's RSS feed."""
    url = 'https://www.classcentral.com/feed'
    response = requests.get(url)

    if response.status_code != 200:
        print(f"❌ Error fetching courses: {response.status_code}")
        return []

    soup = BeautifulSoup(response.content, 'xml')
    courses = []

    for item in soup.find_all('item'):
        courses.append({
            'title': item.title.text,
            'link': item.link.text,
            'description': item.description.text,
            'pubDate': item.pubDate.text
        })

    return courses
