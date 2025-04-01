from pathlib import Path
import shutil
from typing import Optional
from pykubegrader._telemetry import telemetry
from pykubegrader.api.checks import check_api_connection, check_ipython
from pykubegrader.os.user import get_jhub_user
from pykubegrader.telemetry.responses import log_variable
import panel as pn
from pykubegrader.tokens.user import generate_user_seed
from pykubegrader._utils import api_base_url

import requests

from pykubegrader.utils.printing.api import print_api_response
from pykubegrader.utils.printing.assignments import print_assignment_info


def initialize_assignment(
    name: str,
    week: Optional[str] = None,
    assignment_type: Optional[str] = None,
    verbose: Optional[bool] = False,
    assignment_points: Optional[float] = None,
    assignment_tag: Optional[str] = None,
    **kwargs,
) -> dict:
    """
    Initialize an assignment in a Jupyter environment.

    This function prepares the environment for an assignment by performing the following steps:
    1. Generates a user-specific seed for the assignment.
    2. Initializes telemetry to track assignment interactions.
    3. Verifies the connection to the API server.
    4. Logs the total points for the assignment.
    5. Prints initialization details if verbose mode is enabled.

    Args:
        name (str): The name of the assignment.
        week (Optional[str]): The week of the assignment. Defaults to None.
        assignment_type (Optional[str]): The type of the assignment. Defaults to None.
        verbose (Optional[bool]): If True, prints detailed initialization information. Defaults to False.
        assignment_points (Optional[float]): The total points available for the assignment. Defaults to None.
        assignment_tag (Optional[str]): A custom tag for the assignment. Defaults to None.
        **kwargs: Additional keyword arguments to be passed to the move_dotfiles function.

    Returns:
        dict: A dictionary containing user and assignment details after initialization.

    Raises:
        Exception: If the environment is unsupported or if initialization encounters an error.
    """

    assignment_tag = build_assignment_tag(week, assignment_type, assignment_tag)

    initialize_telemetry(**kwargs)

    jhub_user = get_jhub_user()

    try:
        responses = generate_user_seed(name, week, assignment_type, jhub_user)

        
        pn.extension(silent=True)

        # Check connection to API server
        check_api_connection()

        params = {"jhub_user": responses["jhub_user"]}

        response = requests.get(api_base_url, params=params)

        print_api_response(response, verbose = verbose)

    except Exception as e:
        raise Exception(f"Failed to initialize assignment: {e}")

    log_variable("total-points", f"{assignment_tag}, {name}", assignment_points)

    print("Assignment successfully initialized")
    print_assignment_info(name, jhub_user, verbose = verbose)

    return responses


def initialize_telemetry(**kwargs):
    """
    Initialize telemetry for the Jupyter environment.

    This function performs the following steps:
    1. Checks if the current environment is a Jupyter environment.
    2. Moves essential dotfiles from a fixed source directory to the current working directory.
    3. Registers the telemetry function to be called before each cell execution.

    Args:
        **kwargs: Additional keyword arguments to be passed to the move_dotfiles function.

    Raises:
        Exception: If the environment is not a Jupyter environment or if telemetry
                   registration fails.
    """
    ipython = check_ipython()

    try:
        move_dotfiles(**kwargs)
        ipython.events.register("pre_run_cell", telemetry)
    except Exception as e:
        raise Exception(f"Failed to register telemetry: {e}")

def move_dotfiles(**kwargs):
    """
    Move essential dotfiles from a fixed source directory to the current working directory.

    This function copies essential dotfiles required for the environment setup from a predefined
    source directory to the current working directory. It ensures that the necessary key files
    are available and correctly placed for further operations.

    Args:
        **kwargs: Additional keyword arguments to specify custom file paths.
            - client_private_key_path (str): Custom path for the client private key file.
            - server_public_key_path (str): Custom path for the server public key file.

    Raises:
        FileNotFoundError: If a source file is missing.
        Exception: If copying fails for any other reason.
    """
    client_private_key_path = kwargs.get("client_private_key_path", ".client_private_key.bin")
    server_public_key_path = kwargs.get("server_public_key_path", ".server_public_key.bin")
    
    source_dir = Path("/opt/dotfiles")
    target_dir = Path.cwd()

    files_to_copy = [client_private_key_path, server_public_key_path]

    for file_name in files_to_copy:
        source_file = source_dir / file_name
        target_file = target_dir / file_name

        if not source_file.exists():
            raise FileNotFoundError(f"Key file not found: {source_file}")

        try:
            shutil.copy2(source_file, target_file)
        except Exception as e:
            raise Exception(f"Failed to copy {source_file} to {target_file}: {e}")


def build_assignment_tag(week, assignment_type, assignment_tag):
    """
    Build an assignment tag based on the week and assignment type.

    This function constructs an assignment tag using the provided week and assignment type.
    If the assignment tag is not provided, it will be generated using the week and assignment type.

    Args:
        week (str): The week of the assignment.
        assignment_type (str): The type of the assignment.
        assignment_tag (str, optional): The assignment tag. If not provided, it will be generated.

    Returns:
        str: The constructed assignment tag.

    Raises:
        ValueError: If the week or assignment type is not provided when assignment_tag is None.
    """
    if assignment_tag is None:
        if week is None:
            raise ValueError("Week is required when assignment_tag is not provided")
        if assignment_type is None:
            raise ValueError("Assignment type is required when assignment_tag is not provided")
        assignment_tag = f"{week}-{assignment_type}"
    return assignment_tag