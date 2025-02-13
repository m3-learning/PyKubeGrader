import sys

import panel as pn
import requests
from panel.pane import Markdown
from panel.widgets import Button, Select, TextInput
from requests.auth import HTTPBasicAuth

from ..utils import api_base_url, student_pw, student_user

pn.extension()


class TokenGenerator:
    def __init__(self) -> None:
        if not student_user or not student_pw:
            raise RuntimeError("API credentials not found in environment variables")

        self.username = student_user
        self.password = student_pw

        self.students: list[str] = self.fetch_options("students", key="email")
        self.assignments: list[str] = self.fetch_options("assignments", key="title")

        # Empty lists are falsy
        if not self.students or not self.assignments:
            raise RuntimeError("No students found, or no assignments")

        self.stud_select = Select(name="Student email", options=self.students)
        self.assn_select = Select(name="Assignment name", options=self.assignments)
        self.token_input = TextInput(name="Desired token value")
        self.submit_btn = Button(name="Submit", button_type="primary")
        self.status_msg = Markdown("")

        self.submit_btn.on_click(self.request_token)

    def fetch_options(self, endpoint: str, key: str) -> list[str]:
        try:
            response = requests.get(
                url=f"{api_base_url}/{endpoint}",
                auth=HTTPBasicAuth(self.username, self.password),
            )
            response.raise_for_status()
            return sorted([item[key] for item in response.json()])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {endpoint}: {e}", file=sys.stderr)
            return []

    def request_token(self, _) -> None:
        payload = {
            "student_id": self.stud_select.value,
            "assignment": self.assn_select.value,
            "value": self.token_input.value,
        }

        try:
            response = requests.post(
                url=f"{api_base_url}/tokens",
                auth=HTTPBasicAuth(self.username, self.password),
                json=payload,
            )
            response.raise_for_status()
            self.status_msg.object = "✅ Token generated successfully!"
        except requests.exceptions.RequestException as e:
            self.status_msg.object = f"❌ Submission failed: {e}"

    def show(self) -> pn.Column:
        return pn.Column(
            "# Generate Scoped Token",
            self.stud_select,
            self.assn_select,
            self.token_input,
            self.submit_btn,
            self.status_msg,
        )
