import os

import panel as pn
import requests
from requests.auth import HTTPBasicAuth

from ..utils import api_base_url

# Dummy credentials for HTTP Basic Auth
AUTH = HTTPBasicAuth("user", "password")

# Panel configuration
pn.extension()


def get_jhub_user():
    """
    Fetches the JupyterHub user from the environment.
    """
    jhub_user = os.getenv("JUPYTERHUB_USER")
    if jhub_user is None:
        raise ValueError("JupyterHub user not found")
    return jhub_user


def get_students():
    # Make the request
    response = requests.get(
        f"{api_base_url}students",
        auth=HTTPBasicAuth("user", "pass"),  # Basic Auth
        params={"requester": get_jhub_user()},  # Query parameter
    )

    # Print response
    if response.status_code == 200:
        return [student["email"].split("@")[0] for student in response.json()]
    else:
        print(f"Error {response.status_code}: {response.text}")


def get_assignments():
    # Make the request
    response = requests.get(
        f"{api_base_url}assignments",
        auth=HTTPBasicAuth("user", "pass"),  # Basic Auth
        params={"requester": get_jhub_user()},  # Query parameter
    )

    # Print response
    if response.status_code == 200:
        return [assignment["title"] for assignment in response.json()]
    else:
        print(f"Error {response.status_code}: {response.text}")
