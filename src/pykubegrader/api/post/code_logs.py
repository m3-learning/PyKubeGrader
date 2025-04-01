from pykubegrader.telemetry.responses import ensure_responses
from pykubegrader._utils import api_base_url, student_pw, student_user


import requests
from requests.auth import HTTPBasicAuth


import base64
import gzip


def upload_execution_log() -> None:
    """
    Uploads the code execution log to the server.

    This function retrieves the student's email and assignment name from the responses,
    reads the code execution log file, compresses and encodes it, and then uploads it
    to the server using a POST request.

    Raises:
        ValueError: If necessary environment variables are not set or if student email
                    and/or assignment name are missing.
        FileNotFoundError: If the code execution log file is not found.
        requests.exceptions.HTTPError: If the HTTP request returned an unsuccessful status code.
    """
    if not student_user or not student_pw or not api_base_url:
        raise ValueError("Necessary environment variables not set")

    responses = ensure_responses()
    student_email: str = responses["jhub_user"]
    assignment: str = responses["assignment"]

    if not student_email or not assignment:
        raise ValueError("Missing student email and/or assignment name")

    print(f"Student: {student_email}")
    print(f"Assignment: {assignment}")
    print("Uploading code execution log...")

    try:
        with open(".output_code.log", "rb") as f:
            log_bytes = f.read()
    except FileNotFoundError:
        raise FileNotFoundError("Code execution log not found")

    print(f"Uncompressed log size: {len(log_bytes)} bytes")

    compressed = gzip.compress(log_bytes)

    print(f"Compressed log size: {len(compressed)} bytes")

    encoded = base64.b64encode(compressed).decode("utf-8")

    payload = {
        "student_email": student_email,
        "assignment": assignment,
        "encrypted_content": encoded,
    }

    res = requests.post(
        url=api_base_url.rstrip("/") + "/execution-logs",
        json=payload,
        auth=HTTPBasicAuth(student_user, student_pw),
    )
    res.raise_for_status()

    print("Execution log uploaded successfully")
