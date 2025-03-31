from pykubegrader.utils import api_base_url, student_pw, student_user


import requests
from requests.auth import HTTPBasicAuth


import os
import socket


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