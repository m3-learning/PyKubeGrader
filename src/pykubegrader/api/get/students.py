from pykubegrader._utils import api_base_url


import requests
from requests.auth import HTTPBasicAuth


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
