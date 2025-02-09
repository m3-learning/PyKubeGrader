import panel as pn
import requests
from requests.auth import HTTPBasicAuth

from ..utils import api_base_url

# Dummy credentials for HTTP Basic Auth
AUTH = HTTPBasicAuth("user", "password")

# Panel configuration
pn.extension()


def fetch_students():
    """
    Fetches the list of students from the API.
    """
    url = api_base_url.rstrip("/") + "/students"
    try:
        response = requests.get(url, auth=AUTH)
        response.raise_for_status()
        students = response.json()
        return {
            str(student["id"]): f"{student['name']} (ID: {student['id']})"
            for student in students
        }
    except requests.exceptions.RequestException as e:
        print(f"Error fetching students: {e}")
        return {}


# Load students dynamically
student_options = fetch_students()

# Input Widgets
token_input = pn.widgets.TextInput(name="Token", placeholder="Enter token string")
duration_input = pn.widgets.IntInput(name="Duration (minutes)", value=20, step=5)
assignment_input = pn.widgets.TextInput(
    name="Assignment Name", placeholder="Enter assignment name"
)
student_select = pn.widgets.Select(
    name="Select Student (Optional)", options={"None": "None", **student_options}
)

status_output = pn.pane.Markdown("", width=600)


def add_token():
    """
    Sends a POST request to mint a token.
    """
    url = api_base_url.rstrip("/") + "/tokens"

    payload = {
        "requester": "ta_user",  # Modify as needed
        "value": token_input.value,
        "assignment_name": assignment_input.value,
        "duration": duration_input.value,
        "student_id": (
            int(student_select.value) if student_select.value != "None" else None
        ),
    }

    headers = {"x-jhub-user": payload["requester"]}

    try:
        response = requests.post(url, json=payload, headers=headers, auth=AUTH)
        response.raise_for_status()
        result = response.json()
        status_output.object = f"✅ **Success!** Token Created: `{result}`"
    except requests.exceptions.RequestException as e:
        status_output.object = f"❌ **Error:** {e}"


submit_button = pn.widgets.Button(name="Submit Token", button_type="primary")
submit_button.on_click(add_token)

# Panel Layout
app = pn.Column(
    "# 🎟 Token Generator",
    token_input,
    duration_input,
    assignment_input,
    student_select,
    submit_button,
    status_output,
)

# Serve the app
app.servable()
