import requests
import os

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


def validate_token(token = None):
    """
    Validate a token by making a GET request to the validation endpoint.

    Args:
        token (str): The token to validate.

    Raises:
        TokenValidationError: If the token is invalid or if there is an error in the validation process.

    Returns:
        None: If the token is valid, the function will pass silently.
    """
    endpoint = f"https://engr-131-api.eastus.cloudapp.azure.com/validate-token/{token}"

    if token is not None:
        os.environ["TOKEN"] = token

    if token is None:
        token = os.getenv("TOKEN", None)
        
    if token is None:
        raise TokenValidationError("No token provided")

    try:
        response = requests.get(endpoint, timeout=10)

        if response.status_code == 200:
            # If the response is 200, the token is valid
            return  # Pass silently
        elif response.status_code == 404:
            # If the response is 404, the token is invalid
            raise TokenValidationError(response.json().get("detail", "Token not found"))
        else:
            # Handle unexpected status codes
            raise TokenValidationError(
                f"Unexpected response code: {response.status_code}"
            )
    except requests.RequestException as e:
        # Raise an exception for connection errors or timeout
        raise TokenValidationError(f"Request failed: {e}")


# Example usage
if __name__ == "__main__":
    token = "test"
    try:
        validate_token(token)
        print("Token is valid.")
    except TokenValidationError as e:
        print(f"Token validation failed: {e}")
