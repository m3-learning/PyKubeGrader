import os
import httpx
import asyncio

import nest_asyncio

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
    assignment_title: str, file_path: str = ".output_reduced.log"
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
    url = f"{base_url}score-assignment"

    # Get credentials
    credentials = get_credentials()

    # Send the POST request
    async with httpx.AsyncClient() as client:
        try:
            with open(file_path, "rb") as file:
                response = await client.post(
                    url,
                    data={"cred": credentials, "assignment_title": assignment_title},
                    files={"log_file": file},
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


# Importable function
def submit_assignment(
    assignment_title: str, file_path: str = ".output_reduced.log"
) -> None:
    """
    Synchronous wrapper for the `call_score_assignment` function.

    Args:
        assignment_title (str): Title of the assignment.
        file_path (str): Path to the log file to upload.
    """
    response = asyncio.run(call_score_assignment(assignment_title, file_path))
    print("Server Response:", response.get("message", "No message in response"))


# Example usage (remove this section if only the function needs to be importable):
if __name__ == "__main__":
    submit_assignment("Week 1 Assignment", "path/to/your/log_file.txt")
