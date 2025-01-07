import asyncio
import base64
import os

import httpx
import nest_asyncio  # type: ignore

# Apply nest_asyncio for environments like Jupyter
nest_asyncio.apply()


class TokenValidationError(Exception):
    """
    Custom exception raised when the token validation fails.
    """

    def __init__(self, message=None):
        """
        Initialize the exception with an optional message.

        Args:
            message (str, optional): The error message to display. Defaults to None.
        """
        super().__init__(message)


def get_credentials():
    """
    Fetch the username and password from environment variables.

    Returns:
        dict: A dictionary containing 'username' and 'password'.
    """
    username = os.getenv("user_name_student")
    password = os.getenv("keys_student")
    if not username or not password:
        raise ValueError(
            "Environment variables 'user_name_student' or 'keys_student' are not set."
        )
    return {"username": username, "password": password}


async def async_validate_token(token: str = None) -> None:
    """
    Asynchronously validate a token by making a GET request to the validation endpoint.

    Args:
        token (str): The token to validate.

    Raises:
        TokenValidationError: If the token is invalid or if there is an error in the validation process.

    Returns:
        None: If the token is valid, the function will pass silently.
    """

    if token is not None:
        os.environ["TOKEN"] = token

    if token is None:
        token = os.getenv("TOKEN", None)

    if token is None:
        raise TokenValidationError("No token provided")

    # Fetch the endpoint URL
    base_url = os.getenv("DB_URL")
    if not base_url:
        raise ValueError("Environment variable 'DB_URL' is not set.")
    endpoint = f"{base_url}validate-token/{token}"

    # Get credentials
    credentials = get_credentials()
    username = credentials["username"]
    password = credentials["password"]

    # Encode credentials for Basic Authentication
    auth_header = (
        f"Basic {base64.b64encode(f'{username}:{password}'.encode()).decode()}"
    )

    # Make the GET request
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                endpoint, headers={"Authorization": auth_header}, timeout=10
            )

            if response.status_code == 200:
                # If the response is 200, the token is valid
                return  # Pass silently
            elif response.status_code == 404:
                # If the response is 404, the token is invalid
                detail = response.json().get("detail", "Token not found")
                raise TokenValidationError(detail)
            else:
                # Handle unexpected status codes
                raise TokenValidationError(
                    f"Unexpected response code: {response.status_code}"
                )
        except httpx.RequestError as e:
            raise TokenValidationError(f"Request failed: {e}")
        except Exception as e:
            raise TokenValidationError(f"An unexpected error occurred: {e}")


def validate_token(token: str = None) -> None:
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


# Example usage
if __name__ == "__main__":
    token = "test"
    try:
        validate_token(token)
        print("Token is valid.")
    except TokenValidationError as e:
        print(f"Token validation failed: {e}")
