# import the password and user from the build folder
try:
    from pykubegrader.build.passwords import password, user
except:  # noqa: E722
    print("Passwords not found, cannot access database")

import os
import requests
from requests.auth import HTTPBasicAuth
import socket

# Set the environment variables for the database
os.environ["JUPYTERHUB_USER"] = "jca92"
os.environ["TOKEN"] = "token"
os.environ["DB_URL"] = "https://engr-131-api.eastus.cloudapp.azure.com/"
os.environ["keys_student"] = "capture"
os.environ["user_name_student"] = "student"

api_base_url = os.getenv("DB_URL")
student_user = os.getenv("user_name_student")
student_pw = os.getenv("keys_student")


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
