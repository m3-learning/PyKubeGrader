import os
import shutil
from pathlib import Path

import panel as pn
import requests
from IPython import get_ipython

from .telemetry import ensure_responses, telemetry, update_responses


def initialize_assignment(
    name: str,
    url: str = "https://engr-131-api.eastus.cloudapp.azure.com/",
    verbose: bool = False,
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
        seed = hash(jhub_user) % 1000
        update_responses(key="seed", value=seed)

        update_responses(key="assignment", value=name)
        update_responses(key="jhub_user", value=jhub_user)

        responses = ensure_responses()
        # TODO: Add more checks here?
        assert isinstance(responses.get("seed"), int), "Seed not set"

        pn.extension(silent=True)

        # Check connection to API server
        params = {"jhub_user": responses["jhub_user"]}
        response = requests.get(url, params=params)
        if verbose:
            print(f"status code: {response.status_code}")
            data = response.json()
            for k, v in data.items():
                print(f"{k}: {v}")
    except Exception as e:
        raise Exception(f"Failed to initialize assignment: {e}")

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
