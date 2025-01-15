import os

import requests
from requests.auth import HTTPBasicAuth


def build_token_payload(token: str, duration: int) -> dict:
    jhub_user = os.getenv("JUPYTERHUB_USER")
    if jhub_user is None:
        raise ValueError("JupyterHub user not found")

    return {
        "value": token,
        "duration": duration,
        "requester": jhub_user,
    }


def add_token(token: str, duration: int = 20) -> None:
    """
    Sends a POST request to mint a token
    """

    url = "https://engr-131-api.eastus.cloudapp.azure.com/tokens"

    payload = build_token_payload(token=token, duration=duration)

    # Dummy credentials for HTTP Basic Auth
    auth = HTTPBasicAuth("user", "password")

    # Add a custom header, for potential use in authorization
    headers = {"x-jhub-user": payload["requester"]}

    response = requests.post(url=url, json=payload, headers=headers, auth=auth)

    # Print response
    print(f"Status code: {response.status_code}")

    try:
        print(f"Response: {response.json()}")
    except ValueError:
        print(f"Response: {response.text}")
