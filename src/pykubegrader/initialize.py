import hashlib
import os
import shutil
from pathlib import Path
from typing import Optional

import panel as pn
import requests
from IPython.core.getipython import get_ipython

from .telemetry import ensure_responses, log_variable, telemetry, update_responses
from .utils import api_base_url


# TODO: could cleanup to remove redundant imports
def initialize_assignment(
    name: str,
    week: str,
    assignment_type: str,
    verbose: bool = False,
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

    if assignment_tag is None:
        assignment_tag = f"{week}-{assignment_type}"

    ipython = get_ipython()
    if ipython is None:
        raise Exception("Setup unsuccessful. Are you in a Jupyter environment?")

    try:
        move_dotfiles()
        ipython.events.register("pre_run_cell", telemetry)
    except Exception as e:
        raise Exception(f"Failed to register telemetry: {e}")

    jhub_user = os.getenv("JUPYTERHUB_USER")
    if jhub_user is None:
        raise Exception("Setup unsuccessful. Are you on JupyterHub?")

    try:
        seed = username_to_seed(jhub_user) % 1000
        update_responses(key="seed", value=seed)
        update_responses(key="week", value=week)
        update_responses(key="assignment_type", value=assignment_type)

        update_responses(key="assignment", value=name)
        update_responses(key="jhub_user", value=jhub_user)

        # TODO: Check whether this is called correctly
        log_variable("Student Info", jhub_user, seed)

        responses = ensure_responses()
        # TODO: Add more checks here?
        assert isinstance(responses.get("seed"), int), "Seed not set"

        pn.extension(silent=True)

        # Check connection to API server
        if not api_base_url:
            raise Exception("Environment variable for API URL not set")
        params = {"jhub_user": responses["jhub_user"]}
        response = requests.get(api_base_url, params=params)
        if verbose:
            print(f"status code: {response.status_code}")
            data = response.json()
            for k, v in data.items():
                print(f"{k}: {v}")
    except Exception as e:
        raise Exception(f"Failed to initialize assignment: {e}")

    log_variable("total-points", f"{assignment_tag}, {name}", assignment_points)

    print("Assignment successfully initialized")
    if verbose:
        print(f"Assignment: {name}")
        print(f"Username: {jhub_user}")

    return responses


#
# Helper functions
#


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
