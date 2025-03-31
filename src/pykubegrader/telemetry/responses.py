import datetime
import json
import logging
import os
from typing import Any

from pykubegrader._telemetry import logger_reduced
from pykubegrader.utils.security.jupyter import block_direct_notebook_calls
from pykubegrader.utils.security.encryption import encrypt_to_b64


def log_encrypted(logger: logging.Logger, message: str) -> None:
    """
    Logs an encrypted version of the given message using the provided logger.

    Args:
        logger (object): The logger object used to log the encrypted message.
        message (str): The message to be encrypted and logged.

    Returns:
        None
    """
    encrypted_b64 = encrypt_to_b64(message)
    logger.info(f"Encrypted Output: {encrypted_b64}")

@block_direct_notebook_calls
def log_variable(assignment_name: str, value: Any, info_type: str) -> None:
    """
    Logs a variable with its assignment name, value, and type, along with a timestamp.

    This function constructs a log message containing the assignment name, the type of information,
    the value, and a timestamp. The message is then encrypted and logged using the reduced logger.

    Args:
        assignment_name (str): The name of the assignment.
        value (Any): The value to be logged.
        info_type (str): The type of information being logged.

    Returns:
        None
    """
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat(
        sep=" ", timespec="seconds"
    )
    message = f"{assignment_name}, {info_type}, {value}, {timestamp}"
    log_encrypted(logger_reduced, message)


def ensure_responses() -> dict[str, Any]:
    """
    Ensures the existence and integrity of the responses file.

    This function checks for the existence of the .responses.json file and ensures it is properly formatted.
    If the file does not exist or is not properly formatted, it initializes an empty dictionary and writes it to the file.

    Returns:
        dict[str, Any]: The responses dictionary loaded from the .responses.json file.
    """
    with open(".responses.json", "a") as _:
        pass

    responses = {}

    try:
        with open(".responses.json", "r") as f:
            responses = json.load(f)
    except json.JSONDecodeError:
        with open(".responses.json", "w") as f:
            json.dump(responses, f)

    return responses


def set_responses_json(key: str, value) -> dict:
    """
    Updates the responses dictionary with a new key-value pair and writes it to the .responses.json file.

    This function ensures the existence and integrity of the responses file, updates it with the provided key-value pair,
    and writes the updated dictionary back to the file. It uses a temporary file to ensure atomicity of the write operation.

    Args:
        key (str): The key to be added or updated in the responses dictionary.
        value (Any): The value to be associated with the key in the responses dictionary.

    Returns:
        dict: The updated responses dictionary.

    Raises:
        TypeError: If the value provided is not serializable to JSON.
        json.JSONDecodeError: If there is an error decoding the JSON file.
    """
    data = ensure_responses()
    data[key] = value

    temp_path = ".responses.tmp"
    orig_path = ".responses.json"

    try:
        with open(temp_path, "w") as f:
            json.dump(data, f)

        os.replace(temp_path, orig_path)
    except (TypeError, json.JSONDecodeError) as e:
        print(f"Failed to update responses: {e}")

        if os.path.exists(temp_path):
            os.remove(temp_path)

        raise

    return data