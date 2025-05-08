"""Course parsing module for the LSU Datastore Dashboard.

This module parses course data from LSU web pages and saves it to CSV or Parquet
files for the Team-34 project. It is used by create_multi_department_data.py to
collect data for the dashboard's database. Generated files are tracked by Git Large
File Storage (LFS) per .gitattributes. Errors are logged to LOG_DIR/LOG_FILE.
"""

from typing import Dict, List

import pandas as pd
import requests

from src.utils import logger


def concatenate_strings(list_str: str, added_str: str, separator: str) -> str:
    """Concatenate two strings with a separator.

    Returns the added string if the initial string is empty, otherwise joins the
    strings with the separator.

    Args:
        list_str: The initial string (may be empty).
        added_str: The string to append.
        separator: The separator to use (e.g., ' + ', ' ').

    Returns:
        The concatenated string.
    """
    if list_str == "":
        return added_str
    return list_str + separator + added_str


def parse_data(course_page: str) -> List[Dict[str, str]]:
    """Parse course data from a web page text into a structured format.

    Args:
        course_page: Raw HTML text of the course page.

    Returns:
        List of dictionaries containing course data with keys: available_spots,
        capacity, prefix, course_number, type, section, title, credits, time, days,
        room, building, special_info, instructor, session, additional_meet_times,
        additional_meet_days, additional_notes.
    """
    lines: List[str] = course_page.split("\n")
    course_data: List[Dict[str, str]] = []
    session: str = "Normal"
    queued_notes: Dict[str, str] = {}
    i: int = 0
    while not lines[i].startswith("------------"):
        i += 1
    i += 1

    for line in lines[i:]:
        line = line.replace("&", "&")
        season_check: str = line[0:6].strip()
        if (
            line == ""
            or season_check == "Fall"
            or season_check.strip() == "Spring"
            or line[0:5].strip() == "</PRE"
        ):
            continue
        if line[5:7] == "**":
            course_data[-1]["additional_notes"] = concatenate_strings(
                course_data[-1]["additional_notes"], line[7:].strip(), " + "
            )
            continue
        if line[6:9] == "***":
            course_name: str = line[11:22].strip()
            note: str = line[32:].strip()
            if course_name in queued_notes:
                queued_notes[course_name] = concatenate_strings(
                    queued_notes[course_name], note, " "
                )
            else:
                queued_notes[course_name] = note
            continue
        if "SESSION  B" in line:
            session = "B"
            continue
        if "SESSION  C" in line:
            session = "C"
            continue

        current_course: Dict[str, str] = {
            "available_spots": line[0:5].strip(),
            "capacity": line[5:11].strip(),
            "prefix": line[11:16].strip(),
            "course_number": line[16:21].strip(),
            "type": line[21:27].strip(),
            "section": line[27:32].strip(),
            "title": line[32:55].strip(),
            "credits": line[55:60].strip(),
            "time": line[60:72].strip(),
            "days": line[72:79].strip(),
            "room": line[79:84].strip(),
            "building": line[84:100].strip(),
            "special_info": line[100:117].strip(),
            "instructor": line[117:].strip(),
            "session": session,
            "additional_meet_times": "",
            "additional_meet_days": "",
            "additional_notes": "",
        }

        if current_course["available_spots"] == "(F)":
            current_course["available_spots"] = "0"

        course_string: str = current_course["prefix"] + " " + current_course["course_number"]
        if course_string in queued_notes:
            current_course["additional_notes"] = concatenate_strings(
                course_data[-1]["additional_notes"],
                queued_notes.pop(course_string),
                " + ",
            )

        if current_course["course_number"] == "":
            if current_course["type"] == "LAB":
                course_data[-1]["type"] = "LECLAB"
                course_data[-1]["additional_meet_times"] = concatenate_strings(
                    course_data[-1]["additional_meet_times"],
                    current_course["time"],
                    " + ",
                )
                course_data[-1]["additional_meet_days"] = concatenate_strings(
                    course_data[-1]["additional_meet_days"],
                    current_course["days"],
                    " + ",
                )
            elif current_course["special_info"] != "":
                course_data[-1]["special_info"] = concatenate_strings(
                    course_data[-1]["special_info"],
                    current_course["special_info"],
                    " + ",
                )
        else:
            course_data.append(current_course)

    return course_data


def parse_course_page(url: str) -> List[Dict[str, str]]:
    """Fetch and parse course data from a given LSU web page URL.

    Args:
        url: URL of the course page to parse.

    Returns:
        List of dictionaries containing course data, or empty list if fetching fails.

    Raises:
        requests.RequestException: If the HTTP request fails.
    """
    try:
        response: requests.Response = requests.get(url)
        response.raise_for_status()
        return parse_data(response.text)
    except requests.RequestException as e:
        logger.error(
            "Course Page Fetch Failed",
            extra={
                "username": "System",
                "action": "parse_course_page",
                "details": f"Error fetching {url}: {e}",
            },
        )
        return []


def create_csv(data: List[Dict[str, str]], name: str) -> None:
    """Save course data to a CSV file.

    Args:
        data: List of course data dictionaries.
        name: Base name for the CSV file (without extension).

    Returns:
        None

    Raises:
        OSError: If the CSV file cannot be written.
    """
    try:
        df: pd.DataFrame = pd.DataFrame(data)
        df.to_csv(f"{name}.csv", index=False)
        logger.info(
            "CSV File Saved",
            extra={
                "username": "System",
                "action": "create_csv",
                "details": f"Saved {name}.csv",
            },
        )
    except OSError as e:
        logger.error(
            "CSV Save Failed",
            extra={
                "username": "System",
                "action": "create_csv",
                "details": f"Error saving {name}.csv: {e}",
            },
        )
        raise


def create_parquet(data: List[Dict[str, str]], name: str) -> None:
    """Save course data to a Parquet file.

    Args:
        data: List of course data dictionaries.
        name: Base name for the Parquet file (without extension).

    Returns:
        None

    Raises:
        OSError: If the Parquet file cannot be written.
    """
    try:
        df: pd.DataFrame = pd.DataFrame(data)
        df.to_parquet(f"{name}.parquet", engine="pyarrow", index=False)
        logger.info(
            "Parquet File Saved",
            extra={
                "username": "System",
                "action": "create_parquet",
                "details": f"Saved {name}.parquet",
            },
        )
    except OSError as e:
        logger.error(
            "Parquet Save Failed",
            extra={
                "username": "System",
                "action": "create_parquet",
                "details": f"Error saving {name}.parquet: {e}",
            },
        )
        raise


if __name__ == "__main__":
    create_csv(
        parse_course_page(
            "https://appl101.lsu.edu/booklet2.nsf/All/"
            "67FD57ECBF3676C486258BAC002C42AB?OpenDocument"
        ),
        "csc_courses",
    )
