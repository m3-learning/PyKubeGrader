import base64
import datetime
import json
import logging
import os
from typing import Any, Optional

import nacl.public
import requests
from IPython.core.interactiveshell import ExecutionInfo
from requests import Response
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException

#
# Logging setup
#

# Logger for cell execution
logger_code = logging.getLogger("code_logger")
logger_code.setLevel(logging.INFO)

file_handler_code = logging.FileHandler(".output_code.log")
file_handler_code.setLevel(logging.INFO)
logger_code.addHandler(file_handler_code)

# Logger for question scores etc.
logger_reduced = logging.getLogger("reduced_logger")
logger_reduced.setLevel(logging.INFO)

file_handler_reduced = logging.FileHandler(".output_reduced.log")
file_handler_reduced.setLevel(logging.INFO)
logger_reduced.addHandler(file_handler_reduced)

#
# Local functions
#


def encrypt_to_b64(message: str) -> str:
    with open(".server_public_key.bin", "rb") as f:
        server_pub_key_bytes = f.read()
    server_pub_key = nacl.public.PublicKey(server_pub_key_bytes)

    with open(".client_private_key.bin", "rb") as f:
        client_private_key_bytes = f.read()
    client_priv_key = nacl.public.PrivateKey(client_private_key_bytes)

    box = nacl.public.Box(client_priv_key, server_pub_key)
    encrypted = box.encrypt(message.encode())
    encrypted_b64 = base64.b64encode(encrypted).decode("utf-8")

    return encrypted_b64


def ensure_responses() -> dict[str, Any]:
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


def log_variable(assignment_name, value, info_type) -> None:
    timestamp = datetime.datetime.now(datetime.UTC).isoformat(
        sep=" ", timespec="seconds"
    )
    message = f"{assignment_name}, {info_type}, {value}, {timestamp}"
    log_encrypted(logger_reduced, message)


def telemetry(info: ExecutionInfo) -> None:
    cell_content = info.raw_cell
    log_encrypted(logger_code, f"code run: {cell_content}")


def update_responses(key: str, value) -> dict:
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


#
# API request functions
#


def score_question(
    term: str = "winter_2025",
    base_url: str = "https://engr-131-api.eastus.cloudapp.azure.com",
) -> None:
    url = base_url + "/live-scorer"

    responses = ensure_responses()

    payload: dict[str, Any] = {
        "student_email": f"{responses['jhub_user']}@drexel.edu",
        "term": term,
        "week": responses["week"],
        "assignment": responses["assignment_type"],
        "question": f"_{responses['assignment']}",
        "responses": responses,
    }

    try:
        res = requests.post(url, json=payload, auth=HTTPBasicAuth("student", "capture"))
        res.raise_for_status()

        res_data: dict[str, tuple[float, float]] = res.json()

        for question, (points_earned, max_points) in res_data.items():
            log_variable(
                assignment_name=responses["assignment"],
                value=f"{points_earned}, {max_points}",
                info_type=question,
            )
    except RequestException as e:
        raise RuntimeError("Failed to access question-scoring endpoint") from e
    except ValueError as e:
        raise ValueError("Failed to parse question-scoring JSON response") from e
    except Exception as e:
        raise RuntimeError("Failed to score question") from e


def submit_question(
    student_email: str,
    term: str,
    assignment: str,
    question: str,
    responses: dict,
    score: dict,
    base_url: str = "https://engr-131-api.eastus.cloudapp.azure.com/",
) -> Response:
    url = base_url + "/submit-question"

    payload = {
        "student_email": student_email,
        "term": term,
        "assignment": assignment,
        "question": question,
        "responses": responses,
        "score": score,
    }

    res = requests.post(url, json=payload, auth=HTTPBasicAuth("student", "capture"))

    return res


# TODO: Refine
def verify_server(
    jhub_user: Optional[str] = None,
    url: str = "https://engr-131-api.eastus.cloudapp.azure.com/",
) -> str:
    params = {"jhub_user": jhub_user} if jhub_user else {}
    res = requests.get(url, params=params)
    message = f"status code: {res.status_code}"
    return message
