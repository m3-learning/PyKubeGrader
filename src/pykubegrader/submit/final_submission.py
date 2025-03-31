import os

import requests
from requests.auth import HTTPBasicAuth

from ..submit.submit_assignment import get_credentials


def final_submission(
    assignment: str, assignment_type: str, token: str, week_number=None
) -> None:
    """
    Mark a student as complete for an assignment
    """

    base_url = os.getenv("DB_URL")
    if not base_url:
        raise ValueError("Environment variable 'DB_URL' not set")

    url = base_url.rstrip("/") + "/completed-assignments"

    username, password = get_credentials().values()

    params = final_submission_payload(
        assignment=assignment,
        assignment_type=assignment_type,
        token=token,
        week_number=week_number,
    )

    env_token = os.getenv("TOKEN")
    if env_token:
        params["key_used"] = token

    try:
        res = requests.post(
            url=url, auth=HTTPBasicAuth(username, password), json=params
        )
        res.raise_for_status()

        return res.json()

    except requests.RequestException as err:
        raise RuntimeError(f"An error occurred while requesting {url}: {err}")
    except Exception as err:
        raise RuntimeError(f"An unexpected error occurred: {err}")


def final_submission_payload(
    assignment: str, assignment_type: str, token: str, week_number=None
) -> dict:
    jhub_user = os.getenv("JUPYTERHUB_USER")
    if jhub_user is None:
        raise ValueError("JupyterHub user not found")

    student_email = jhub_user

    payload = {
        "student_email": student_email,
        "assignment": assignment,
        "week_number": week_number,
        "assignment_type": assignment_type,
        "student_seed": 0,  # Not Implemented
        "key_used": token,
    }

    return payload


def delete_completed_assignment(
    assignment: str,
    assignment_type: str,
    token: str,
    week_number: int,
    admin_user: str,
    admin_pw: str,
) -> None:
    base_url = os.getenv("DB_URL")
    if not base_url:
        raise ValueError("Environment variable 'DB_URL' not set")

    url = base_url.rstrip("/") + "/completed-assignments"

    params = final_submission_payload(
        assignment=assignment,
        assignment_type=assignment_type,
        token=token,
        week_number=week_number,
    )

    env_token = os.getenv("TOKEN")
    if env_token:
        params["key_used"] = token

    try:
        res = requests.delete(
            url, params=params, auth=HTTPBasicAuth(admin_user, admin_pw)
        )
        res.raise_for_status()
        return res.json()

    except requests.RequestException as err:
        raise RuntimeError(f"An error occurred while requesting {url}: {err}")
    except Exception as err:
        raise RuntimeError(f"An unexpected error occurred: {err}")
