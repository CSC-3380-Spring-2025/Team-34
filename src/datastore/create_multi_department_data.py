"""Multi-department data collection module for Team-34 project.

Collects course data from LSU web links, processes it into CSV or Parquet files,
and provides default data for the LSU Datastore Dashboard.
"""

from typing import List

import parse_courses as parse_courses


def collect_multi_department_records(links: List[str]) -> List[dict[str, str]]:
    """Collect course data from multiple LSU web links.

    Args:
        links (List[str]): List of URLs to scrape for course data.

    Returns:
        List[dict[str, str]]: List of dictionaries containing course data.

    Raises:
        ValueError: If the links list is empty.
    """
    if not links:
        raise ValueError("No links provided for data collection")
    full_data: List[dict[str, str]] = []
    for link in links:
        try:
            full_data.extend(parse_courses.parse_course_page(link))
        except Exception as e:
            print(f"Error parsing link {link}: {e}")
    return full_data


def save_multi_department_csv(links: List[str]) -> None:
    """Save multi-department course data to a CSV file.

    Args:
        links (List[str]): List of URLs to scrape for course data.
    """
    parse_courses.create_csv(
        collect_multi_department_records(links),
        'multi_department_data',
    )


def save_multi_department_parquet(links: List[str]) -> None:
    """Save multi-department course data to a Parquet file.

    Args:
        links (List[str]): List of URLs to scrape for course data.
    """
    parse_courses.create_parquet(
        collect_multi_department_records(links),
        'multi_department_data',
    )


def collect_default_data() -> List[dict[str, str]]:
    """Collect default course data from predefined LSU web links.

    Returns:
        List[dict[str, str]]: List of dictionaries containing default course data.
    """
    links : List[str]= [
        'https://appl101.lsu.edu/booklet2.nsf/All/67FD57ECBF3676C486258BAC002C42AB?OpenDocument',
        'https://appl101.lsu.edu/booklet2.nsf/All/2719C3AEB8F7AE3986258BAC002C42D6?OpenDocument',
        'https://appl101.lsu.edu/booklet2.nsf/All/D61BDEBE0037080E86258BAC002C42B1?OpenDocument',
        'https://appl101.lsu.edu/booklet2.nsf/All/2C01DE7970FAE7E386258BAC002C42CA?OpenDocument',
    ]
    return collect_multi_department_records(links)
