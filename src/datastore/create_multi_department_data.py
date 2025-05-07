"""Multi-department data collection module for the LSU Datastore Dashboard.

This module collects course data from LSU web links, processes it into CSV or
Parquet files, and provides default data for the Team-34 project. It is used by
the data-fetching script to populate the dashboard's database. Generated files are
tracked by Git Large File Storage (LFS) per .gitattributes. Errors are logged to
LOG_DIR/LOG_FILE.
"""

from typing import List

import parse_courses

from src.utils import logger


def collect_multi_department_records(links: List[str]) -> List[dict[str, str]]:
    """Collect course data from multiple LSU web links.

    Args:
        links: List of URLs to scrape for course data.

    Returns:
        List of dictionaries containing course data with keys such as course code,
        title, and department.

    Raises:
        ValueError: If the links list is empty.
        requests.RequestException: If a web request fails during scraping.
    """
    if not links:
        raise ValueError("No links provided for data collection")

    full_data: List[dict[str, str]] = []
    for link in links:
        try:
            full_data.extend(parse_courses.parse_course_page(link))
        except requests.RequestException as e:
            logger.error(
                "Course Data Collection Failed",
                extra={
                    "username": "System",
                    "action": "collect_course_data",
                    "details": f"Error parsing link {link}: {e}",
                },
            )
    return full_data


def collect_default_data() -> List[dict[str, str]]:
    """Collect default course data from predefined LSU web links.

    Returns:
        List of dictionaries containing default course data with keys such as
        course code, title, and department.

    Raises:
        ValueError: If no links are available for data collection.
        requests.RequestException: If a web request fails during scraping.
    """
    links: List[str] = [
        "https://appl101.lsu.edu/booklet2.nsf/All/67FD57ECBF3676C486258BAC002C42AB?OpenDocument",
        "https://appl101.lsu.edu/booklet2.nsf/All/2719C3AEB8F7AE3986258BAC002C42D6?OpenDocument",
        "https://appl101.lsu.edu/booklet2.nsf/All/D61BDEBE0037080E86258BAC002C42B1?OpenDocument",
        "https://appl101.lsu.edu/booklet2.nsf/All/2C01DE7970FAE7E386258BAC002C42CA?OpenDocument",
    ]
    return collect_multi_department_records(links)


def save_multi_department_csv(links: List[str]) -> None:
    """Save multi-department course data to a CSV file.

    Args:
        links: List of URLs to scrape for course data.

    Returns:
        None

    Raises:
        ValueError: If no links are provided or no data is collected.
        OSError: If the CSV file cannot be written.
        requests.RequestException: If a web request fails during scraping.
    """
    data: List[dict[str, str]] = collect_multi_department_records(links)
    if not data:
        raise ValueError("No data collected for CSV file")

    try:
        parse_courses.create_csv(data, "multi_department_data")
        logger.info(
            "CSV File Saved",
            extra={
                "username": "System",
                "action": "save_csv",
                "details": "Saved multi_department_data.csv",
            },
        )
    except OSError as e:
        logger.error(
            "CSV Save Failed",
            extra={
                "username": "System",
                "action": "save_csv",
                "details": f"Error saving multi_department_data.csv: {e}",
            },
        )
        raise


def save_multi_department_parquet(links: List[str]) -> None:
    """Save multi-department course data to a Parquet file.

    Args:
        links: List of URLs to scrape for course data.

    Returns:
        None

    Raises:
        ValueError: If no links are provided or no data is collected.
        OSError: If the Parquet file cannot be written.
        requests.RequestException: If a web request fails during scraping.
    """
    data: List[dict[str, str]] = collect_multi_department_records(links)
    if not data:
        raise ValueError("No data collected for Parquet file")

    try:
        parse_courses.create_parquet(data, "multi_department_data")
        logger.info(
            "Parquet File Saved",
            extra={
                "username": "System",
                "action": "save_parquet",
                "details": "Saved multi_department_data.parquet",
            },
        )
    except OSError as e:
        logger.error(
            "Parquet Save Failed",
            extra={
                "username": "System",
                "action": "save_parquet",
                "details": f"Error saving multi_department_data.parquet: {e}",
            },
        )
        raise
