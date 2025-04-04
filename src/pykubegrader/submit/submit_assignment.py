import json
import os
from typing import Dict

import requests
from requests.auth import HTTPBasicAuth


def get_credentials():
    """
    Fetch the username and password from environment variables.
    """
    username = os.getenv("user_name_student")
    password = os.getenv("keys_student")
    if not username or not password:
        raise ValueError(
            "Environment variables 'user_name_student' or 'keys_student' are not set."
        )
    return {"username": username, "password": password}


def call_score_assignment(
    assignment_title: str, notebook_title: str, file_path: str = ".output_reduced.log"
) -> Dict[str, str]:
    """
    Submit an assignment to the scoring endpoint.

    Args:
        assignment_title (str): Title of the assignment
        notebook_title (str): Title of the notebook
        file_path (str): Path to the log file to upload

    Returns:
        dict: JSON response from the server

    Raises:
        RuntimeError: If server returns a client or server error
        FileNotFoundError: If the log file doesn't exist
    """

    base_url = os.getenv("DB_URL")
    if not base_url:
        raise ValueError("Environment variable 'DB_URL' not set")

    url = base_url.rstrip("/") + "/score-assignment"

    params = {
        "assignment_title": assignment_title,
        "notebook_title": notebook_title,
    }

    token = os.getenv("TOKEN")
    if token:
        params["key_used"] = token

    username, password = get_credentials().values()

    try:
        with open(file_path, "rb") as file:
            res = requests.post(
                url=url,
                params=params,
                auth=HTTPBasicAuth(username, password),
                files={"log_file": file},
            )

            if res.status_code != 200:
                # Try to extract a meaningful error message
                try:
                    err_detail = res.json().get("detail", "No detail provided")
                except json.JSONDecodeError:
                    err_detail = res.text  # fallback to raw text

                raise RuntimeError(f"Server returned {res.status_code}: {err_detail}")

            return res.json()

    except FileNotFoundError:
        raise FileNotFoundError(f"File {file_path} does not exist")

    except requests.RequestException as err:
        raise RuntimeError(f"Request failed to {url}: {err}")

    except Exception as err:
        raise RuntimeError(f"Unexpected error: {err}")


def submit_assignment(
    assignment_title: str,
    notebook_title: str,
    file_path: str = ".output_reduced.log",
) -> None:
    """
    Synchronous wrapper for the `call_score_assignment` function.

    Args:
        assignment_title (str): Title of the assignment.
        file_path (str): Path to the log file to upload.
    """

    response = call_score_assignment(assignment_title, notebook_title, file_path)

    print("Server Response:", response.get("message", "No message in response"))


# Example usage (remove this section if only the function needs to be importable):
if __name__ == "__main__":
    submit_assignment("week1-readings", "path/to/your/log_file.txt")
