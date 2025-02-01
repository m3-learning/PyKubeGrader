import os

import pandas as pd
import requests
from requests.auth import HTTPBasicAuth


def format_assignment_table(assignments):
    # Create DataFrame
    df = pd.DataFrame(assignments)

    # Replacements for normalization
    replacements = {
        "practicequiz": "practice quiz",
        "practice-quiz": "practice quiz",
        "attend": "attendance",
        "attendance": "attendance",
    }

    # Remove assignments of type 'test'
    remove_assignments = ["test"]

    # Apply replacements
    df["assignment_name"] = df["assignment_type"].replace(replacements)

    # Filter out specific assignment types
    df = df[~df["assignment_type"].isin(remove_assignments)]

    # Sort by week number and assignment name
    df = df.sort_values(by=["assignment_name", "week_number"]).reset_index(drop=True)

    return df


def get_student_grades(student_username):
    # Get env variables here, in the function, rather than globally
    api_base_url = os.getenv("DB_URL")
    student_user = os.getenv("user_name_student")
    student_pw = os.getenv("keys_student")

    if not api_base_url or not student_user or not student_pw:
        raise ValueError("Environment variables not set")

    params = {"username": student_username}
    res = requests.get(
        url=api_base_url.rstrip("/") + "/student-grades-testing",
        params=params,
        auth=HTTPBasicAuth(student_user, student_pw),
    )
    [assignments, sub] = res.json()

    assignments_df = format_assignment_table(assignments)

    return assignments_df, pd.DataFrame(sub)


def filter_assignments(df, max_week=None, exclude_types=None):
    """
    Remove assignments with week_number greater than max_week
    or with specific assignment types.

    :param df: DataFrame containing assignments.
    :param max_week: Maximum allowed week_number (int).
    :param exclude_types: A single assignment type or a list of assignment types to exclude.
    :return: Filtered DataFrame.
    """
    if max_week is not None:
        df = df[df["week_number"] <= max_week]

    if exclude_types is not None:
        # Ensure exclude_types is a list
        if not isinstance(exclude_types, (list, tuple, set)):
            exclude_types = [exclude_types]
        df = df[~df["assignment_type"].isin(exclude_types)]

    return df
