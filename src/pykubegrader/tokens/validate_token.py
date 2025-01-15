import asyncio
import os
from typing import Optional

import httpx
import nest_asyncio  # type: ignore
import requests
from requests.auth import HTTPBasicAuth

# Apply nest_asyncio for environments like Jupyter
nest_asyncio.apply()


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


async def async_validate_token(token: Optional[str] = None) -> None:
    """
    Asynchronously validate a token by making a GET request to the validation endpoint.

    Args:
        token (str): The token to validate.

    Raises:
        TokenValidationError: If the token is invalid or if there is an error in the validation process.

    Returns:
        None: If the token is valid, the function will pass silently.
    """

    # First, check if token is provided as an argument
    if token is not None:
        os.environ["TOKEN"] = token

    # Next, check if token is available in environment variables
    if token is None:
        token = os.getenv("TOKEN", None)

    # Otherwise, raise an error
    if token is None:
        raise TokenValidationError("No token provided")

    # Fetch the endpoint URL
    base_url = os.getenv("DB_URL")
    if not base_url:
        raise ValueError("Environment variable 'DB_URL' not set")
    endpoint = f"{base_url}validate-token/{token}"

    # Get credentials
    credentials = get_credentials()
    username = credentials["username"]
    password = credentials["password"]

    basic_auth = httpx.BasicAuth(username=username, password=password)

    # Make GET request
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url=endpoint, auth=basic_auth, timeout=10)
            response.raise_for_status()
            return
        except httpx.HTTPStatusError as e:
            detail = e.response.json().get("detail", e.response.text)
            raise TokenValidationError(detail)
        except httpx.RequestError as e:
            raise TokenValidationError(f"Request failed: {e}")
        except Exception as e:
            raise TokenValidationError(f"An unexpected error occurred: {e}")


def validate_token(token: Optional[str] = None) -> None:
    """
    Synchronous wrapper for the `async_validate_token` function.

    Args:
        token (str): The token to validate.

    Raises:
        TokenValidationError: If the token is invalid or if there is an error in the validation process.

    Returns:
        None: If the token is valid, the function will pass silently.
    """

    # Get the current event loop or create one
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Run the async function in the event loop
    loop.run_until_complete(async_validate_token(token))


def validate_token_sync(token: Optional[str] = None) -> None:
    # First, check if token is provided as an argument
    if token is not None:
        os.environ["TOKEN"] = token

    # Next, check if token is available in environment variables
    if token is None:
        token = os.getenv("TOKEN", None)

    # Otherwise, raise an error
    if token is None:
        raise TokenValidationError("No token provided")

    # Fetch the endpoint URL
    base_url = os.getenv("DB_URL")
    if not base_url:
        raise ValueError("Environment variable 'DB_URL' not set")
    endpoint = f"{base_url}validate-token/{token}"

    # Get credentials
    credentials = get_credentials()
    username = credentials["username"]
    password = credentials["password"]
    basic_auth = HTTPBasicAuth(username, password)

    try:
        response = requests.get(url=endpoint, auth=basic_auth)
        response.raise_for_status()
        return
    except requests.exceptions.HTTPError as e:
        detail = e.response.json().get("detail", e.response.text)
        raise TokenValidationError(detail)
    except requests.exceptions.RequestException as e:
        raise TokenValidationError(f"Request failed: {e}")
    except Exception as e:
        raise TokenValidationError(f"An unexpected error occurred: {e}")


# Example usage
if __name__ == "__main__":
    token = "test"

    try:
        validate_token(token)
        print("Token is valid")
    except TokenValidationError as e:
        print(f"Token validation failed: {e}")
