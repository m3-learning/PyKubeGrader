from pykubegrader.telemetry.responses import ensure_responses, log_variable
from pykubegrader.utils import api_base_url, student_pw, student_user


import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException


from typing import Any


def score_question(term: str = "winter_2025") -> None:
    """
    Scores a question by sending a request to the live-scorer endpoint.

    This function constructs a payload with student and assignment details,
    sends it to the live-scorer endpoint, and logs the scores received in the response.

    Args:
        term (str): The academic term for which the question is being scored. Defaults to "winter_2025".

    Raises:
        ValueError: If necessary environment variables are not set.
        RuntimeError: If there is a failure accessing the question-scoring endpoint.
        ValueError: If there is a failure parsing the JSON response from the scoring endpoint.
        RuntimeError: For any other exceptions that occur during the scoring process.
    """
    if not student_user or not student_pw or not api_base_url:
        raise ValueError("Necessary environment variables not set")

    url = api_base_url.rstrip("/") + "/live-scorer"

    responses = ensure_responses()

    # TODO: Make week optional
    # TODO: Make student email not drexel.edu
    payload: dict[str, Any] = {
        "student_email": f"{responses['jhub_user']}@drexel.edu",
        "term": term,
        "week": responses["week"],
        "assignment": responses["assignment_type"],
        "question": f"_{responses['assignment']}",
        "responses": responses,
    }

    try:
        res = requests.post(
            url, json=payload, auth=HTTPBasicAuth(student_user, student_pw)
        )
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
