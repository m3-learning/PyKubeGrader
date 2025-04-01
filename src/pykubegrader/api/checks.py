from IPython.core.getipython import get_ipython
from pykubegrader._utils import api_base_url


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


def check_ipython():
    """
    Check if the current environment is a Jupyter environment.

    This function checks if the IPython environment is available. If it is not available,
    it raises an exception indicating that the setup was unsuccessful.

    Returns:
        InteractiveShell: The IPython InteractiveShell instance.

    Raises:
        Exception: If the IPython environment is not available.
    """
    ipython = get_ipython()
    if ipython is None:
        raise Exception("Setup unsuccessful. Are you in a Jupyter environment?")
    return ipython
