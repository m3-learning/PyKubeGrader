from pykubegrader.utils import api_base_url

def check_api_connection():
    """
    Check the API connection by verifying the API base URL.

    This function checks if the environment variable for the API base URL is set.
    If the variable is not set, it raises an exception.

    Raises:
        Exception: If the environment variable for the API URL is not set.
    """
    if not api_base_url:
        raise Exception("Environment variable for API URL not set")