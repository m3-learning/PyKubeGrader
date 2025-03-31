from pykubegrader.utils import api_base_url, student_pw, student_user

import requests
from requests import Response
from requests.auth import HTTPBasicAuth


def submit_question(
    student_email: str,
    term: str,
    assignment: str,
    question: str,
    responses: dict,
    score: dict,
) -> Response:
    """
    Submits a question's responses and score to the server.

    This function constructs a payload with student and assignment details,
    sends it to the submit-question endpoint, and returns the server's response.

    Args:
        student_email (str): The email of the student submitting the question.
        term (str): The academic term for which the question is being submitted.
        assignment (str): The name of the assignment.
        question (str): The specific question being submitted.
        responses (dict): The student's responses to the question.
        score (dict): The score for the question.

    Returns:
        Response: The response from the server after submitting the question.

    Raises:
        ValueError: If necessary environment variables are not set.
    """
    if not student_user or not student_pw or not api_base_url:
        raise ValueError("Necessary environment variables not set")

    url = api_base_url.rstrip("/") + "/submit-question"

    payload = {
        "student_email": student_email,
        "term": term,
        "assignment": assignment,
        "question": question,
        "responses": responses,
        "score": score,
    }

    res = requests.post(url, json=payload, auth=HTTPBasicAuth(student_user, student_pw))

    return res
