def filter_courses(courses, keywords):
    """Filter courses based on relevant keywords."""
    return [course for course in courses if any(keyword.lower() in course['title'].lower() for keyword in keywords)]

# Define course keywords for filtering
course_keywords = {
    "Software_Engineering": ["Software", "Programming", "Development", "Engineering"],
    "Data_Science": ["Data Science", "Machine Learning", "AI", "Analytics"],
    "Cloud_Computing": ["Cloud", "AWS", "Azure", "GCP", "Cloud Computing"]
}
