def filter_research(papers, keywords):
    """Filter research papers based on relevant keywords."""
    return [paper for paper in papers if any(keyword.lower() in paper['title'].lower() for keyword in keywords)]

# Define research keywords for filtering
research_keywords = {
    "Software_Engineering": ["Software", "Programming", "Algorithm", "Development"],
    "Data_Science": ["Data Science", "Machine Learning", "AI", "Deep Learning"],
    "Cloud_Computing": ["Cloud", "AWS", "Azure", "GCP", "Distributed Systems"]
}
