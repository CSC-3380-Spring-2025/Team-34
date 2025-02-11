from fetch_research import fetch_research
from filter_research import filter_research, research_keywords
from save_research import save_research_to_csv

def main():
    """Main function to fetch, filter, and save research papers."""
    for category, keyword_list in research_keywords.items():
        papers = fetch_research(category)
        filtered_papers = filter_research(papers, keyword_list)
        save_research_to_csv(filtered_papers, category)

if __name__ == "__main__":
    main()
