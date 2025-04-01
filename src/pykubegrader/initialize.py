import hashlib
import os
import shutil
from pathlib import Path
from typing import Optional

import panel as pn
import requests
from IPython.core.getipython import get_ipython

from pykubegrader.telemetry.responses import (
    ensure_responses,
    set_responses_json,
    log_variable,
)

from pykubegrader._telemetry import telemetry
from pykubegrader._utils import api_base_url


def initialize_assignment(
    name: str,
    week: Optional[str] = None,
    assignment_type: Optional[str] = None,
    verbose: Optional[bool] = False,
    assignment_points: Optional[float] = None,
    assignment_tag: Optional[str] = None,
) -> dict:
    """
    Initialize an assignment in a Jupyter environment.

    Args:
        name (str): The name of the assignment.
        url (str): The URL of the API server.
        verbose (bool): Whether to print detailed initialization information.

    Returns:
        dict: The responses dictionary after initialization.

    Raises:
        Exception: If the environment is unsupported or initialization fails.
    """

    assignment_tag = build_assignment_tag(week, assignment_type, assignment_tag)

    initialize_telemetry()

    jhub_user = get_jhub_user()

    try:
        responses = generate_user_seed(name, week, assignment_type, jhub_user)

        pn.extension(silent=True)

        # Check connection to API server
        check_api_connection()

        params = {"jhub_user": responses["jhub_user"]}

        response = requests.get(api_base_url, params=params)

        print_api_response(response, verbose=verbose)

    except Exception as e:
        raise Exception(f"Failed to initialize assignment: {e}")

    log_variable("total-points", f"{assignment_tag}, {name}", assignment_points)

    print("Assignment successfully initialized")
    print_assignment_info(name, jhub_user, verbose=verbose)

    return responses


def print_assignment_info(name, jhub_user, **kwargs):
    verbose = kwargs.get("verbose", False)
    if verbose:
        print(f"Assignment: {name}")
        print(f"Username: {jhub_user}")


def print_api_response(response, **kwargs):
    verbose = kwargs.get("verbose", False)

    if verbose:
        print(f"status code: {response.status_code}")
        data = response.json()
        for k, v in data.items():
            print(f"{k}: {v}")


def generate_user_seed(name, week, assignment_type, jhub_user):
    seed = username_to_seed(jhub_user) % 1000
    set_responses_json(key="seed", value=seed)
    set_responses_json(key="week", value=week)
    set_responses_json(key="assignment_type", value=assignment_type)

    set_responses_json(key="assignment", value=name)
    set_responses_json(key="jhub_user", value=jhub_user)

    # TODO: Check whether this is called correctly
    log_variable("Student Info", jhub_user, seed)

    responses = ensure_responses()

    if not isinstance(responses.get("seed"), int):
        raise ValueError("Seed not set or is not an integer")
    return responses


def check_api_connection():
    if not api_base_url:
        raise Exception("Environment variable for API URL not set")


def get_jhub_user():
    jhub_user = os.getenv("JUPYTERHUB_USER")
    if jhub_user is None:
        raise Exception("Setup unsuccessful. Are you on JupyterHub?")
    return jhub_user


def initialize_telemetry():
    ipython = get_ipython()
    if ipython is None:
        raise Exception("Setup unsuccessful. Are you in a Jupyter environment?")

    try:
        move_dotfiles()
        ipython.events.register("pre_run_cell", telemetry)
    except Exception as e:
        raise Exception(f"Failed to register telemetry: {e}")


def build_assignment_tag(week, assignment_type, assignment_tag):
    if assignment_tag is None:
        if week is None:
            raise ValueError("Week is required when assignment_tag is not provided")
        if assignment_type is None:
            raise ValueError(
                "Assignment type is required when assignment_tag is not provided"
            )
        assignment_tag = f"{week}-{assignment_type}"
    return assignment_tag


def move_dotfiles():
    """
    Move essential dotfiles from a fixed source directory to the current working directory.

    Raises:
        FileNotFoundError: If a source file is missing.
        Exception: If copying fails for any other reason.
    """
    source_dir = Path("/opt/dotfiles")
    target_dir = Path.cwd()

    files_to_copy = [".client_private_key.bin", ".server_public_key.bin"]

    for file_name in files_to_copy:
        source_file = source_dir / file_name
        target_file = target_dir / file_name

        if not source_file.exists():
            raise FileNotFoundError(f"Key file not found: {source_file}")

        try:
            shutil.copy2(source_file, target_file)
        except Exception as e:
            raise Exception(f"Failed to copy {source_file} to {target_file}: {e}")


def username_to_seed(username: str, mod: int = 1000) -> int:
    hash_object = hashlib.sha256(username.encode())
    hash_hex = hash_object.hexdigest()
    hash_int = int(hash_hex, 16)
    return hash_int % mod
