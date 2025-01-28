import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
import os

api_base_url = os.getenv("DB_URL")
student_user = os.getenv("user_name_student")
student_pw = os.getenv("keys_student")

from_env = os.getenv("JUPYTERHUB_USER")
params = {"username": from_env}


# get submission information
res = requests.get(
    # url=api_base_url.rstrip("/") + "/student-grades-testing",
    url=api_base_url.rstrip("/") + "/my-grades-testing",
    params=params,
    # auth=HTTPBasicAuth("admin", "TrgpUuadm2PWtdgtC7Yt"),
    auth=HTTPBasicAuth(os.getenv("user_name_student"), os.getenv("keys_student")),
)
api_base_url = os.getenv("DB_URL")

# def get_all_students():
#     '''admin only'''
#     from ..build.passwords import password, user
#     res = requests.get(
#         url=api_base_url.rstrip("/") + "/get-all-submission-emails",
#         auth=HTTPBasicAuth(user(), password()),
#     )

#     return res.json()


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
    params = {"username": student_username}
    res = requests.get(
        url=api_base_url.rstrip("/") + "/student-grades-testing",
        params=params,
        auth=HTTPBasicAuth( os.getenv("user_name_student"), os.getenv("keys_student")),
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
