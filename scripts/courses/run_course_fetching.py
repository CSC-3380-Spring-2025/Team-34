from fetch_courses import fetch_courses
from filter_courses import filter_courses, course_keywords
from save_courses import save_courses_to_csv

def main():
    """Main function to fetch, filter, and save courses."""
    courses = fetch_courses()

    for category, keyword_list in course_keywords.items():
        filtered_courses = filter_courses(courses, keyword_list)
        save_courses_to_csv(filtered_courses, category)

if __name__ == "__main__":
    main()
