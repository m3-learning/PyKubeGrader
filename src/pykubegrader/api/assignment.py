from typing import Optional
from pykubegrader._initialize import build_assignment_tag, check_api_connection, generate_user_seed, get_jhub_user, move_dotfiles, print_api_response, print_assignment_info
from pykubegrader._telemetry import telemetry
from pykubegrader.api.checks import check_ipython
from pykubegrader.telemetry.responses import log_variable
import panel as pn
from pykubegrader.utils import api_base_url

import requests


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

    This function sets up the necessary environment for an assignment by generating
    a user seed, initializing telemetry, and verifying the API connection. It also
    logs the total points for the assignment and prints initialization details if
    verbose mode is enabled.

    Args:
        name (str): The name of the assignment.
        week (Optional[str]): The week of the assignment. Defaults to None.
        assignment_type (Optional[str]): The type of the assignment. Defaults to None.
        verbose (Optional[bool]): Whether to print detailed initialization information. Defaults to False.
        assignment_points (Optional[float]): The total points for the assignment. Defaults to None.
        assignment_tag (Optional[str]): A custom tag for the assignment. Defaults to None.

    Returns:
        dict: The responses dictionary after initialization, containing user and assignment details.

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

        print_api_response(response, verbose = verbose)

    except Exception as e:
        raise Exception(f"Failed to initialize assignment: {e}")

    log_variable("total-points", f"{assignment_tag}, {name}", assignment_points)

    print("Assignment successfully initialized")
    print_assignment_info(name, jhub_user, verbose = verbose)

    return responses


def initialize_telemetry():
    """
    Initialize telemetry for the Jupyter environment.

    This function checks if the current environment is a Jupyter environment,
    moves essential dotfiles, and registers the telemetry function to be called
    before each cell execution.

    Raises:
        Exception: If the environment is not a Jupyter environment or if telemetry
                   registration fails.
    """
    ipython = check_ipython()

    try:
        move_dotfiles()
        ipython.events.register("pre_run_cell", telemetry)
    except Exception as e:
        raise Exception(f"Failed to register telemetry: {e}")