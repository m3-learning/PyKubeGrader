import os

import requests


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
    auth = ("user", "password")

    response = requests.post(url, json=payload, auth=auth)

    # Print response
    print(f"Status code: {response.status_code}")

    try:
        print(f"Response: {response.json()}")
    except ValueError:
        print(f"Response: {response.text}")
