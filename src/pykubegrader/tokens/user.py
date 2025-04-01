from pykubegrader._initialize import username_to_seed
from pykubegrader.telemetry.responses import (
    ensure_responses,
    log_variable,
    set_responses_json,
)


def generate_user_seed(name, week, assignment_type, jhub_user):
    """
    Generate a user seed and set response JSON.

    This function generates a seed based on the JupyterHub username, sets various
    response JSON values, logs the student information, and ensures the responses
    are correctly set.

    Args:
        name (str): The name of the assignment.
        week (str): The week of the assignment.
        assignment_type (str): The type of the assignment.
        jhub_user (str): The JupyterHub username of the student.

    Returns:
        dict: The responses dictionary containing the seed and other assignment details.

    Raises:
        ValueError: If the seed is not set or is not an integer.
    """
    seed = username_to_seed(jhub_user) % 1000
    set_responses_json(key="seed", value=seed)
    set_responses_json(key="week", value=week)
    set_responses_json(key="assignment_type", value=assignment_type)

    set_responses_json(key="assignment", value=name)
    set_responses_json(key="jhub_user", value=jhub_user)

    log_variable("Student Info", jhub_user, seed)

    responses = ensure_responses()

    if not isinstance(responses.get("seed"), int):
        raise ValueError("Seed not set or is not an integer")

    return responses
