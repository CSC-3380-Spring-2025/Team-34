import requests
from bs4 import BeautifulSoup

# Define arXiv RSS feeds for each category
ARXIV_FEEDS = {
    "Software_Engineering": "http://export.arxiv.org/rss/cs.SE",
    "Data_Science": "http://export.arxiv.org/rss/cs.LG",
    "Cloud_Computing": "http://export.arxiv.org/rss/cs.DC",
}

def fetch_research(category):
    """Fetch research papers from arXiv RSS feed."""
    url = ARXIV_FEEDS.get(category)
    if not url:
        print(f"❌ No RSS feed found for {category}")
        return []

    response = requests.get(url)
    if response.status_code != 200:
        print(f"❌ Error fetching research for {category}")
        return []

    soup = BeautifulSoup(response.content, "xml")
    papers = []

    for item in soup.find_all("item"):
        papers.append({
            "title": item.title.text,
            "summary": item.description.text,
            "link": item.link.text,
            "published": item.pubDate.text
        })

    return papers
