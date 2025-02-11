import requests

# Your NewsAPI key
NEWS_API_KEY = "pub_68861ffac957477623fce703ef66055932c8a"
BASE_URL = "https://newsdata.io/api/1/news"

# Mapping majors to news categories
CATEGORIES = {
    "Software_Engineering": "technology",
    "Data_Science": "science",
    "Cloud_Computing": "technology"
}

def fetch_courses(category):
    """Fetch tech news articles based on category from NewsAPI."""
    params = {
        "apikey": NEWS_API_KEY,
        "q": CATEGORIES.get(category, "technology"),
        "language": "en",
        "country": "us"
    }

    response = requests.get(BASE_URL, params=params)

    # Debugging output
    print(f"🔍 DEBUG: Response status: {response.status_code}")
    if response.status_code != 200:
        print(f"❌ Error fetching news for {category}: {response.status_code}")
        return []

    news_data = response.json().get("results", [])
    return [
        {
            "title": article.get("title", "No Title"),
            "description": article.get("description", "No Description"),
            "url": article.get("link", ""),
            "published": article.get("pubDate", "No Date")
        }
        for article in news_data
    ]
