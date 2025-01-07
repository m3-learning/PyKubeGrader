import asyncio
import base64
import os

import httpx
import nest_asyncio  # type: ignore

# Apply nest_asyncio for environments like Jupyter
nest_asyncio.apply()


def get_credentials():
    """
    Fetch the username and password from environment variables.
    """
    username = os.getenv("user_name_student")
    password = os.getenv("keys_student")
    if not username or not password:
        raise ValueError(
            "Environment variables 'user_name_student' or 'keys_student' are not set."
        )
    return {"username": username, "password": password}


async def call_score_assignment(
    assignment_title: str, notebook_title: str, file_path: str = ".output_reduced.log"
) -> dict:
    """
    Submit an assignment to the scoring endpoint.

    Args:
        assignment_title (str): Title of the assignment.
        file_path (str): Path to the log file to upload.

    Returns:
        dict: JSON response from the server.
    """
    # Fetch the endpoint URL from environment variables
    base_url = os.getenv("DB_URL")
    if not base_url:
        raise ValueError("Environment variable 'DB_URL' is not set.")
    url = f"{base_url}score-assignment?assignment_title={assignment_title}&notebook_title={notebook_title}"

    # Get credentials
    credentials = get_credentials()
    username = credentials["username"]
    password = credentials["password"]

    # Encode credentials for Basic Authentication
    auth_header = (
        f"Basic {base64.b64encode(f'{username}:{password}'.encode()).decode()}"
    )

    # Send the POST request
    async with httpx.AsyncClient() as client:
        try:
            with open(file_path, "rb") as file:
                response = await client.post(
                    url,
                    headers={"Authorization": auth_header},  # Add Authorization header
                    files={"log_file": file},  # Upload log file
                )

                # Handle the response
                response.raise_for_status()  # Raise an exception for HTTP errors
                response_data = response.json()
                return response_data
        except FileNotFoundError:
            raise FileNotFoundError(f"The file {file_path} does not exist.")
        except httpx.RequestError as e:
            raise RuntimeError(f"An error occurred while requesting {url}: {e}")
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred: {e}")


def submit_assignment(
    assignment_title: str,
    notebook_title: str,
    file_path: str = ".output_reduced.log",
) -> None:
    """
    Synchronous wrapper for the `call_score_assignment` function.

    Args:
        assignment_title (str): Title of the assignment.
        file_path (str): Path to the log file to upload.
    """
    # Get the current event loop or create one
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Run the async function in the event loop
    response = loop.run_until_complete(
        call_score_assignment(assignment_title, notebook_title, file_path)
    )
    print("Server Response:", response.get("message", "No message in response"))


# Example usage (remove this section if only the function needs to be importable):
if __name__ == "__main__":
    submit_assignment("week1-readings", "path/to/your/log_file.txt")
