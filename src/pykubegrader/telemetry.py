import base64
import datetime
import json
import logging
import os
from typing import Optional

import nacl.public
import requests
from IPython.core.interactiveshell import ExecutionInfo
from requests import Response
from requests.auth import HTTPBasicAuth

# Set logging config (`force` is important)
logging.basicConfig(filename=".output.log", level=logging.INFO, force=True)

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


def ensure_responses() -> dict:
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


def log_encrypted(message: str) -> None:
    encrypted_b64 = encrypt_to_b64(message)
    logging.info(f"Encrypted Output: {encrypted_b64}")


def log_variable(assignment_name, value, info_type) -> None:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"{info_type}, {value}, {timestamp}, {assignment_name}"
    log_encrypted(message)


def telemetry(info: ExecutionInfo) -> None:
    cell_content = info.raw_cell
    log_encrypted(f"code run: {cell_content}")


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


# If we instead call this with **responses
def score_question(
    student_email: str,
    assignment: str,
    question: str,
    submission: str,
    term: str = "winter_2025",
    base_url: str = "https://engr-131-api.eastus.cloudapp.azure.com/",
) -> Response:
    url = base_url + "/live-scorer"

    payload = {
        "student_email": student_email,
        "term": term,
        "assignment": assignment,
        "question": question,
        "responses": submission,
    }

    res = requests.post(url, json=payload, auth=HTTPBasicAuth("student", "capture"))

    return res


def submit_question(
    student_email: str,
    term: str,
    assignment: str,
    question: str,
    responses: dict,
    score: dict,
    base_url: str = "https://engr-131-api.eastus.cloudapp.azure.com/",
):
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


# TODO: refine function
def verify_server(
    jhub_user: Optional[str] = None,
    url: str = "https://engr-131-api.eastus.cloudapp.azure.com/",
) -> str:
    params = {"jhub_user": jhub_user} if jhub_user else {}
    res = requests.get(url, params=params)
    message = f"status code: {res.status_code}"
    return message


# TODO: implement function; or maybe not?
# At least improve other one
def score_question_improved(question_name: str, responses: dict) -> dict:
    return {}
