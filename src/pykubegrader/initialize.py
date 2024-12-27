import json
import os
from typing import Optional

import panel as pn
from IPython import get_ipython
import requests
from .telemetry import telemetry, update_responses, ensure_responses


def initialize_assignment(
    name: str,
    verbose: Optional[bool] = False,
    url: Optional[str] = "https://engr-131-api.eastus.cloudapp.azure.com/",
) -> None:
    ipython = get_ipython()
    if ipython is None:
        print("Setup unsuccessful. Are you in a Jupyter environment?")
        return

    try:
        ipython.events.register("pre_run_cell", telemetry)
    except TypeError as e:
        print(f"Failed to register telemetry: {e}")
        return

    jhub_user = os.getenv("JUPYTERHUB_USER")
    if jhub_user is None:
        print("Setup unsuccessful. Are you on JupyterHub?")
        return

    try:
        seed = hash(jhub_user) % 1000
        update_responses(key="seed", value=seed)
        update_responses(key="assignment", value=name)
        update_responses(key="jhub_user", value=jhub_user)

    except (TypeError, json.JSONDecodeError) as e:
        print(f"Failed to initialize assignment: {e}")
        return

    # extract responses
    responses = ensure_responses()

    # TODO: Add more checks here??
    assert isinstance(responses.get("seed"), int), "valid seed not found in responses"

    pn.extension(silent=True)

    if verbose:
        print("Assignment successfully initialized")
        print(f"Assignment: {name}")
        print(f"Username: {jhub_user}")

    # Checks connectivity to the API
    params = {"jhub_user": responses["jhub_user"]}
    response = requests.get(url, params=params)
    if verbose:
        print(f"status code: {response.status_code}")
        data = response.json()
        for k, v in data.items():
            print(f"{k}: {v}")

    print("Assignment successfully initialized")
    return responses
