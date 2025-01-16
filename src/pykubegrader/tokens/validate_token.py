import os
import sys
from typing import Optional

import requests
from requests.auth import HTTPBasicAuth


class TokenValidationError(Exception):
    """
    Custom exception raised when the token validation fails.
    """

    def __init__(self, message: Optional[str] = None):
        """
        Initialize the exception with an optional message.

        Args:
            message (str, optional): The error message to display. Defaults to None.
        """

        super().__init__(message)


def get_credentials() -> dict[str, str]:
    """
    Fetch the username and password from environment variables.

    Returns:
        dict: A dictionary containing 'username' and 'password'.
    """

    username = os.getenv("user_name_student")
    password = os.getenv("keys_student")

    if not username or not password:
        raise ValueError(
            "Environment variable 'user_name_student' or 'keys_student' not set"
        )

    return {"username": username, "password": password}


def validate_token(token: Optional[str] = None) -> None:
    if token:
        os.environ["TOKEN"] = token  # If token passed, set env var
    else:
        token = os.getenv("TOKEN")  # Otherwise try to get from env
        if not token:
            print("Error: No token provided", file=sys.stderr)
            sys.exit(1)

    # Get endpoint URL
    base_url = os.getenv("DB_URL")
    if not base_url:
        print("Error: Environment variable 'DB_URL' not set", file=sys.stderr)
        sys.exit(1)
    endpoint = f"{base_url.rstrip('/')}/validate-token/{token}"

    # Get credentials
    try:
        credentials = get_credentials()
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    username = credentials["username"]
    password = credentials["password"]
    basic_auth = HTTPBasicAuth(username, password)

    try:
        response = requests.get(url=endpoint, auth=basic_auth, timeout=10)
        response.raise_for_status()

        detail = response.json().get("detail", response.text)
        return
    except requests.exceptions.HTTPError as e:
        detail = e.response.json().get("detail", e.response.text)
        print(f"Error: {detail}", file=sys.stderr)
    except requests.exceptions.RequestException as e:
        print(f"Error: Request failed: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)

    sys.exit(1)  # If we reached here, something went wrong


# Example usage
if __name__ == "__main__":
    token = "test"

    try:
        validate_token(token)
        print("Token is valid")
    except TokenValidationError as e:
        print(f"Token validation failed: {e}")
