import base64
import gzip
import logging
import os
import socket
from typing import Any, Optional

import pandas as pd
import requests
from IPython.core.interactiveshell import ExecutionInfo
from requests import Response
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException

from pykubegrader.telemetry.responses import ensure_responses 

from pykubegrader.telemetry.responses import log_encrypted
from pykubegrader.telemetry.responses import log_variable
from pykubegrader.utils import api_base_url, student_pw, student_user

#
# Logging setup
#

# Logger for cell execution
logger_code = logging.getLogger("code_logger")
logger_code.setLevel(logging.INFO)

file_handler_code = logging.FileHandler(".output_code.log")
file_handler_code.setLevel(logging.INFO)
logger_code.addHandler(file_handler_code)

# Logger for question scores etc.
logger_reduced = logging.getLogger("reduced_logger")
logger_reduced.setLevel(logging.INFO)

file_handler_reduced = logging.FileHandler(".output_reduced.log")
file_handler_reduced.setLevel(logging.INFO)
logger_reduced.addHandler(file_handler_reduced)

def telemetry(info: ExecutionInfo) -> None:
    cell_content = info.raw_cell
    log_encrypted(logger_code, f"code run: {cell_content}")


#
# API request functions
#


def score_question(term: str = "winter_2025") -> None:
    if not student_user or not student_pw or not api_base_url:
        raise ValueError("Necessary environment variables not set")

    url = api_base_url.rstrip("/") + "/live-scorer"

    responses = ensure_responses()

    payload: dict[str, Any] = {
        "student_email": f"{responses['jhub_user']}@drexel.edu",
        "term": term,
        "week": responses["week"],
        "assignment": responses["assignment_type"],
        "question": f"_{responses['assignment']}",
        "responses": responses,
    }

    try:
        res = requests.post(
            url, json=payload, auth=HTTPBasicAuth(student_user, student_pw)
        )
        res.raise_for_status()

        res_data: dict[str, tuple[float, float]] = res.json()

        for question, (points_earned, max_points) in res_data.items():
            log_variable(
                assignment_name=responses["assignment"],
                value=f"{points_earned}, {max_points}",
                info_type=question,
            )
    except RequestException as e:
        raise RuntimeError("Failed to access question-scoring endpoint") from e
    except ValueError as e:
        raise ValueError("Failed to parse question-scoring JSON response") from e
    except Exception as e:
        raise RuntimeError("Failed to score question") from e


def submit_question(
    student_email: str,
    term: str,
    assignment: str,
    question: str,
    responses: dict,
    score: dict,
) -> Response:
    if not student_user or not student_pw or not api_base_url:
        raise ValueError("Necessary environment variables not set")

    url = api_base_url.rstrip("/") + "/submit-question"

    payload = {
        "student_email": student_email,
        "term": term,
        "assignment": assignment,
        "question": question,
        "responses": responses,
        "score": score,
    }

    res = requests.post(url, json=payload, auth=HTTPBasicAuth(student_user, student_pw))

    return res


# TODO: Refine
def verify_server(jhub_user: Optional[str] = None) -> str:
    if not api_base_url:
        raise ValueError("Environment variable for API URL not set")
    params = {"jhub_user": jhub_user} if jhub_user else {}
    res = requests.get(api_base_url, params=params)
    message = f"status code: {res.status_code}"
    return message


# TODO: reformat into a nice table
def get_my_grades() -> pd.DataFrame:
    # get all submissions,
    # recalculate late penalty in new columns,
    # take max,
    # divide by total points
    if not student_user or not student_pw or not api_base_url:
        raise ValueError("Necessary environment variables not set")
    from_hostname = socket.gethostname().removeprefix("jupyter-")
    from_env = os.getenv("JUPYTERHUB_USER")
    if from_hostname != from_env:
        raise ValueError("Problem with JupyterHub username")

    params = {"username": from_env}
    res = requests.get(
        url=api_base_url.rstrip("/") + "/my-grades",
        params=params,
        auth=HTTPBasicAuth(student_user, student_pw),
    )
    res.raise_for_status()

    grades = res.json()

    # Convert JSON to DataFrame
    df = pd.json_normalize(grades)
    # Transpose the DataFrame to make it vertical
    vertical_df = df.transpose()

    # Sort by row titles (index)
    sorted_vertical_df = vertical_df.sort_index()

    return sorted_vertical_df

   
    

#
# Code execution log testing
#


def upload_execution_log() -> None:
    if not student_user or not student_pw or not api_base_url:
        raise ValueError("Necessary environment variables not set")

    responses = ensure_responses()
    student_email: str = responses["jhub_user"]
    assignment: str = responses["assignment"]
    if not student_email or not assignment:
        raise ValueError("Missing student email and/or assignment name")

    print(f"Student: {student_email}")
    print(f"Assignment: {assignment}")
    print("Uploading code execution log...")

    try:
        with open(".output_code.log", "rb") as f:
            log_bytes = f.read()
    except FileNotFoundError:
        raise FileNotFoundError("Code execution log not found")

    print(f"Uncompressed log size: {len(log_bytes)} bytes")

    compressed = gzip.compress(log_bytes)

    print(f"Compressed log size: {len(compressed)} bytes")

    encoded = base64.b64encode(compressed).decode("utf-8")

    payload = {
        "student_email": student_email,
        "assignment": assignment,
        "encrypted_content": encoded,
    }

    res = requests.post(
        url=api_base_url.rstrip("/") + "/execution-logs",
        json=payload,
        auth=HTTPBasicAuth(student_user, student_pw),
    )
    res.raise_for_status()

    print("Execution log uploaded successfully")


def get_all_students(user, password):
    """
    Fetches a list of all students from the API and returns their usernames.

    Args:
        user (str): The username for HTTP basic authentication.
        password (str): The password for HTTP basic authentication.

    Returns:
        list: A list of usernames extracted from the students' email addresses.

    Raises:
        requests.exceptions.HTTPError: If the HTTP request returned an unsuccessful status code.
    """
    if not api_base_url:
        raise ValueError("Necessary environment variables not set")

    res = requests.get(
        url=api_base_url.rstrip("/") + "/students",
        auth=HTTPBasicAuth(user, password),
    )
    res.raise_for_status()

    # Input: List of players
    return [student["email"].split("@")[0] for student in res.json()]


def get_assignments_submissions(params=None):
    """
    Fetches assignment submissions for a student from the grading API.
    This function retrieves the assignment submissions for a student by making a GET request to the grading API.
    It requires certain environment variables to be set and validates the JupyterHub username.
    Args:
        params (dict, optional): A dictionary of parameters to be sent in the query string. Defaults to None. If not provided, it will default to {"username": <JUPYTERHUB_USER>}.
    Raises:
        ValueError: If necessary environment variables (student_user, student_pw, api_base_url) are not set.
        ValueError: If there is a mismatch between the JupyterHub username from the hostname and the environment variable.
    Returns:
        dict: A dictionary containing the JSON response from the API with the assignment submissions.
    """

    if not student_user or not student_pw or not api_base_url:
        raise ValueError("Necessary environment variables not set")

    from_hostname = socket.gethostname().removeprefix("jupyter-")
    from_env = os.getenv("JUPYTERHUB_USER")

    if from_hostname != from_env:
        raise ValueError("Problem with JupyterHub username")

    if not params:
        params = {"username": from_env}

    # get submission information
    res = requests.get(
        url=api_base_url.rstrip("/") + "/my-grades-testing",
        params=params,
        auth=HTTPBasicAuth(student_user, student_pw),
    )

    return res.json()

