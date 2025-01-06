import requests

try:
    from pykubegrader.build.passwords import password, user, juptyerhub_user
except:  # noqa: E722
    print("Passwords not found, cannot access database")


def build_token_payload(token: str, duration: int) -> dict:

    if juptyerhub_user() is None:
        raise ValueError("JupyterHub user not found")

    # Return the extracted details as a dictionary
    return {
        "value": token,
        "requester": juptyerhub_user(),
        "duration": duration,
    }


# Need to do for add token as well
def add_token(self, token, duration=20):
    """
    Sends a POST request to add a notebook.
    """
    # Define the URL
    url = "https://engr-131-api.eastus.cloudapp.azure.com/tokens"

    # Build the payload
    payload = self.build_token_payload(token= token, duration=duration)

    # Define HTTP Basic Authentication
    auth = (user(), password())

    # Define headers
    headers = {"Content-Type": "application/json"}

    # Serialize the payload with the custom JSON encoder
    serialized_payload = json.dumps(payload, default=self.json_serial)

    # Send the POST request
    response = requests.post(url, data=serialized_payload, headers=headers, auth=auth)

    # Print the response
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {response.json()}")
    except ValueError:
        print(f"Response: {response.text}")
