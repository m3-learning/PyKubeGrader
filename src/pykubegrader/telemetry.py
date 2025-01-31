import base64
import datetime
import gzip
import json
import logging
import os
import socket
from typing import Any, Optional

import nacl.public
import pandas as pd
import requests
from dateutil import parser
from IPython.core.interactiveshell import ExecutionInfo
from requests import Response
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException

from .graders.late_assignments import calculate_late_submission
from .utils import api_base_url, student_pw, student_user

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

#
# Local functions
#


def encrypt_to_b64(message: str) -> str:
    with open(".server_public_key.bin", "rb") as f:
        server_pub_key_bytes = f.read()
    server_pub_key = nacl.public.PublicKey(server_pub_key_bytes)

    with open(".client_private_key.bin", "rb") as f:
        client_private_key_bytes = f.read()
    client_priv_key = nacl.public.PrivateKey(client_private_key_bytes)

    box = nacl.public.Box(client_priv_key, server_pub_key)
    encrypted = box.encrypt(message.encode())
    encrypted_b64 = base64.b64encode(encrypted).decode("utf-8")

    return encrypted_b64


def ensure_responses() -> dict[str, Any]:
    with open(".responses.json", "a") as _:
        pass

    responses = {}

    try:
        with open(".responses.json", "r") as f:
            responses = json.load(f)
    except json.JSONDecodeError:
        with open(".responses.json", "w") as f:
            json.dump(responses, f)

    return responses


def log_encrypted(logger: logging.Logger, message: str) -> None:
    """
    Logs an encrypted version of the given message using the provided logger.

    Args:
        logger (object): The logger object used to log the encrypted message.
        message (str): The message to be encrypted and logged.

    Returns:
        None
    """
    encrypted_b64 = encrypt_to_b64(message)
    logger.info(f"Encrypted Output: {encrypted_b64}")


def log_variable(assignment_name, value, info_type) -> None:
    timestamp = datetime.datetime.now(datetime.UTC).isoformat(
        sep=" ", timespec="seconds"
    )
    message = f"{assignment_name}, {info_type}, {value}, {timestamp}"
    log_encrypted(logger_reduced, message)


def telemetry(info: ExecutionInfo) -> None:
    cell_content = info.raw_cell
    log_encrypted(logger_code, f"code run: {cell_content}")


def update_responses(key: str, value) -> dict:
    data = ensure_responses()
    data[key] = value

    temp_path = ".responses.tmp"
    orig_path = ".responses.json"

    try:
        with open(temp_path, "w") as f:
            json.dump(data, f)

        os.replace(temp_path, orig_path)
    except (TypeError, json.JSONDecodeError) as e:
        print(f"Failed to update responses: {e}")

        if os.path.exists(temp_path):
            os.remove(temp_path)

        raise

    return data


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


# #
# # Qiao's work on grades
#


def get_assignments_submissions():
    if not student_user or not student_pw or not api_base_url:
        raise ValueError("Necessary environment variables not set")
    from_hostname = socket.gethostname().removeprefix("jupyter-")
    from_env = os.getenv("JUPYTERHUB_USER")
    if from_hostname != from_env:
        raise ValueError("Problem with JupyterHub username")

    params = {"username": from_env}
    # get submission information
    res = requests.get(
        url=api_base_url.rstrip("/") + "/my-grades-testing",
        params=params,
        auth=HTTPBasicAuth(student_user, student_pw),
    )
    return res.json()


def setup_grades_df(assignments):
    assignment_types = list(set([a["assignment_type"] for a in assignments]))

    inds = [f"week{i + 1}" for i in range(11)] + ["Running Avg"]
    restruct_grades = {k: [0 for i in range(len(inds))] for k in assignment_types}
    restruct_grades["inds"] = inds
    new_weekly_grades = pd.DataFrame(restruct_grades)
    new_weekly_grades.set_index("inds", inplace=True)
    return new_weekly_grades


def fill_grades_df(new_weekly_grades, assignments, student_subs):
    for assignment in assignments:
        # get the assignment from all submissions
        subs = [
            sub
            for sub in student_subs
            if sub["assignment_type"] == assignment["assignment_type"]
            and sub["week_number"] == assignment["week_number"]
        ]
        if len(subs) == 0:
            # print(assignment['title'], 0, assignment['max_score'])
            continue
        elif len(subs) == 1:
            grade = subs[0]["raw_score"] / assignment["max_score"]
            # print(assignment['title'], sub['raw_score'], assignment['max_score'])
        else:
            # get due date from assignment
            due_date = parser.parse(assignment["due_date"])
            grades = []
            for sub in subs:
                entry_date = parser.parse(sub["timestamp"])
                if entry_date <= due_date:
                    grades.append(sub["raw_score"])
                else:
                    grades.append(
                        calculate_late_submission(
                            due_date.strftime("%Y-%m-%d %H:%M:%S"),
                            entry_date.strftime("%Y-%m-%d %H:%M:%S"),
                        )
                    )
            # print(assignment['title'], grades, assignment['max_score'])
            grade = max(grades) / assignment["max_score"]

        # fill out new df with max
        new_weekly_grades.loc[
            f"week{assignment['week_number']}", assignment["assignment_type"]
        ] = grade

        # Merge different names
        new_weekly_grades["attend"] = new_weekly_grades[["attend", "attendance"]].max(
            axis=1
        )
        new_weekly_grades["practicequiz"] = new_weekly_grades[
            ["practicequiz", "practice-quiz"]
        ].max(axis=1)
        new_weekly_grades.drop(
            ["attendance", "practice-quiz", "test"],
            axis=1,
            inplace=True,
            errors="ignore",
        )

        return new_weekly_grades


def get_current_week(start_date):
    # Calculate the current week (1-based indexing)
    start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    today = datetime.datetime.now()
    days_since_start = (today - start_date).days
    return days_since_start // 7 + 1


# This function currently has many undefined variables and other problems!
def get_my_grades_testing(start_date="2025-01-06"):
    """takes in json.
    reshapes columns into reading, lecture, practicequiz, quiz, lab, attendance, homework, exam, final.
    fills in 0 for missing assignments
    calculate running average of each category"""

    # set up new df format
    weights = {
        "homework": 0.15,
        "lab": 0.15,
        "lecture": 0.15,
        "quiz": 0.15,
        "readings": 0.15,
        # 'midterm':0.15, 'final':0.2
        "labattendance": 0.05,
        "practicequiz": 0.05,
    }

    assignments, student_subs = get_assignments_submissions()

    new_grades_df = setup_grades_df(assignments)

    new_weekly_grades = fill_grades_df(new_grades_df, assignments, student_subs)

    current_week = get_current_week(start_date)

    # Get average until current week
    new_weekly_grades.iloc[-1] = new_weekly_grades.iloc[: current_week - 1].mean()

    # make new dataframe with the midterm, final, and running average
    max_key_length = max(len(k) for k in weights.keys())
    total = 0
    for k, v in weights.items():
        grade = new_weekly_grades.get(k, pd.Series([0])).iloc[-1]
        total += grade * v
        print(f"{k:<{max_key_length}}:\t {grade:.2f}")
    print(f"\nTotal: {total}")  # exclude midterm and final

    return new_weekly_grades  # get rid of test and running avg columns
